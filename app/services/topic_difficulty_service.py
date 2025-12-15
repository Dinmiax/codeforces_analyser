from typing import List, Dict, Set, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from collections import defaultdict

from app.database import models as db_models


class TopicDifficultyService:
    def __init__(self, db: Session):
        self.db = db

    def _get_all_problems_with_assocs(self) -> List[Any]:
        return (
            self.db.query(db_models.Problem)
            .options(joinedload(db_models.Problem.user_associations))
            .all()
        )

    def _get_total_user_count(self) -> int:
        return self.db.query(db_models.User).count()

    def get_global_hard_topics(self, top_n: int = 10, min_problems: int = 3) -> List[Dict[str, Any]]:
        problems = self._get_all_problems_with_assocs()
        tag_problem_ids: Dict[str, Set[int]] = defaultdict(set)
        tag_solvers: Dict[str, Set[int]] = defaultdict(set)

        for p in problems:
            tags = p.tags or []
            if isinstance(tags, str):
                tags = [tags]
            if not isinstance(tags, (list, tuple)):
                continue
            for t in tags:
                if t is None:
                    continue
                tag_problem_ids[t].add(p.id)
                for assoc in getattr(p, "user_associations", []):
                    if getattr(assoc, "user_id", None) is not None:
                        tag_solvers[t].add(assoc.user_id)

        rows: List[Dict[str, Any]] = []
        avg_list: List[float] = []
        for t, pids in tag_problem_ids.items():
            pcnt = len(pids)
            if pcnt < min_problems:
                continue
            solvers = len(tag_solvers.get(t, set()))
            avg = solvers / pcnt if pcnt > 0 else 0.0
            rows.append({
                "tag": t,
                "problem_count": pcnt,
                "unique_solvers": solvers,
                "avg_solvers_per_problem": avg
            })
            avg_list.append(avg)

        if not rows:
            return []

        min_avg = min(avg_list)
        max_avg = max(avg_list)
        span = max_avg - min_avg if max_avg > min_avg else 1.0
        for r in rows:
            norm = (r["avg_solvers_per_problem"] - min_avg) / span
            r["difficulty"] = round(1.0 - norm, 6)

        rows.sort(key=lambda x: x["difficulty"], reverse=True)
        return rows[:top_n]

    def _get_user_solved_ids(self, user_id: int) -> Set[int]:
        rows = (
            self.db.query(db_models.UserProblem.problem_id)
            .filter_by(user_id=user_id)
            .all()
        )
        return {r[0] for r in rows if r and isinstance(r[0], int)}

    def get_user_hard_topics(self, user_id: int, top_n: int = 10, min_problems: int = 2) -> List[Dict[str, Any]]:
        problems = self._get_all_problems_with_assocs()
        user_solved = self._get_user_solved_ids(user_id)

        tag_problem_ids: Dict[str, Set[int]] = defaultdict(set)
        for p in problems:
            tags = p.tags or []
            if isinstance(tags, str):
                tags = [tags]
            if not isinstance(tags, (list, tuple)):
                continue
            for t in tags:
                if t is None:
                    continue
                tag_problem_ids[t].add(p.id)

        rows: List[Dict[str, Any]] = []
        for t, pids in tag_problem_ids.items():
            pcnt = len(pids)
            if pcnt < min_problems:
                continue
            user_cnt = len(pids.intersection(user_solved))
            ratio = user_cnt / pcnt if pcnt > 0 else 0.0
            user_difficulty = round(1.0 - ratio, 6)
            rows.append({
                "tag": t,
                "problem_count": pcnt,
                "user_solved": user_cnt,
                "user_solved_ratio": round(ratio, 6),
                "user_difficulty": user_difficulty
            })

        rows.sort(key=lambda x: x["user_difficulty"], reverse=True)
        return rows[:top_n]

    def get_all_solved_pairs(self) -> List[Tuple[int, int]]:
        rows = self.db.query(
            db_models.UserProblem.user_id,
            db_models.UserProblem.problem_id
        ).all()
        return [(int(u), int(p)) for u, p in rows]
