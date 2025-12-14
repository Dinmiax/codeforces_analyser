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
from app.services.codeforces_update import CodeforcesUpdater
# from app.models.schemas import User, UserStats, UserProblem
# from app.core.auth import get_current_user
from typing import List


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get("/all", response_model=List[schemas.User])
async def get_all(db: Session = Depends(get_db)):
    all_users = db.query(models.User).all()
    return all_users

@router.get("/me")
async def get_me(db: Session = Depends(get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    user_service = UserService(db)
    user = await user_service.get_user_by_id(current_user.id)
    return user
    

@router.post("/update_solved_problems")
async def get_solved(db: Session = Depends(get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    user_service = UserService(db)
    codeforces_updater = CodeforcesUpdater(db)
    user = await user_service.get_user_by_id(current_user.id)
    if (not user):
        raise HTTPException(403, "Not authorized")

    problems = await codeforces_updater.get_solved_problems(user.codeforces_handle)

    problems = await codeforces_updater.add_problems(problems)
    tmp = await user_service.connect_with_problems(user, problems)


@router.get("/get_solved_problems", response_model=List[schemas.Problem])
async def get_solved(db: Session = Depends(get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    user_service = UserService(db)
    user = await user_service.get_user_by_id(current_user.id)
    return await user_service.get_solved_problems(user)