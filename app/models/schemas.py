from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime


class User(BaseModel):
    id: int
    email: str
    password: str
    codeforces_handle: str

class RegisterUser(BaseModel):
    email: str
    password: str
    codeforces_handle: str

class LoginUser(BaseModel):
    email: str
    password: str

class PrintUser(BaseModel):
    email: str
    codeforces_handle: str


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None
    id: int | None = None


class Problem(BaseModel):
    id: int | None
    contest_id: int
    index: str
    name: str | None
    rating: int | None
    tags: List[str] | None

class SaveProblem(BaseModel):
    contest_id: int
    index: str
    name: str | None
    rating: int | None
    tags: List[str] | None


class FindProblem(BaseModel):
    contest_id : int | None
    index : str | None



class Conversation(BaseModel):
    id: int
    name: str

class Message(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

class GetMessage(BaseModel):
    content: str

class ProblemData:
    title: str | None
    time_limit: str | None
    memory_limit: str | None
    statement: List[str] | None
    input_spec: List[str] | None
    output_spec: List[str] | None
    note: List[str] | None
    samples: List[str] | None
    raw_text: str | None

    def __init__(self, data: Dict):
        self.title = data["title"]
        self.time_limit = data["time_limit"]
        self.memory_limit = data["memory_limit"]
        self.statement = data["statement"]
        self.input_spec = data["input_spec"]
        self.output_spec = data["output_spec"]
        self.note = data["note"]
        self.samples = data["samples"]
        self.raw_text = data["raw_text"]



class ProblemMinimal(BaseModel):
    id: int
    contest_id: int
    index: str
    name: Optional[str]
    rating: Optional[int]
    tags: Optional[list]

class RecommendationSchema(BaseModel):
    id: int
    user_id: int
    problem_id: int
    reason: Optional[str]
    score: float
    completed: bool
    created_at: datetime
    completed_at: Optional[datetime]
    problem: Optional[ProblemMinimal]

    class Config:
        orm_mode = True
