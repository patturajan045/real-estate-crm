# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key_estateflow_crm_super_secure_key_2026")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "super_secret_jwt_key_estateflow_crm_2026_secure_32bytes!")

    # Local MongoDB connection string
    MONGO_URI = os.environ.get(
        "MONGO_URI",
        "mongodb://localhost:27017/real_estate_crm"
    )