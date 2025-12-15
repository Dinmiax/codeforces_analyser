from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.base import get_db
from app.services.topic_difficulty_service import TopicDifficultyService

router = APIRouter(
    prefix="/topics",
    tags=["topics"]
)


@router.get("/hardest")
def get_hardest_topics(top_n: int = 10, min_problems: int = 3, db: Session = Depends(get_db)):
    service = TopicDifficultyService(db)
    topics = service.get_global_hard_topics(
        top_n=top_n,
        min_problems=min_problems
    )
    if not topics:
        raise HTTPException(
            status_code=404,
            detail="No difficulty statistics available."
        )
    return {
        "mode": "global",
        "topics": topics
    }


@router.get("/hardest/{user_id}")
def get_user_hardest_topics(user_id: int, top_n: int = 10, min_problems: int = 2, db: Session = Depends(get_db)):
    service = TopicDifficultyService(db)
    topics = service.get_user_hard_topics(
        user_id=user_id,
        top_n=top_n,
        min_problems=min_problems
    )
    if not topics:
        raise HTTPException(
            status_code=404,
            detail="No difficulty statistics for this user."
        )
    return {
        "mode": "user",
        "user_id": user_id,
        "topics": topics
    }
