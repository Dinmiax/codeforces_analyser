from typing import List, Tuple, Dict, Set
from sqlalchemy.orm import Session
from app.database import models as db_models
from app.models.schemas import ProblemMinimal

import math
from collections import defaultdict
from typing import List


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

    def estimate_user_rating(self, user_id: int) -> float:
        solved = self.db.query(db_models.UserProblem).filter(db_models.UserProblem.user_id == user_id).all()
        ratings = []
        for s in solved:
            if s.problem and s.problem.rating:
                ratings.append(s.problem.rating)
        if not ratings:
            return 1500.0
        return sum(ratings) / len(ratings)

    def recommend_smart(self, user_id: int, limit: int = 10, candidate_pool: int = 200) -> List[ProblemMinimal]:
        user = self.db.query(db_models.User).filter(db_models.User.id == user_id).first()
        if not user:
            return []
        solved_ids = self._get_user_solved_problem_ids(user_id)
        totals, solveds = self._get_tag_totals_and_solved(user_id)
        if not totals:
            all_problems = self.db.query(db_models.Problem).filter(~db_models.Problem.id.in_(list(solved_ids))).limit(
                limit).all()
            return [ProblemMinimal(id=p.id, contest_id=p.contest_id, index=p.index, name=p.name, rating=p.rating,
                                   tags=p.tags) for p in all_problems]
        tag_weakness = {}
        for t, tot in totals.items():
            solved = solveds.get(t, 0)
            tag_weakness[t] = 1.0 - (solved / tot) if tot > 0 else 1.0

        user_rating = self._estimate_user_rating(user_id)

        sorted_tags = sorted(tag_weakness.items(), key=lambda x: x[1], reverse=True)
        candidates = []
        seen = set()
        all_problems = self.db.query(db_models.Problem).all()
        for tag, weakness in sorted_tags:
            for p in all_problems:
                if p.id in seen or p.id in solved_ids:
                    continue
                if not p.tags:
                    continue
                if tag in p.tags:
                    candidates.append((p, weakness))
                    seen.add(p.id)
                    if len(candidates) >= candidate_pool:
                        break
            if len(candidates) >= candidate_pool:
                break

        if len(candidates) < candidate_pool:
            for p in all_problems:
                if p.id in seen or p.id in solved_ids:
                    continue
                candidates.append((p, 0.0))
                seen.add(p.id)
                if len(candidates) >= candidate_pool:
                    break

        scored = []
        ratings_list = [p.rating for (p, _) in candidates if p.rating is not None]
        max_rating = max(ratings_list) if ratings_list else 2000.0
        min_rating = min(ratings_list) if ratings_list else 800.0
        for p, weakness in candidates:
            if p.rating is None:
                diff_match = 0.5
            else:
                gap = p.rating - user_rating
                diff_match = math.exp(-abs(gap) / 200.0)
            p_tags = p.tags or []
            seen_tag = any(((t in totals) and (solveds.get(t, 0) > 0)) for t in p_tags)
            novelty = 0.0 if seen_tag else 1.0
            pop_norm = 0.0
            if p.rating:
                pop_norm = (p.rating - min_rating) / (max_rating - min_rating + 1e-9)
            score = 0.45 * weakness + 0.30 * diff_match + 0.15 * novelty + 0.10 * pop_norm

            scored.append((p, score, weakness))

        scored.sort(key=lambda x: x[1], reverse=True)
        result = []
        tag_count = defaultdict(int)
        for p, score, weakness in scored:
            p_tags = p.tags or []
            primary_tag = p_tags[0] if p_tags else "misc"
            if tag_count[primary_tag] >= 3:
                found_slot = False
                for t in p_tags:
                    if tag_count[t] < 3:
                        primary_tag = t
                        found_slot = True
                        break
                if not found_slot:
                    continue
            tag_count[primary_tag] += 1
            result.append((p, score))
            if len(result) >= limit:
                break

        recs = []
        for p, score in result:
            rec = db_models.Recommendation(user_id=user_id, problem_id=p.id, reason=f"smart:score={score:.3f}",
                                           score=float(score))
            self.db.add(rec)
            recs.append(rec)
        if recs:
            self.db.commit()

        out = []
        for p, score in result:
            out.append(ProblemMinimal(id=p.id, contest_id=p.contest_id, index=p.index, name=p.name, rating=p.rating,
                                      tags=p.tags))
        return out
