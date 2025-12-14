import sys
sys.path.append("../")

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.base import get_db
from models import schemas
from services.user_service import UserService


router = APIRouter(
    prefix="/register",
    tags=["Register"]
)

@router.post("/")
async def register_new_user(request: schemas.RegisterUser, db: Session = Depends(get_db)):
    user_service = UserService(db)
    new_user = user_service.register_new_user(request)
    return new_user
