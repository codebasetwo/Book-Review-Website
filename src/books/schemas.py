from typing import List
from pydantic import BaseModel
import uuid
from datetime import datetime, date

from src.reviews.schemas import ReviewModel

class Books(BaseModel):
    uid: uuid.UUID
    title: str
    author: str
    publisher: str
    published_date: date
    page_count: int
    language: str
    created_at: datetime
    updated_at: datetime

class BookCreateModel(BaseModel):
    title: str
    author: str
    publisher: str
    published_date: str
    page_count: int
    language: str


class BookDetailModel(Books):
    reviews: List[ReviewModel]


class BookUpdateModel(BaseModel):
    title: str
    publisher: str
    page_count: int
    language: str