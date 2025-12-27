from pydantic import BaseModel
from typing import Optional

class CommentLikeCreate(BaseModel):
    user_identifier: str

class CommentLikeResponse(BaseModel):
    comment_id: int
    liked: bool
    like_count: int

    class Config:
        from_attributes = True