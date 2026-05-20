from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
import bcrypt
import jwt
import datetime
from bson.objectid import ObjectId
from app.core.config import settings
from app.core.database import users_collection, blacklist_collection

router = APIRouter(prefix="/api", tags=["Auth & User"])

class AuthSchema(BaseModel):
    username: str
    password: str

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def generate_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Отсутсвует или неверен токен")
    
    token = authorization.split(" ")[1]
    if blacklist_collection.find_one({"token": token}):
        raise HTTPException(status_code=401, detail="Токен отозван (вышли из системы)")
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload.get("user_id"), token
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(status_code=401, detail="Токен недействителен")
    
@router.post("/register")
def register(data: AuthSchema):
    if users_collection.find_one({"username": data.username}):
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    
    user = {
        "username": data.username,
        "password": hash_password(data.password),
        "status": 0,
        "balance": 500,
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }
    result = users_collection.insert_one(user)
    token = generate_token(str(result.inserted_id))
    return {"token": token, "username": data.username}

@router.post("/login")
def login(data: AuthSchema):
    user = users_collection.find_one({"username": data.username})
    if user and check_password(data.password, user["password"]):
        token = generate_token(str(user["_id"]))
        return {"token": token, "username": user["username"]}
    raise HTTPException(status_code=401, detail="Неверный логин или пароль")

@router.post("/logout")
def logout(user_data: tuple = Depends(get_current_user)):
    _, token = user_data
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            blacklist_collection.insert_one({
                "token": token,
                "expires_at": datetime.datetime.fromtimestamp(exp_timestamp, tz=datetime.timezone.utc)
            })
    except Exception:
        pass
    return {"status": "success"}

@router.get("/user/profile")
def get_profile(user_data: tuple = Depends(get_current_user)):
    user_id, _ = user_data
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {
        "username": user.get("username", "Гость"),
        "status": user.get("status", 0),
        "balance": user.get("balance", 0)
    }