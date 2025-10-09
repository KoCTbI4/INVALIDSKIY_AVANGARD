import asyncio
import websockets
import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
import hashlib
import hmac
import sqlite3

# Класс для сохранения логов в JSON
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
            "name": record.name
        }
        return json.dumps(log_entry, ensure_ascii=False)

# Настройка логирования
def setup_logging():
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    json_formatter = JSONFormatter()
    json_handler = RotatingFileHandler("chat_logs.json", maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
    json_handler.setFormatter(json_formatter)

    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    logging.basicConfig(level=logging.INFO, handlers=[json_handler, console_handler])

# Проверка initData
def check_telegram_auth(init_data: str, bot_token: str):
    try:
        params = dict(x.split("=", 1) for x in init_data.split("&"))
        received_hash = params.pop('hash', '')
        
        data_check_arr = [f"{k}={v}" for k, v in sorted(params.items())]
        data_check_string = "\n".join(data_check_arr)
        
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        calculated_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()
        
        if calculated_hash != received_hash:
            return None
        
        return params
    except Exception:
        return None

# Получение данных пользователя из БД
def get_user_data(telegram_id: int):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT first_name, last_name, username, photo_url, phone_number FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )
    user = cursor.fetchone()
    
    conn.close()
    
    if user:
        return {
            "first_name": user[0],
            "last_name": user[1],
            "username": user[2],
            "photo_url": user[3],
            "phone_number": user[4]
        }
    return None

# Хранение подключённых клиентов
clients = {}  # websocket: user_data

async def handle_message(websocket):
    user_data = {
        "telegram_id": None,
        "name": "Аноним",
        "avatar": None
    }
    
    try:
        # Ждём initData от клиента
        init_message = await websocket.recv()
        init_data = json.loads(init_message).get("initData")

        if not init_data:
            logging.warning("Клиент не отправил initData")
            await websocket.close()
            return

        # ЗАМЕНИ НА ТОКЕН СВОЕГО БОТА
        bot_token = "8359337265:AAEOkV9Dox9nnbfPsBFxVH9DcQopa0wAuiM"
        telegram_user_data = check_telegram_auth(init_data, bot_token)

        if not telegram_user_data:
            logging.warning("Неверный initData")
            await websocket.close()
            return

        telegram_id = int(json.loads(telegram_user_data["user"])["id"])
        
        # Получаем данные из БД
        db_user = get_user_data(telegram_id)
        if db_user:
            name = f"{db_user['first_name']} {db_user['last_name']}".strip()
            user_data = {
                "telegram_id": telegram_id,
                "name": name if name else db_user["username"] or "Аноним",
                "avatar": db_user["photo_url"]
            }
        else:
            # Если нет в БД — используем данные из Telegram
            tg_user = json.loads(telegram_user_data["user"])
            name = f"{tg_user.get('first_name', '')} {tg_user.get('last_name', '')}".strip()
            user_data = {
                "telegram_id": telegram_id,
                "name": name if name else tg_user.get("username", "Аноним"),
                "avatar": tg_user.get("photo_url")
            }

        clients[websocket] = user_data
        logging.info(f"Пользователь '{user_data['name']}' (ID: {telegram_id}) подключился. Всего пользователей: {len(clients)}")

    except Exception as e:
        logging.error(f"Ошибка при подключении: {e}")
        await websocket.close()
        return

    try:
        async for message in websocket:
            data = json.loads(message)
            full_message = {
                "name": user_data["name"],
                "text": data["text"],
                "sender": data.get("sender", "user"),
                "telegram_id": user_data["telegram_id"],
                "timestamp": datetime.now().isoformat()
            }
            logging.info(f"[{user_data['name']}] -> {data['text']}")

            # Рассылаем сообщение всем подключённым
            for client_ws in clients.copy():
                try:
                    await client_ws.send(json.dumps(full_message))
                except:
                    logging.warning(f"Ошибка отправки пользователю '{clients.get(client_ws, {}).get('name', 'Unknown')}'")
                    clients.pop(client_ws, None)
    except websockets.exceptions.ConnectionClosed:
        logging.info(f"Пользователь '{user_data['name']}' (ID: {user_data['telegram_id']}) отключился. Всего пользователей: {len(clients)}")
    finally:
        clients.pop(websocket, None)

async def main():
    setup_logging()
    logging.info("=== Чат-сервер для Telegram WebApp запущен ===")
    logging.info("Сервер запущен на ws://localhost:8765")
    
    start_server = websockets.serve(handle_message, "localhost", 8765)
    await start_server
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())