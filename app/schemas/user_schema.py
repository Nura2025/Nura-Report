# schemas/user_schema.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class UserUpdateByEmail(BaseModel):
    email: EmailStr
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    gender: Optional[str]
    date_of_birth: Optional[date]
    phone_number: Optional[str]
