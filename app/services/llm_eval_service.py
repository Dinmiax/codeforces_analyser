import json
import re
import asyncio
from typing import List, Dict, Any, Optional

from app.services.llm_service import LLM_service


class LLMEvalService:
    def __init__(self, db):
        self.llm = LLM_service(db)
        self._criteria = [
            ("factuality", "Насколько ответ соответствует фактам и корректен с точки зрения фактической информации."),
            ("completeness",
             "Насколько ответ полный и покрывает все важные аспекты исходного запроса (без ненужного расширения)."),
            ("clarity",
             "Насколько ответ ясен, понятен и полезен для целевой аудитории (без лишней воды и без кода, если запрос был о концептах).")
        ]

    async def _ask_one(self, criterion_key: str, criterion_desc: str, original_query: str, model_answer: str,
                       attempt: int = 1) -> Dict[str, Any]:
        system_msg = {
            "role": "system",
            "content": "Ты — независимый оценщик ответов LLM. Давай коротко и честно."
        }
        user_prompt = (
            f"Оцени, пожалуйста, следующий ответ модели по критерию: {criterion_desc}\n\n"
            "Важные инструкции:\n"
            "- Верни **ТОЛЬКО** JSON-объект в точно таком формате:\n"
            '  {\"score\": <целое от 1 до 10>, \"reason\": \"короткая причина 5-20 слов\"}\n'
            "- score = 1 — очень плохой, 10 — идеальный.\n"
            "- Поле reason — одна-две короткие фразы, почему такая оценка.\n"
            "- НИКАКОГО кода и ничего лишнего вокруг JSON.\n\n"
            f"Исходный запрос пользователя:\n{original_query}\n\n"
            f"Ответ модели:\n{model_answer}\n\n"
            "Если не можешь поставить числовую оценку, укажи score=1 и коротко объясни почему.\n"
        )
        messages = [system_msg, {"role": "user", "content": user_prompt}]

        try:
            raw = await self.llm.send_by_chat_wraper(messages, stream=False)
        except Exception as e:
            return {"criterion": criterion_key, "score": 1, "reason": f"LLM error: {e}", "raw": ""}

        parsed = self._parse_score_from_text(raw)
        if parsed is None and attempt == 1:
            refine_prompt = (
                "Ответ должен быть ТОЛЬКО JSON-объектом в формате "
                "{\"score\":<int 1..10>, \"reason\":\"короткая причина\"}. "
                "Пожалуйста, верни только этот JSON."
            )
            messages_refine = [system_msg, {"role": "user", "content": refine_prompt + "\n\nИсходный ответ:\n" + raw}]
            try:
                raw2 = await self.llm.send_by_chat_wraper(messages_refine, stream=False)
            except Exception:
                raw2 = raw
            parsed = self._parse_score_from_text(raw2)
            raw = raw2
        if parsed is None:
            score = self._extract_first_number(raw) or 1
            score = self._clamp_score(int(round(score)))
            reason = "Could not parse JSON; best-effort extraction."
            return {"criterion": criterion_key, "score": score, "reason": reason, "raw": raw}

        score = self._clamp_score(parsed.get("score", 1))
        reason = parsed.get("reason", "") or ""
        return {"criterion": criterion_key, "score": int(score), "reason": reason, "raw": raw}

    async def evaluate_response(self, original_query: str, model_answer: str) -> Dict[str, Any]:
        tasks = [
            self._ask_one(key, desc, original_query, model_answer)
            for key, desc in self._criteria
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        scores = [r["score"] for r in results if isinstance(r, dict) and "score" in r]
        avg = round(sum(scores) / len(scores), 3) if scores else 0.0

        return {
            "evaluations": results,
            "average_score": avg
        }

    def _parse_score_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        if not text or not isinstance(text, str):
            return None
        try:
            obj = json.loads(text.strip())
            if isinstance(obj, dict) and "score" in obj:
                return obj
        except Exception:
            pass
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                obj = json.loads(m.group(0))
                if isinstance(obj, dict) and "score" in obj:
                    return obj
            except Exception:
                pass
        return None

    def _extract_first_number(self, text: str) -> Optional[int]:
        if not text:
            return None
        nums = re.findall(r"(?<!\d)(?:[1-9]|10)(?!\d)", text)
        if nums:
            try:
                return int(nums[0])
            except Exception:
                return None
        any_nums = re.findall(r"-?\d+", text)
        if any_nums:
            try:
                return int(any_nums[0])
            except Exception:
                return None
        return None

    def _clamp_score(self, val: int) -> int:
        if val is None:
            return 1
        if val < 1:
            return 1
        if val > 10:
            return 10
        return int(val)
