from bson import ObjectId
from fastapi import HTTPException

from config.database import users_collection
from model.user import User
from passlib.context import CryptContext  # For password hashing

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def create_user(user: User):
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    user.roles = ["user"]  # Default role is "user"
    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)    # Hash password before storing

    result = await users_collection.insert_one(user_dict)
    return {"message": "User registered successfully", "id": str(result.inserted_id)}

async def get_user_by_email(email: str):
    user = await users_collection.find_one({"email": email})
    if user:
        return {"id": str(user["_id"]), "first_name": user["first_name"], "last_name": user["last_name"],
                "email": user["email"], "roles": user["roles"], "profile_pic_url": user.get("profile_pic_url", ""), "country": user.get("country", "")}
    return None

async def get_users():
    users = await users_collection.find().to_list(100)
    return [{"id": str(user["_id"]), "first_name": user["first_name"], "last_name": user["last_name"],
             "email": user["email"], "roles": user["roles"], "profile_pic_url": user.get("profile_pic_url", ""), "country": user.get("country", "")} for user in users]

async def get_user(user_id: str):
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        return {"id": str(user["_id"]), "first_name": user["first_name"], "last_name": user["last_name"],
                "email": user["email"], "roles": user["roles"], "profile_pic_url": user.get("profile_pic_url", ""), "country": user.get("country", "")}
    return None
