import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_DB_URI")
DB_NAME = os.getenv("MONDO_DB_NAME")

client = AsyncIOMotorClient(MONGO_URI)
database = client[DB_NAME]  # Select the database

print("mongo connection done")
users_collection = database["users"]  # Select the users collection
analysis_data_collection = database["analysis_data"]