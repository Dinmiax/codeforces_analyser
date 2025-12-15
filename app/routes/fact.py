from app.services.fact_service import FactsService
from app.database.base import get_db
from app.services.recomendation_service import RecommendationService


@router.get("/facts/by-weak-tag/{user_id}")
async def route(user_id: int, db=Depends(get_db)):
    service = RecommendationService(db)
    fs = FactsService(db)
    weak_tag = service.get_weakest_tag(user_id)
    weak_tag = weak_tag or "algorithms"
    facts = await fs.fetch_facts_text(weak_tag, n=5)  # как будто тут лучше 3-7 ставить
    return {"facts": facts}
