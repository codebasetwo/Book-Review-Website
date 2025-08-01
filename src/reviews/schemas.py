import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ReviewCreateModel(BaseModel):
    rating: int = Field(lt=5)
    review_text: str



class ReviewModel(BaseModel):
    uid: uuid.UUID
    rating: int = Field(lt=5)
    review_text: str
    user_uid: Optional[uuid.UUID]
    book_uid: Optional[uuid.UUID]
    created_at: datetime
    update_at: datetime