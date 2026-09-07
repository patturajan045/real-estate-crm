# db.py
from pymongo import MongoClient
from app.config import Config

client = MongoClient(Config.MONGO_URI)
db = client.get_default_database()  # Automatically selects 'real_estate_crm' from the URI

# Real Estate CRM Collections
user_collection = db["users"]
lead_collection = db["leads"]
project_collection = db["projects"]
building_collection = db["buildings"]
unit_collection = db["units"]
booking_collection = db["bookings"]