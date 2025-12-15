# app/routes/llm_eval_router.py
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database.base import get_db
from app.services.llm_eval_service import LLMEvalService

router = APIRouter(
    prefix="/llm-eval",
    tags=["llm-eval"]
)


class LLMEvalRequest(BaseModel):
    original_query: str = Field(..., description="Исходный запрос пользователя")
    model_answer: str = Field(..., description="Ответ модели, который нужно оценить")


class EvaluationItem(BaseModel):
    criterion: str
    score: int
    reason: Optional[str] = None
    raw: Optional[str] = None


class LLMEvalResponse(BaseModel):
    evaluations: List[EvaluationItem]
    average_score: float


@router.post("/score", response_model=LLMEvalResponse)
async def evaluate_llm_answer(payload: LLMEvalRequest, db: Session = Depends(get_db)):
    """
    Оценивает ответ LLM по нескольким критериям (3 внутренних запроса к LLM),
    возвращает частные оценки и средний балл.
    """
    if not payload.original_query.strip():
        raise HTTPException(status_code=400, detail="original_query is empty")
    if not payload.model_answer.strip():
        raise HTTPException(status_code=400, detail="model_answer is empty")

    service = LLMEvalService(db)
    result = await service.evaluate_response(
        original_query=payload.original_query,
        model_answer=payload.model_answer
    )

    # Привести результат в Pydantic-формат: service возвращает dict с keys "evaluations" и "average_score"
    # Убедимся, что каждая evaluation содержит нужные поля
    evals = []
    for r in result.get("evaluations", []):
        evals.append(
            EvaluationItem(
                criterion=r.get("criterion", ""),
                score=int(r.get("score", 1)),
                reason=r.get("reason"),
                raw=r.get("raw")
            )
        )

    resp = LLMEvalResponse(evaluations=evals, average_score=float(result.get("average_score", 0.0)))
    return resp
