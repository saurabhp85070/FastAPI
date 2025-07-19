from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file

MONGO_URL = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URL)

db = client["ecommerce_db"]  # You can rename this to any database name you want

product_collection = db.products
order_collection = db.orders
