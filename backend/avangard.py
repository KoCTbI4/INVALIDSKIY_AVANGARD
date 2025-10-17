# unified_server.py

from fastapi import FastAPI, File, UploadFile, Form
import requests
import base64
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
from deep_translator import GoogleTranslator
import uuid
import torch # Если нужен
from transformers import BlipProcessor, BlipForConditionalGeneration # Если нужен BLIP локально
import asyncio
import websockets
import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
import threading

# --- Конфигурация ---
MOONDREAM_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlfaWQiOiJmODM3NGRiZS1lMWVkLTRhNDAtOTU1Mi0yMmExODdhOGU1ZDAiLCJvcmdfaWQiOiI1S2ZkU1FqaWZaelRVeFp3NTZrdHV1eEJYa3V6ZjVXZSIsImlhdCI6MTc2MDUzMDM3NywidmVyIjoxfQ.lxreTJtXbyRyY9hBBkknuyeZPSoU_L-dl3a6D4oxKtI"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL_NAME = "deepseek-r1:8b"
BLIP_MODEL_NAME = "Salesforce/blip-image-captioning-base"

# --- Глобальное хранилище сессий (для временного использования) ---
sessions = {}

# --- Глобальные переменные для BLIP модели (если используется локально) ---
blip_processor = None
blip_model = None

# --- Глобальные переменные для WebSocket ---
ws_clients = {}
ws_logger = None

# --- Инициализация FastAPI ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Важно для доступа извне, но осторожно в продакшене
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Функции из camera-chat.py ---
def get_image_mime_type(image_format: str):
    """Возвращает MIME-тип для формата изображения."""
    mime_map = {
        "JPEG": "image/jpeg", "PNG": "image/png", "GIF": "image/gif",
        "BMP": "image/bmp", "WEBP": "image/webp", "JPG": "image/jpg",
    }
    return mime_map.get(image_format.upper(), "image/jpg")

def get_moondream_response(image_data: str, mime_type: str, prompt: str):
    headers = {
        "X-Moondream-Auth": MOONDREAM_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "image_url": f"data:{mime_type};base64,{image_data}",
        "prompt": prompt
    }
    response = requests.post("https://api.moondream.ai/v1/caption", headers=headers, json=payload)
    print("Moondream response:", response.text)
    if response.status_code == 200:
        data = response.json()
        if "caption" in data:
            answer = data["caption"]
            # Перевод текста на русский
            try:
                answer_ru = GoogleTranslator(source='auto', target='ru').translate(answer)
            except Exception:
                answer_ru = answer
            return answer_ru
        else:
            return str(data)
    else:
        raise Exception(f"Moondream error: {response.text}")

def encode_image_to_base64_and_get_mime(image_file):
    """Кодирует изображение в base64 и возвращает MIME-тип."""
    img = Image.open(image_file)
    mime_type = get_image_mime_type(img.format)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    img_bytes = buffer.getvalue()
    image_data = base64.b64encode(img_bytes).decode('utf-8')
    return image_data, mime_type

def get_llama_response(prompt: str):
    url = OLLAMA_URL
    payload = {
        "model": OLLAMA_MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data.get("response", "").strip()
    else:
        raise Exception(f"Model error: {response.text}")

# --- Функции из camera-test.py (BLIP) ---
def load_blip_model():
    global blip_processor, blip_model
    if blip_processor is None or blip_model is None:
        print("Loading BLIP model...")
        blip_processor = BlipProcessor.from_pretrained(BLIP_MODEL_NAME)
        blip_model = BlipForConditionalGeneration.from_pretrained(BLIP_MODEL_NAME)
        # Важно: на CPU это будет работать медленно
        device = "cpu" # Используем CPU, так как GPU, скорее всего, нет
        blip_model = blip_model.to(device)
        blip_model.eval()
        print("BLIP model loaded.")

def get_blip_description(image_bytes):
    """Генерирует описание изображения с помощью BLIP."""
    global blip_processor, blip_model
    load_blip_model() # Убедимся, что модель загружена

    try:
        device = "cpu"
        # Открываем изображение
        raw_image = Image.open(io.BytesIO(image_bytes)).convert('RGB')

        # Подготавливаем изображение для модели
        inputs = blip_processor(raw_image, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()} # Переносим на CPU

        # Генерируем описание
        with torch.no_grad(): # Отключаем вычисление градиентов для ускорения
            out = blip_model.generate(**inputs, max_new_tokens=50) # Ограничиваем длину описания

        # Декодируем результат
        description_en = blip_processor.decode(out[0], skip_special_tokens=True)

        print("BLIP description (EN):", description_en)

        # Переводим на русский
        try:
            description_ru = GoogleTranslator(source='en', target='ru').translate(description_en)
        except Exception:
            description_ru = description_en

        return description_ru
    except Exception as e:
        raise Exception(f"BLIP error: {str(e)}")

# --- Эндпоинты из camera-chat.py ---
@app.post("/api/start_chat")
async def start_chat(image: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    image.file.seek(0)
    image_data, mime_type = encode_image_to_base64_and_get_mime(image.file)
    description = get_moondream_response(image_data, mime_type, "Опиши, что изображено на этом фото.")
    # Сохраняем описание и историю в сессии
    sessions[session_id] = {
        "image_description": description,
        "chat_history": [
            {"role": "user", "content": "Опиши, что изображено на этом фото."},
            {"role": "assistant", "content": description}
        ]
    }
    return {"session_id": session_id, "description": description}

@app.post("/api/ask")
async def ask_question(session_id: str = Form(...), question: str = Form(...)):
    if session_id not in sessions:
        return {"error": "Session not found"}

    session = sessions[session_id]
    history = session["chat_history"]
    image_description = session["image_description"]

    # Добавляем вопрос пользователя в историю
    history.append({"role": "user", "content": question})

    context_lines = []
    for msg in history:
        role = "Пользователь" if msg["role"] == "user" else "Бот"
        context_lines.append(f"{role}: {msg['content']}")
    
    context = "\n".join(context_lines)

    # Промпт для Модели
    prompt = f"""Ты — помощник, который отвечает на вопросы о фотографии. Ты должен помочь пользователю понять что изображено на фотографии . 
Тебе уже дано описание изображения:

{image_description}

История диалога:
{context}

Задача: 
- Отвечать на любые вопросы пользователя в рамках изображения и связанных с ним деталей.
- Ответь на последний вопрос кратко, по существу, не повторяя описание изображения заново. 
- Не повторяй теги вроде (center), (background) или другие странные скобки.
- Отвечай **только на русском языке**.
- Не используй английские или азиатские слова, символы или фразы.
- Не начинай с фразы "На изображении..." — просто ответь на вопрос."""

    try:
        answer = get_llama_response(prompt)
    except Exception as e:
        answer = f"Ошибка при генерации ответа: {str(e)}"

    # Добавляем ответ модели в историю
    history.append({"role": "assistant", "content": answer})

    return {"answer": answer}

# --- Новый эндпоинт из camera-test.py ---
@app.post("/api/describe_blip")
async def describe_image_blip(file: UploadFile = File(...)):
    print("BLIP: Получен файл:", file.filename)
    print("BLIP: Тип файла:", file.content_type)

    img_bytes = await file.read()

    try:
        description = get_blip_description(img_bytes)
    except Exception as e:
        return {"error": str(e)}

    print("BLIP: Описание на русском:", description)

    return {"description": description}

# --- Логика из main.py (WebSocket) ---
# Настройка логирования
def setup_ws_logging():
    global ws_logger
    if ws_logger is None:
        ws_logger = logging.getLogger("WebSocket")
        ws_logger.setLevel(logging.INFO)
        handler = RotatingFileHandler("chat_logs.json", maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        ws_logger.addHandler(handler)

async def ws_handle_message(websocket):
    user_data = {"username": "Аноним"}

    try:
        # Ждём имя пользователя от клиента
        init_message = await websocket.recv()
        init_data = json.loads(init_message).get("username")

        if not init_data:
            logging.warning("Клиент не отправил username")
            await websocket.close()
            return

        user_data["username"] = init_data
        ws_clients[websocket] = user_data
        logging.info(f"Пользователь '{user_data['username']}' подключился. Всего пользователей: {len(ws_clients)}")

        # Обработка сообщений
        async for message in websocket:
            try:
                data = json.loads(message)

                # Обработка пинга
                if data.get("type") == "ping":
                    await websocket.send(json.dumps({"type": "pong"}))
                    continue

                # Обработка обычных сообщений
                full_message = {
                    "name": user_data["username"],
                    "text": data["text"],
                    "sender": data.get("sender", "user"),
                    "timestamp": datetime.now().isoformat()
                }
                logging.info(f"[{user_data['username']}] -> {data['text']}")

                # Рассылаем сообщение всем подключённым
                for client_ws in list(ws_clients.keys()):
                    try:
                        await client_ws.send(json.dumps(full_message))
                    except websockets.exceptions.ConnectionClosed:
                        logging.warning(f"Соединение с клиентом '{ws_clients[client_ws]['username']}' разорвано.")
                        ws_clients.pop(client_ws, None)

            except json.JSONDecodeError:
                logging.error("Некорректный формат входящего сообщения.")

    except websockets.exceptions.ConnectionClosed:
        logging.info(f"Пользователь '{user_data['username']}' отключился. Всего пользователей: {len(ws_clients)}")
    finally:
        ws_clients.pop(websocket, None)

async def ws_main():
    setup_ws_logging()
    logging.info("=== WebSocket-сервер запущен ===")
    logging.info("WebSocket-сервер запущен на ws://localhost:7509") # Изменён порт
    
    # Запускаем WebSocket сервер на отдельном порту
    start_server = websockets.serve(ws_handle_message, "localhost", 7509) # Изменён порт
    await start_server

def run_ws_server():
    """Функция для запуска WebSocket сервера в отдельном потоке."""
    asyncio.run(ws_main())

# --- Запуск приложения ---
if __name__ == "__main__":
    import uvicorn
    import threading

    # Запускаем WebSocket сервер в отдельном потоке
    ws_thread = threading.Thread(target=run_ws_server)
    ws_thread.daemon = True # Поток завершится, когда основной процесс завершится
    ws_thread.start()

    # Запускаем FastAPI сервер на порту 7508
    uvicorn.run(app, host="0.0.0.0", port=7508)
