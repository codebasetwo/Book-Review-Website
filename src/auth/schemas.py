
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List
import uuid

from src.books.schemas import Books
from src.reviews.schemas import ReviewModel



class UserCreateModel(BaseModel):
    username: str = Field(max_length=8)
    email: str = Field(max_length=40)
    first_name: str = Field(max_length=25)
    last_name: str = Field(max_length=25)
    password: str = Field(min_length=6)


class UserModel(BaseModel):
    uid: uuid.UUID
    username: str
    email: str
    first_name: str
    last_name: str
    is_verified: bool = Field(default=False)
    password_hash: str = Field(exclude=True)
    created_at: datetime
    updated_at: datetime

    def __repr__(self):
        return f"<User {self.username}>"


class UserBooksModel(UserModel):
    books: List[Books]
    reviews: List[ReviewModel]


class UserLoginModel(BaseModel):
    email: str = Field(max_length=40)
    password: str = Field(min_length=6)


class EmailModel(BaseModel):
    addresses : List[str]


class PasswordResetRequestModel(BaseModel):
    email: str


class PasswordResetConfirmModel(BaseModel):
    new_password: str
    confirm_new_password: str