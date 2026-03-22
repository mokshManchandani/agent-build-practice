from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: str


class ConfirmationRequest(BaseModel):
    session_id: str
    user_id: str
    function_call_id: Optional[str] = None
    invocation_id: Optional[str] = None
    confirmed: bool
    payload: dict = Field(default_factory=dict)


class ClarificationRequest(BaseModel):
    session_id: str
    user_id: str
    invocation_id: str
    answer: str


class SessionResponse(BaseModel):
    session_id: str
