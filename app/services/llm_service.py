import sys

sys.path.append('../')

import asyncio
import aiohttp
import json
import re
from collections import defaultdict
from typing import List, Dict, Tuple

from sqlalchemy.orm import Session
from app.database import base
from app.models import schemas
from app.database import models
from app.config import settings


class LLM_service:
    def __init__(self, db):
        self.db = db
        self.api_url = settings.LLM_API_URL
        self.model = settings.LLM_MODEL

    async def send_by_chat(self, messages, stream: bool = False):
        url = f"{self.api_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    response.raise_for_status()

                    if stream:
                        async for line in response.content:
                            if line:
                                try:
                                    data = json.loads(line.decode('utf-8'))
                                    if 'message' in data and 'content' in data['message']:
                                        yield data['message']['content']
                                    if data.get('done', False):
                                        break
                                except json.JSONDecodeError:
                                    continue
                    else:
                        data = await response.json()
                        if 'message' in data and 'content' in data['message']:
                            yield data['message']['content']

        except aiohttp.ClientConnectionError:
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}")
        except aiohttp.ClientError as e:
            raise RuntimeError(f"HTTP error: {e}")

    async def send_by_chat_wraper(self, messages, stream: bool = False) -> str:
        resonse = ""
        async for chunk in self.send_by_chat(messages, stream):
            resonse += chunk
        return resonse

    def create_base_prompt(self, problem: schemas.ProblemData) -> str:
        task_parts = []

        if problem.title:
            task_parts.append(f"### **Название:** {problem.title}\n")

        if problem.time_limit or problem.memory_limit:
            task_parts.append("### **Ограничения:**\n")
            if problem.time_limit:
                task_parts.append(f"- Время: {problem.time_limit}\n")
            if problem.memory_limit:
                task_parts.append(f"- Память: {problem.memory_limit}\n")

        if problem.statement:
            task_parts.append("### **Условие:**\n")
            task_parts.extend(f"{line}\n" for line in problem.statement)

        if problem.input_spec:
            task_parts.append("### **Формат входных данных:**\n")
            task_parts.extend(f"{line}\n" for line in problem.input_spec)

        if problem.output_spec:
            task_parts.append("### **Формат выходных данных:**\n")
            task_parts.extend(f"{line}\n" for line in problem.output_spec)

        if problem.samples:
            task_parts.append("### **Примеры:**\n")
            task_parts.extend(f"{sample}\n" for sample in problem.samples)

        if problem.note:
            task_parts.append("### **Примечание:**\n")
            task_parts.extend(f"{line}\n" for line in problem.note)

        if problem.raw_text:
            task_parts.append("### **Полный текст:**\n")
            task_parts.append(f"{problem.raw_text}\n")

        task_block = "".join(task_parts)
        prompt = f"""Ты — опытный преподаватель программирования, алгоритмов и структур данных. Объясни решение следующей задачи на русском языке. Объяснение должно быть пошаговым, понятным для ученика, готовящегося к олимпиадам."""
        user_prompt = f"""
    **Процесс объяснения:**
    1.  **Повтори условие:** Кратко сформулируй задачу своими словами.
    2.  **Разбери ключевую идею:** Объясни основную мысль решения (какой алгоритм, структура данных или математический факт лежит в основе). Почему это применимо здесь?
    3.  **Представь алгоритм:** Опиши шаги решения логично и последовательно. Если решение сложное, разбей его на логические этапы.
    4.  **Проанализируй сложность:** Оцени временную и, если важно, память.
    5.  **Разбери пример(ы):** Покажи, как предложенный алгоритм работает на конкретных примерах из условия или своих (если нужно).
    6.  **Ответь на возможные вопросы:** Предположи, какие сложные моменты или подводные камни могут возникнуть у решающего, и кратко поясни их.
    7.  **Код (если уместно):** *Не приводи полный код, если не просят особо.* Вместо этого можно показать ключевой фрагмент (псевдокод или синтаксис на Python/C++) и пояснить его работу. Основной акцент — на понимании, а не на реализации.

    **САМА ЗАДАЧА:**

    [НАЧАЛО БЛОКА ЗАДАЧИ]
    {task_block}
    [КОНЕЦ БЛОКА ЗАДАЧИ]

        **Теперь, пожалуйста, приступи к объяснению, следуя инструкциям выше.**
        """
        return (prompt, user_prompt)

    async def create_conversation(self, user: models.User, problem: schemas.ProblemData) -> models.Conversation:
        new_chat = models.Conversation(user_id=user.id, name=f"{problem.title}")
        self.db.add(new_chat)
        self.db.commit()
        self.db.refresh(new_chat)
        system_message_prompt, user_message_prompt = self.create_base_prompt(problem)

        system_message = models.Message(conversation_id=new_chat.id, role="system",
                                        content=system_message_prompt)


        self.db.add(system_message)
        # print(user_message_prompt)
        self.db.commit()
        await self.send_message(user, new_chat.id, schemas.GetMessage(content=user_message_prompt))
        return new_chat

    async def get_conversation(self, user: models.User, conversation_id: int) -> List[models.Message] | None:
        conv = self.db.query(models.Conversation).filter(models.Conversation.id == conversation_id,
                                                         models.Conversation.user_id == user.id).first()
        if (conv is None):
            return None
        messages = conv.messages
        return messages

    async def send_message(self, user: models.User, conversation_id: int, message: schemas.GetMessage):
        messages = await(self.get_conversation(user, conversation_id))

        print(messages)

        chat = []
        for mes in messages:
            chat.append({
                "role": mes.role,
                "content": mes.content
            })
        chat.append({
            "role": "user",
            "content": message.content
        })

        # print(chat)
        response = await self.send_by_chat_wraper(chat)

        user_message = models.Message(conversation_id=conversation_id, role="user", content=message.content)
        response_message = models.Message(conversation_id=conversation_id, role="assistant", content=response)
        self.db.add(user_message)
        self.db.add(response_message)
        self.db.commit()

        messages = await self.get_conversation(user, conversation_id)
        return messages

    async def get_short_hint(self, problem: schemas.ProblemData, min_words: int = 10, max_words: int = 40) -> str:
        parts = []
        if problem.title:
            parts.append(f"Название: {problem.title}")
        if problem.statement:
            parts.append(" ".join(problem.statement[:8]))
        elif problem.raw_text:
            parts.append((problem.raw_text[:2000] if len(problem.raw_text) > 2000 else problem.raw_text))
        prompt = (
            "Дай, пожалуйста, короткую подсказку для этой задачи на русском языке.\n\n"
            "Требования к подсказке:\n"
            "- Около 10–40 слов (лучше ближе к 25).\n"
            "- НИКАКОГО кода, псевдокода или формул — только ориентир и ключевая идея.\n"
            "- Одна-две связные фразы, без списков и маркеров.\n\n"
            "Задача:\n"
            f"{chr(10).join(parts)}\n\n"
            "Верни ТОЛЬКО саму подсказку (текст), ничего лишнего."
        )

        messages = [
            {"role": "system",
             "content": "Ты — опытный преподаватель по алгоритмам и структурам данных. Отвечай коротко и по сути."},
            {"role": "user", "content": prompt}
        ]
        try:
            resp = await self.send_by_chat_wraper(messages, stream=False)
        except Exception:
            return ""
        if not isinstance(resp, str):
            resp = str(resp)
        cleaned = resp.strip().strip('"\'')
        cleaned = " ".join(cleaned.split())

        words = cleaned.split()
        if len(words) == 0:
            return ""
        attempts = 0
        while len(words) > max_words and attempts < 2:
            attempts += 1
            shorten_prompt = (
                f"Сократи следующую подсказку до {min_words}–{max_words} слов, сохрани смысл, "
                "ничего не добавляй, НИКАКОГО кода. Верни ТОЛЬКО сокращённую подсказку.\n\n"
                f"Исходная подсказка:\n{cleaned}"
            )
            messages_shorten = [
                {"role": "system", "content": "Ты — ассистент сокращающий текст, сохраняя смысл и стиль."},
                {"role": "user", "content": shorten_prompt}
            ]
            try:
                resp2 = await self.send_by_chat_wraper(messages_shorten, stream=False)
            except Exception:
                break
            if not isinstance(resp2, str):
                resp2 = str(resp2)
            cleaned = resp2.strip().strip('"\'')
            cleaned = " ".join(cleaned.split())
            words = cleaned.split()
            if len(words) <= max_words:
                break
    
        if len(words) > max_words:
            cleaned = " ".join(words[:max_words]).rstrip(" ,.;:") + "..."
            cleaned = " ".join(cleaned.split())

        return cleaned
