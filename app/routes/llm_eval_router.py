from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database.base import get_db
from app.services.llm_eval_service import LLMEvalService

router = APIRouter(
    prefix="/llm-eval",
    tags=["llm-eval"]
)


@router.post("/score", response_model=LLMEvalResponse)
async def evaluate_llm_answer(payload: LLMEvalRequest, db: Session = Depends(get_db)):
    if not payload.original_query.strip():
        raise HTTPException(status_code=400, detail="original_query is empty")
    if not payload.model_answer.strip():
        raise HTTPException(status_code=400, detail="model_answer is empty")
    service = LLMEvalService(db)
    result = await service.evaluate_response(
        original_query=payload.original_query,
        model_answer=payload.model_answer
    )

    return result
