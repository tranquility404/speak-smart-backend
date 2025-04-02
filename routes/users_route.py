from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from config.database import users_collection
from security.auth import verify_password, create_access_token, get_current_user
from services.user_service import hash_password
from model.user import User

router = APIRouter()

# ------------------------- User Registration -------------------------
class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

@router.post("/register/")
async def register_user(user: RegisterRequest):
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "password": hash_password(user.password),
        "roles": ["USER"],  # Assign "user" role by default
    }

    new_user_id = await users_collection.insert_one(new_user)
    return {"message": "User registered successfully", "user_id": str(new_user_id.inserted_id)}

# ------------------------- User Login -------------------------
@router.post("/login/")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await users_collection.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(str(user["_id"]), user["roles"])
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me/")
async def get_my_info(current_user: User = Depends(get_current_user)):
    return {
        "first_name": current_user["first_name"],
        "last_name": current_user["last_name"],
        "email": current_user["email"],
        "country": current_user.get("country", ""),  # If country doesn't exist, return empty string
        "profile_pic_url": current_user.get("profile_pic_url", ""),  # If profile_pic_url doesn't exist, return empty string
    }


# ------------------------- Reset Password -------------------------
class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str

# @router.post("/reset-password/")
# async def reset_password(data: ResetPasswordRequest):
#     user = await collection.find_one({"email": data.email})
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#
#     hashed_password = hash_password(data.new_password)
#     await collection.update_one({"email": data.email}, {"$set": {"password": hashed_password}})
#
#     return {"message": "Password reset successful"}