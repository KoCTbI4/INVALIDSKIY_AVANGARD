from fastapi import FastAPI, File, UploadFile, Form
import requests
import base64
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
from deep_translator import GoogleTranslator
import uuid

#                   ИДЕАЛ.              СПАЙКА ДВУХ МОДЕЛЕЙ, MOONDREAM - ПОДРОБНОЕ ОПИСАНИЕ ФОТОГРАФИИ, DEEPSEEK - LLM МОДЕЛЬ ДЛЯ ОБЩЕНИЯ В КОНТЕКСТЕ ИЗОБРАЖЕНИЯ

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MOONDREAM_API_KEY ключ
MOONDREAM_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlfaWQiOiJmODM3NGRiZS1lMWVkLTRhNDAtOTU1Mi0yMmExODdhOGU1ZDAiLCJvcmdfaWQiOiI1S2ZkU1FqaWZaelRVeFp3NTZrdHV1eEJYa3V6ZjVXZSIsImlhdCI6MTc2MDUzMDM3NywidmVyIjoxfQ.lxreTJtXbyRyY9hBBkknuyeZPSoU_L-dl3a6D4oxKtI"

def get_image_mime_type(image_format: str):
    """Возвращает MIME-тип для формата изображения."""
    mime_map = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "GIF": "image/gif",
        "BMP": "image/bmp",
        "WEBP": "image/webp",
        "JPG": "image/jpg",
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
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "deepseek-r1:8b",
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data.get("response", "").strip()
    else:
        raise Exception(f"Model error: {response.text}")

# Хранилище истории по сессиям
sessions = {}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7508)