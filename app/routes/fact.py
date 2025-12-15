from app.services.fact_service import FactsService
from app.database.base import get_db
from app.services.recomendation_service import RecommendationService

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/facts",
    tags=["Facts"]
)

@router.get("/by-weak-tag/{user_id}")
async def route(user_id: int, db=Depends(get_db)):
    service = RecommendationService(db)
    fs = FactsService(db)
    weak_tag = service.get_weak_tags(user_id)
    weak_tag = weak_tag or "algorithms"
    facts = await fs.fetch_facts_text(weak_tag, n=5)  # как будто тут лучше 3-7 ставить
    return {"facts": facts}
