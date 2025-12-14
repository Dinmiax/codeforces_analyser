import sys

sys.path.append("../")

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from fastapi import HTTPException

from app.database import models
from app.models import schemas
from app.hashing import Hash


class UserService:
    def __init__(self, db: Session):
        self.db = db

    async def get_user_by_id(self, user_id: int) -> Optional[models.User]:
        user = self.db.query(models.User).filter(models.User.id == user_id).first()
        return user

    async def register_new_user(self, request: schemas.RegisterUser):
        existing = self.db.query(models.User).filter(models.User.email == request.email).first()
        if (existing):
            raise HTTPException(status_code=400, detail=f"User with such email already exist")

        new_user = models.User(email=request.email, codeforces_handle=request.codeforces_handle,
                               password=Hash.get_hash(request.password))
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    async def connect_with_problems(self, user: models.User, problems: List[models.Problem]) -> List[models.Problem]:
        for problem in problems:
            if (problem.id in [i.id for i in user.solved_problems]):
                continue
            assoc = models.UserProblem(
                user=user,
                problem=problem,
            )
            self.db.add(assoc)
        self.db.commit()
        for problem in problems:
            self.db.refresh(problem)
        return problems

    async def get_solved_problems(self, user: models.User) -> List[models.Problem]:
        return user.solved_problems
