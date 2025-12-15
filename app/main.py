import sys

import logging
from fastapi import FastAPI
from database.base import engine, get_db, Base
import models
import uvicorn
from routes import users, register, auth, conversation, recommendations, fact, topics
from config import settings

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Codeforces Tutor API",
    description="API for learning competitive programming with Codeforces",
    version="1.0.0"
)

app.include_router(recommendations.router)
app.include_router(users.router)
app.include_router(register.router)
app.include_router(auth.router)
app.include_router(conversation.router)
app.include_router(fact.router)
app.include_router(topics.router)

if __name__ == "__main__":
    logging.getLogger('passlib').setLevel(logging.ERROR)
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
