from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)
    client_code: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    client_name: Optional[str] = None
    client_code: Optional[str] = None

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    data_source: Optional[str] = None


class ChatLogItem(BaseModel):
    id: int
    timestamp: datetime
    user_message: str
    ai_response: Optional[str] = None
    intent: Optional[str] = None
    data_source: Optional[str] = None

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    items: List[ChatLogItem]