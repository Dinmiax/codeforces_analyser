from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.services.recomendation_service import RecommendationService
from app.models.schemas import ProblemMinimal

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"]
)


@router.get("/by-weak-topic/{user_id}", response_model=List[ProblemMinimal])
def recommend_by_weak_topic(user_id: int, db: Session = Depends(get_db)):
    service = RecommendationService(db)
    problems = service.recommend_by_weak_topic(user_id=user_id, limit=10)
    if not problems:
        raise HTTPException(status_code=404, detail="No recommendations found or insufficient data.")
    return problems


@router.post("/smart/{user_id}")
def smart_recommendation_placeholder(user_id: int):
    """
    будет позже
    """
    raise HTTPException(status_code=501, detail="Smart recommendation mode is not implemented yet.")
