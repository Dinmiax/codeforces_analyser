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


@router.post("/smart/{user_id}", response_model=List[ProblemMinimal])
async def smart_recommendation(user_id: int, db: Session = Depends(get_db)):
    service = RecommendationService(db)
    problems = service.recommend_smart(user_id=user_id, limit=10)

    if not problems:
        raise HTTPException(status_code=404, detail="No recommendations found or insufficient data.")
    llm = LLM_service(db)
    tasks = []
    prob_datas = []
    for p in problems:
        pdata = {
            "title": p.name or f"{p.contest_id}{p.index}",
            "time_limit": None,
            "memory_limit": None,
            "statement": [],
            "input_spec": [],
            "output_spec": [],
            "note": [],
            "samples": [],
            "raw_text": None
        }
        prob_obj = ProblemData(pdata)
        prob_datas.append((p, prob_obj))
        tasks.append(llm.get_short_hint(prob_obj))

    hints = await asyncio.gather(*tasks, return_exceptions=True)

    for (p, _), hint in zip(prob_datas, hints):
        if isinstance(hint, Exception) or not hint:
            continue
        rec = (
            db.query(db_models.Recommendation)
            .filter(
                db_models.Recommendation.user_id == user_id,
                db_models.Recommendation.problem_id == p.id
            )
            .order_by(db_models.Recommendation.created_at.desc())
            .first()
        )
        if rec:
            prefix = (rec.reason + " ") if rec.reason else ""
            rec.reason = f"{prefix}hint: {hint}"
            db.add(rec)
    try:
        db.commit()
    except Exception:
        db.rollback()
    return problems