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

    async def verify_fact(self, fact: Dict, timeout_sec: int = 8, retry: int = 1) -> Dict:
        title = fact.get("title") or ""
        year = fact.get("year")
        person = fact.get("person") or ""
        desc = fact.get("description") or ""
        source_hint = fact.get("source") or ""
        fact_brief = f"Title: {title}\nYear: {year}\nPerson: {person}\nDescription: {desc}\nSourceHint: {source_hint}"
        system_msg = {
            "role": "system",
            "content": "Ты — проверяющий факты об истории математики, алгоритмов и структур данных. Отвечай кратко и точно."
        }
        user_prompt = (
            "Проверь, пожалуйста, корректность следующего факта. "
            "Ответь ТОЛЬКО JSON-объектом в формате:\n"
            '{"verified": true|false|null, "confidence": 0.0-1.0, "evidence": "короткая строка/URL or null"}\n'
            "- verified = true если факт подтверждается надежными источниками;\n"
            "- verified = false если фактическая ошибка (имя/год/событие неверны);\n"
            "- verified = null если модель не уверена или нет источника.\n"
            "- confidence — число от 0 до 1, 1 — полностью уверена.\n"
            "Никаких дополнительных слов, только JSON.\n\n"
            f"Факт:\n{fact_brief}\n"
        )

        messages = [system_msg, {"role": "user", "content": user_prompt}]
        raw = ""
        parsed = None
        attempts = 0
        while attempts <= retry:
            attempts += 1
            try:
                raw = await asyncio.wait_for(self.llm.send_by_chat_wraper(messages, stream=False), timeout=timeout_sec)
            except Exception as e:
                fact.update({
                    "verified": None,
                    "confidence": None,
                    "evidence": f"LLM error: {e}",
                    "checked_at": datetime.datetime.utcnow().isoformat() + "Z"
                })
                return fact

            parsed = self._parse_json_object(raw)
            if parsed is not None:
                break
            messages = [
                system_msg,
                {"role": "user",
                 "content": "Ты должен вернуть ТОЛЬКО JSON в указанном формате. Пожалуйста, верни корректный JSON для проверки выше.\n\nИсходный ответ:\n" + raw}
            ]
        if parsed is None:
            verified = None
            confidence = None
            evidence = None
            if raw:
                if re.search(r"\\btrue\\b", raw, flags=re.IGNORECASE):
                    verified = True
                elif re.search(r"\\bfalse\\b", raw, flags=re.IGNORECASE):
                    verified = False
                num = re.search(r"0(?:\\.\\d+)?|1(?:\\.0+)?|0?\\.\\d+", raw)
                if num:
                    try:
                        confidence = float(num.group(0))
                        if confidence > 1:
                            confidence = confidence / 100.0 if confidence <= 100 else None
                    except Exception:
                        confidence = None
                evidence = raw.strip()[:200]
            fact.update({
                "verified": verified,
                "confidence": confidence,
                "evidence": evidence,
                "checked_at": datetime.datetime.utcnow().isoformat() + "Z",
                "raw_verification": raw
            })
            return fact
        verified = parsed.get("verified")
        confidence = parsed.get("confidence")
        evidence = parsed.get("evidence") or parsed.get("source") or None
        if isinstance(verified, str):
            if verified.lower() in ("true", "yes", "1"):
                verified = True
            elif verified.lower() in ("false", "no", "0"):
                verified = False
            else:
                verified = None
        if isinstance(confidence, (int, float)):
            try:
                confidence = float(confidence)
                if confidence < 0:
                    confidence = 0.0
                if confidence > 1:
                    if confidence <= 100:
                        confidence = round(confidence / 100.0, 3)
                    else:
                        confidence = 1.0
            except Exception:
                confidence = None
        else:
            confidence = None

        fact.update({
            "verified": bool(verified) if isinstance(verified, bool) else None,
            "confidence": confidence,
            "evidence": evidence,
            "checked_at": datetime.datetime.utcnow().isoformat() + "Z",
            "raw_verification": raw
        })
        return fact

    async def verify_facts_batch(self, facts: List[Dict], concurrency: int = 3) -> List[Dict]:
        sem = asyncio.Semaphore(concurrency)

        async def worker(f):
            async with sem:
                try:
                    return await self.verify_fact(f)
                except Exception as e:
                    f.update({
                        "verified": None,
                        "confidence": None,
                        "evidence": f"internal error: {e}",
                        "checked_at": datetime.datetime.utcnow().isoformat() + "Z"
                    })
                    return f

        tasks = [worker(fact) for fact in facts]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return results

    def _parse_json_object(self, text: str) -> Optional[Dict]:
        if not text or not isinstance(text, str):
            return None
        try:
            obj = json.loads(text.strip())
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                obj = json.loads(m.group(0))
                if isinstance(obj, dict):
                    return obj
            except Exception:
                s = m.group(0)
                last = s.rfind("}")
                if last != -1:
                    try:
                        obj = json.loads(s[: last + 1])
                        if isinstance(obj, dict):
                            return obj
                    except Exception:
                        pass
        return None
