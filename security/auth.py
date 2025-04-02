import jwt
import datetime
from bson import ObjectId
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from config.database import users_collection

# JWT Secret Key
SECRET_KEY = "dff4073c53b943a1d7038f6d0abe3cf71e7abe85830218122b371faf88523aa840ddf74d69bfa5648c6e0dbe048a0f12161e17978ad2a8b26bc9ef44180ae31cb873aad084e79e8c08bc3282f4efa2313d1397ca075719526af93d0994cf41a015f534d9ad753d5fbbd578ec2e04a8f1ba3cfb58dd61343cca35151ea88733398ce20a7cff79ed662205bbc5fa91f8bd4d0f8c67c7133553f7da82ae18c57182786e901c6b34564bb0bc215466745627ef61a9d447f1c3c3c1b8ac429a2d31c09c8ea0e810adbe867fea6f7b49c087d5cb30dc7d0c40c5f8a91bd40a6aee15c78a7349cbbd5e870c7999fcd3aff545354efa91f6ce17ab7230b1a4531276f4a4"
ALGORITHM = "HS256"

# OAuth2 scheme for login authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: str, roles: list):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(days=30)
    payload = {
        "sub": user_id,
        "roles": roles,
        "exp": expiration
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def authenticate_user(email: str, password: str):
    user = await users_collection.find_one({"email": email})
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(str(user["_id"]), user["roles"])
    return {"access_token": token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user_websocket(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_role(required_roles: list, user: dict = Depends(get_current_user)):
    if not any(role in user.get("roles", []) for role in required_roles):
        raise HTTPException(status_code=403, detail="Access forbidden: insufficient permissions")
    return user