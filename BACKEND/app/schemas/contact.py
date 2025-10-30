from pydantic import BaseModel
from datetime import datetime

class ContactBase(BaseModel):
    name: str
    email: str
    message: str

class ContactCreate(ContactBase):
    pass

class Contact(ContactBase):
    id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True