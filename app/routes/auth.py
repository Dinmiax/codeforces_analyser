import sys
sys.path.append("../")

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.base import get_db
from app.database import models

from app.hashing import Hash
from app.JWTtoken import create_access_token

router = APIRouter(
    tags=["Login"],
    prefix="/login"
)

@router.post('/') 
# def login(request: schemas.OauthForm, db: Session = Depends(database.get_db)):  #without OAuth2PasswordRequestForm
#     librarian = db.query(models.Librarians).filter(models.Librarians.email == request.email).first()
def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.username).first()
    if (not user or not Hash.verify(user.password, request.password)):
        raise HTTPException(status_code=400, detail=f"Incorrect username or password")

    access_token = create_access_token(data={"sub": user.email, "id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}