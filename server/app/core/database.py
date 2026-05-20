from pymongo import MongoClient
from app.core.config import settings

client = MongoClient(settings.MONGO_URI)
db = client[settings.DATABASE]

users_collection = db["users"]
blacklist_collection = db["token_blacklist"]

try:
    blacklist_collection.create_index("expires_at", expireAfterSeconds=0)
except Exception:
    pass