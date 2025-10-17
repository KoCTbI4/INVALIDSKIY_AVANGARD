import asyncio
import websockets
import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Настройка логирования
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            RotatingFileHandler("chat_logs.json", maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

# Хранение подключённых клиентов
clients = {}

async def handle_message(websocket):
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
        clients[websocket] = user_data
        logging.info(f"Пользователь '{user_data['username']}' подключился. Всего пользователей: {len(clients)}")

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
                for client_ws in list(clients.keys()):
                    try:
                        await client_ws.send(json.dumps(full_message))
                    except websockets.exceptions.ConnectionClosed:
                        logging.warning(f"Соединение с клиентом '{clients[client_ws]['username']}' разорвано.")
                        clients.pop(client_ws, None)

            except json.JSONDecodeError:
                logging.error("Некорректный формат входящего сообщения.")

    except websockets.exceptions.ConnectionClosed:
        logging.info(f"Пользователь '{user_data['username']}' отключился. Всего пользователей: {len(clients)}")
    finally:
        clients.pop(websocket, None)

async def main():
    setup_logging()
    logging.info("=== Чат-сервер запущен ===")
    logging.info("Сервер запущен на ws://localhost:8765")
    
    start_server = websockets.serve(handle_message, "localhost", 7509)
    await start_server
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())