# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Safely fall back to a local dev string or None if the env var is missing
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-do-not-use-in-prod")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-do-not-use-in-prod")
    
    # Do not hardcode the Atlas password here
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/local_db")