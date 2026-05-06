from pydantic import BaseModel

class AuthRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    prompt: str

class RechargeRequest(BaseModel):
    amount: int

class DevLoginRequest(BaseModel):
    username: str