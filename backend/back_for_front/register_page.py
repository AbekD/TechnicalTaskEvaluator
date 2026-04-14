import os

from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,EmailStr
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
class enter(BaseModel):
    email_or_username:str
    password: str
class register_page(BaseModel):
    username: str
    email: EmailStr
    password: 
SUPABASE_URL = "https://lbljfyxgzrhotjhkmuef.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
@app.post('/api/register')
async def data(user:register_page):
    existing_user = supabase.table("users").select("username, email").or_(f"username.eq.{user.username},email.eq.{user.email}").execute()
    if existing_user.data:
        found = existing_user.data[0]
        if found['email'] == user.email:
            raise HTTPException(status_code=400, detail="Пользователь с такой почтой уже зарегистрирован")
        if found['username'] == user.username:
            raise HTTPException(status_code=400, detail="Это имя пользователя уже используется")
    print(f"Данные получены: {user}")
    try:
        data = {
            "username": user.username,
            "email": user.email,
            "password": user.password
        }

        response = supabase.table("users").insert(data).execute()
        if len(response.data) > 0:
            return {"message": "Успешно сохранено в базу!", "user": response.data[0]}
        raise HTTPException(status_code=400, detail="Не удалось записать данные")
    except Exception as e:
        print(f"Ошибка на backend части:{e}")
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post('/api/enter')
async def check_login(user: enter):
    try:
        field_to_query = "email" if "@" in user.email_or_username else "username"

        response = supabase.table("users").select("*").eq(field_to_query, user.email_or_username).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        db_user = response.data[0] 
        if str(db_user['password']) == str(user.password):
            return {
                "status": "success", 
                "message": "Доступ разрешен",
                "redirect_url": "chat_ai.html", 
                "user": db_user['username']
            }
        else:
            raise HTTPException(status_code=401, detail="Неверный пароль")

    except Exception as e:
        error_msg = str(e)
        print(f"Ошибка входа: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
@app.get('/db_check')
async def check_db():
    try:
        response = supabase.table("users").select("count", count="exact").execute()
        return {"status": "connected", "total_users": response.count}
    except Exception as e:
        return {"status": "error", "detail": str(e)}