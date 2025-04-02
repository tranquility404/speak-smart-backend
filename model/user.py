from pydantic import BaseModel, EmailStr
from typing import List, Optional

class User(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    roles: List[str]  # Roles can be a list of strings like ['admin', 'user']
    profile_pic_url: Optional[str] = None  # Optional field for profile picture URL
    country: Optional[str] = None  # Optional field for country

    class Config:
        from_attributes = True  # Enable compatibility with ORM models (useful for MongoDB)