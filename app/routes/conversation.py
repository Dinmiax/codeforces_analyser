import sys
sys.path.append("../")

import asyncio
from fastapi import APIRouter, Depends, HTTPException
import oauth2
from sqlalchemy.orm import Session

from app.database.base import get_db
from app.database import models

from app.models import schemas

from app.services.user_service import UserService
from app.services.codeforces_update import CodeforcesUpdater, ProblemParser
from app.services.llm_service import LLM_service
# from app.models.schemas import User, UserStats, UserProblem
# from app.core.auth import get_current_user
from typing import List


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

# @router.get("/send")
# async def send_message():
#     llm_service = LLM_service(None)

#     chat = [
#         {"role": "system", "content": "You are the friend of user."},
#         {"role": "user", "content": "HI! How are you?"}
#     ]
#     response = await llm_service.send_message(chat)
#     return response

@router.post("/create_conversation", response_model=schemas.Conversation)
async def create_conversation(base_problem: schemas.FindProblem, db: Session = Depends(get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    user_service = UserService(db)
    llm_service = LLM_service(db)
    problem_parser = ProblemParser()
    
    
    user = await user_service.get_user_by_id(current_user.id)
    problem_data = await problem_parser.get_problem(base_problem)
    conversation = await llm_service.create_conversation(user, problem_data)
    
        # raise HTTPException(503, "Sorry, we can't get the task")
    return conversation

@router.get("/get_conversation/{id}", response_model=List[schemas.Message])
async def get_conversation(id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    user_service = UserService(db)
    llm_service = LLM_service(db)

    user = await user_service.get_user_by_id(current_user.id)
    messages = await llm_service.get_conversation(user, id)
    if (messages is None):
        raise HTTPException(403, "No such conversation")
    
    return messages

@router.post("/send/{id}", response_model=List[schemas.Message])
async def send_message(id: int, message: schemas.GetMessage, db: Session = Depends(get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    user_service = UserService(db)
    llm_service = LLM_service(db)

    user = await user_service.get_user_by_id(current_user.id)

    messages = await llm_service.send_message(user, id, message)
    return messages
    
# @router.post("/hehe/")
# async def hehe(problem: schemas.FindProblem):
#     llm_service = LLM_service(None)
#     problem_parser = ProblemParser()
#     problem_data = await problem_parser.get_problem(problem)
#     return llm_service.create_base_prompt(problem_data)