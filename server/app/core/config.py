import os

class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "vpl_drop_secret_key_2024")
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb+srv://admin:123456qwerty@cluster0.mvdyb6h.mongodb.net/?appName=Cluster0")
    DATABASE: str = "vpldrop"
    
settings = Settings()