from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext

from models import schemas
from config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
TOKEN_EXPIRE_TIME = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_TIME)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentials_exception: HTTPException):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        id = payload.get("id")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(id=id, email=email)
        return token_data
    except InvalidTokenError:
        raise credentials_exception
