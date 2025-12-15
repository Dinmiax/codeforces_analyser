import json
import asyncio
import re
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import datetime
from typing import Union

from app.services.llm_service import LLM_service


class FactsService:
    def __init__(self, db: Session):
        self.db = db
        self.llm = LLM_service(db)

    async def fetch_facts(self, topic: str, n: int = 5, modern_only: bool = True) -> List[Dict]:
        era_hint = (
            "Современные факты (20-й и 21-й века)."
            if modern_only
            else "Включая исторические и современные факты."
        )
        prompt = (
            f"Ты — эксперт по истории математики и алгоритмов и структур данных."
            f"Опиши до {n} интересных, проверяемых фактов по теме: '{topic}'. "
            f"{era_hint} "
            "Для каждого факта верни JSON-объект с полями "
            "[\"title\", \"year\", \"person\", \"description\", \"source\"]. "
            "Поле `description` — коротко 20–40 слов (одна-две фразы), без кода. "
            "Поле `year` — число или null, `person` — имя или null, `source` — краткая ссылка или null. "
            "Верни строго ТОЛЬКО JSON-массив объектов (без дополнительного текста)."
        )

        messages = [
            {"role": "system", "content": "Ты — эксперт по истории математики и алгоритмов. Отвечай кратко и точно."},
            {"role": "user", "content": prompt},
        ]

        try:
            resp = await self.llm.send_by_chat_wraper(messages, stream=False)
        except Exception:
            return []
        facts = self._parse_json_array(resp)
        if not facts:
            refine_prompt = (
                "Ответ предыдущей модели был нечётким. Пожалуйста, верни ТОЛЬКО JSON-массив с теми же полями, "
                f"максимум {n} объектов. Исходный ответ:\n{resp}"
            )
            messages_refine = [
                {"role": "system", "content": "Ты — ассистент, который возвращает корректный JSON."},
                {"role": "user", "content": refine_prompt},
            ]
            try:
                resp2 = await self.llm.send_by_chat_wraper(messages_refine, stream=False)
                facts = self._parse_json_array(resp2)
            except Exception:
                facts = []

        normalized = []
        for obj in facts[:n]:
            if not isinstance(obj, dict):
                continue
            title = obj.get("title") or obj.get("name") or obj.get("fact") or None
            year = obj.get("year") if isinstance(obj.get("year"), int) else None
            person = obj.get("person") or obj.get("author") or None
            description = obj.get("description") or obj.get("desc") or None
            source = obj.get("source") or None
            if isinstance(description, str):
                description = " ".join(description.split())
            normalized.append({
                "title": title,
                "year": year,
                "person": person,
                "description": description,
                "source": source,
            })

        return normalized

    async def fetch_facts_text(self, topic: str, n: int = 5, modern_only: bool = True) -> List[str]:
        facts = await self.fetch_facts(topic=topic, n=n, modern_only=modern_only)
        out = []
        for f in facts:
            parts = []
            if f.get("title"):
                parts.append(str(f.get("title")))
            if f.get("year"):
                parts.append(str(f.get("year")))
            if f.get("person"):
                parts.append(str(f.get("person")))
            line = " — ".join(parts) if parts else "Факт"
            if f.get("description"):
                line = f"{line}: {f.get('description')}"
            if f.get("source"):
                line = f"{line} (source: {f.get('source')})"
            out.append(line)
        return out

    def _parse_json_array(self, text: str) -> List[Dict]:
        if not text or not isinstance(text, str):
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict) and isinstance(parsed.get("facts"), list):
                return parsed.get("facts")
        except Exception:
            pass
        m = re.search(r"\[[\s\S]*\]", text)
        if m:
            try:
                parsed = json.loads(m.group(0))
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                s = m.group(0)
                last = s.rfind(']')
                if last != -1:
                    try:
                        parsed = json.loads(s[: last + 1])
                        if isinstance(parsed, list):
                            return parsed
                    except Exception:
                        pass
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        cleaned = [ln for ln in lines if len(ln) > 20][:20]
        out = []
        for ln in cleaned[:20]:
            out.append({"title": None, "year": None, "person": None, "description": ln, "source": None})
        return out
