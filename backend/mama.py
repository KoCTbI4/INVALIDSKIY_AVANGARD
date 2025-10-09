from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import hashlib
import hmac
import json
from datetime import datetime

app = FastAPI()

# Подключаем папку с HTML-файлами
app.mount("/", StaticFiles(directory="structory", html=True), name="structory")


# Подключение к БД
def get_db():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

# Создание таблицы
def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            phone_number TEXT,
            photo_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

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

@app.post("/api/account")
async def save_account(request: Request):
    data = await request.json()
    init_data = data.get("initData")
    phone_number = data.get("phone_number", "")

    if not init_data:
        return JSONResponse({"error": "No initData provided"}, status_code=400)

    # ЗАМЕНИ НА ТОКЕН СВОЕГО БОТА
    bot_token = "8359337265:AAEOkV9Dox9nnbfPsBFxVH9DcQopa0wAuiM" 
    user_data = check_telegram_auth(init_data, bot_token)
    
    if not user_data:
        return JSONResponse({"error": "Invalid initData"}, status_code=400)

    user_info = json.loads(user_data["user"])
    telegram_id = int(user_info["id"])
    first_name = user_info.get("first_name", "")
    last_name = user_info.get("last_name", "")
    username = user_info.get("username", "")
    photo_url = user_info.get("photo_url", "")

    # Сохраняем/обновляем в БД
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO users (
            telegram_id, first_name, last_name, username, phone_number, photo_url, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        telegram_id, first_name, last_name, username, phone_number, photo_url, datetime.now()
    ))
    
    conn.commit()
    conn.close()

    return {"message": "Account updated successfully"}

@app.get("/api/account")
async def get_account(request: Request):
    init_data = request.query_params.get("initData")
    if not init_data:
        return JSONResponse({"error": "No initData provided"}, status_code=400)

    bot_token = "8359337265:AAEOkV9Dox9nnbfPsBFxVH9DcQopa0wAuiM"
    user_data = check_telegram_auth(init_data, bot_token)
    if not user_data:
        return JSONResponse({"error": "Invalid initData"}, status_code=400)

    user_info = json.loads(user_data["user"])
    telegram_id = int(user_info["id"])

    # Получаем данные из БД
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    ).fetchone()
    conn.close()

    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)

    return {
        "telegram_id": user["telegram_id"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "username": user["username"],
        "phone_number": user["phone_number"],
        "photo_url": user["photo_url"]
    }

if __name__ == "__main__":
    init_db()
    import uvicorn
    uvicorn.run(app, host="localhost", port=8056)