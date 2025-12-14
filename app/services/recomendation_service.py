from typing import List, Tuple, Dict, Set
from sqlalchemy.orm import Session
from app.database import models as db_models
from app.models.schemas import ProblemMinimal


class RecommendationService:
    def __init__(self, db: Session):
        self.db = db

    def _get_user_solved_problem_ids(self, user_id: int) -> Set[int]:
        assocs = (
            self.db.query(db_models.UserProblem)
            .filter(db_models.UserProblem.user_id == user_id)
            .all()
        )
        return {a.problem_id for a in assocs}

    def _get_tag_totals_and_solved(self, user_id: int) -> Tuple[Dict[str, int], Dict[str, int]]:
        totals: Dict[str, int] = {}
        solveds: Dict[str, int] = {}
        all_problems = self.db.query(db_models.Problem).all()
        user_solved_ids = self._get_user_solved_problem_ids(user_id)
        for p in all_problems:
            tags = p.tags or []
            for t in tags:
                totals[t] = totals.get(t, 0) + 1
                if p.id in user_solved_ids:
                    solveds[t] = solveds.get(t, 0) + 1

        return totals, solveds

    def get_weak_tags(self, user_id: int, top_n: int = 3) -> List[Tuple[str, float]]:
        totals, solveds = self._get_tag_totals_and_solved(user_id)
        if not totals:
            return []

        ratios = []
        for t, tot in totals.items():
            solved = solveds.get(t, 0)
            ratio = solved / tot if tot > 0 else 0.0
            ratios.append((t, ratio))
        ratios.sort(key=lambda x: x[1])
        return ratios[:top_n]

    def recommend_by_weak_topic(self, user_id: int, limit: int = 10) -> List[ProblemMinimal]:
        totals, solveds = self._get_tag_totals_and_solved(user_id)
        if not totals:
            return []
        tag_ratios = []
        for t, tot in totals.items():
            solved = solveds.get(t, 0)
            ratio = solved / tot if tot > 0 else 0.0
            tag_ratios.append((ratio, t))
        tag_ratios.sort(key=lambda x: x[0])

        user_solved_ids = self._get_user_solved_problem_ids(user_id)
        candidates = []
        seen_problem_ids = set()
        all_problems = self.db.query(db_models.Problem).all()

        for ratio, tag in tag_ratios:
            for p in all_problems:
                if p.id in user_solved_ids:
                    continue
                if not p.tags:
                    continue
                if tag in p.tags and p.id not in seen_problem_ids:
                    candidates.append(p)
                    seen_problem_ids.add(p.id)
            if len(candidates) >= limit:
                break

        def rating_key(p: db_models.Problem):
            return (p.rating if p.rating is not None else 10 ** 9, p.id)

        candidates = sorted(candidates, key=rating_key)[:limit]
        saved_recs = []
        for p in candidates:
            reason = f"weak_tag:{tag_ratios[0][1]}" if tag_ratios else "weak_tag:unknown"
            rec = db_models.Recommendation(
                user_id=user_id,
                problem_id=p.id,
                reason=reason,
                score=0.0
            )
            self.db.add(rec)
            saved_recs.append(rec)
        if saved_recs:
            self.db.commit()
        results: List[ProblemMinimal] = []
        for p in candidates:
            results.append(
                ProblemMinimal(
                    id=p.id,
                    contest_id=p.contest_id,
                    index=p.index,
                    name=p.name,
                    rating=p.rating,
                    tags=p.tags,
                )
            )
        return results

    def get_user_recommendations(self, user_id: int, limit: int = 10) -> List[RecommendationSchema]:
        # Implementation to get user recommendations
        pass

    def generate_recommendations(self, user_id: int):
        # Implementation to generate new recommendations based on user performance
        pass

    def mark_completed(self, recommendation_id: int, user_id: int):
        # Implementation to mark recommendation as completed
        pass
