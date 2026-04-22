import os
import json
from typing import Literal
from fastapi import FastAPI
from pydantic import BaseModel, Field
from mistralai.client import Mistral
from langchain_community.vectorstores import FAISS
from langchain_mistralai import MistralAIEmbeddings

from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="RAG Answer Service")

ModeType = Literal["short", "detailed"]
LevelType = Literal["easy", "academic", "exam"]
AnswerPersonaType = Literal["stalin", "churchill"]
SuggestionsPersonaType = Literal["stalin", "churchill", "both"]
HistoryItemType = Literal["question", "stalin", "churchill"]


class HistoryItem(BaseModel):
    type: HistoryItemType
    text: str


class AnswerRequest(BaseModel):
    question: str
    history: list[HistoryItem] = Field(default_factory=list)
    mode: ModeType
    level: LevelType
    persona: AnswerPersonaType


class SuggestionsRequest(BaseModel):
    history: list[HistoryItem] = Field(default_factory=list)
    mode: ModeType
    level: LevelType
    persona: SuggestionsPersonaType


DEFAULT_SUGGESTIONS = [
    "Почему Сталинград считают переломом войны?",
    "Какую роль сыграл ленд-лиз для СССР?",
]

mistral_client = None
vectorstore = None


@app.on_event("startup")
def startup_event():
    global mistral_client, vectorstore
    api_key = os.environ.get("MISTRAL_API_KEY")
    mistral_client = Mistral(api_key=api_key)

    print("Загрузка векторной базы FAISS...")
    try:
        embeddings = MistralAIEmbeddings(mistral_api_key=api_key)
        # allow_dangerous_deserialization=True нужно для FAISS в новых версиях
        vectorstore = FAISS.load_local("vector_db", embeddings, allow_dangerous_deserialization=True)
        print("База успешно загружена!")
    except Exception as e:
        print(f"ВНИМАНИЕ! База не загрузилась. Вы запускали build_index.py? Ошибка: {e}")


@app.post("/answer")
async def answer(payload: AnswerRequest) -> dict:
    global mistral_client, vectorstore

    persona_name = "Иосиф Сталин" if payload.persona == "stalin" else "Уинстон Черчилль"
    context_text = ""

    mode_instruction = "коротко и по делу" if payload.mode == "short" else "очень подробно и развернуто"
    level_instruction = {
        "easy": "простым и понятным языком для обывателя",
        "academic": "академическим, исторически точным языком с терминами",
        "exam": "структурированно, как для сдачи экзамена по истории"
    }.get(payload.level, "понятным языком")

    if vectorstore is not None:
        try:
            docs = vectorstore.similarity_search(
                payload.question,
                k=3,
                filter={"persona": payload.persona}
            )
            context_text = "\n\n---\n\n".join([d.page_content for d in docs])
            print(f"Найдено контекста: {len(context_text)} символов")
        except Exception as e:
            print(f"Ошибка поиска в FAISS: {e}")

    system_prompt = (
        f"Ты выступаешь от лица исторической личности: {persona_name}. "
        f"Отвечай в УНИКАЛЬНОМ СТИЛЕ этой исторической личности. Твой ответ должен быть в режиме: {mode_instruction}."
        f"Стиль изложения: {level_instruction}.\n\n"
        f"ОБЯЗАТЕЛЬНО используй следующие исторические документы для ответа. "
        f"Если в них нет прямого ответа, опирайся на исторические факты, но сохраняй образ.\n\n"
        f"ИСТОРИЧЕСКИЕ ДОКУМЕНТЫ (hrono.info):\n{context_text}\n\n"
        f"Не выделяй смысловые блоки, отвечай так, как будто ведешь один цельный рассказ. "
        f"СТРОГИЙ ЗАПРЕТ: НЕ используй сценические ремарки, RP-отыгрыши и НЕ описывай свои физические действия, "
        f"эмоции или мимику в скобках или звездочках (например, никаких [сердито смотрит] или *вздыхает*). "
        f"НЕ пиши свое имя, роли или теги спикера в начале ответа (никаких 'Сталин:', '[Stalin]:', 'Я:'). Начинай сразу с сути.\n\n"
    )

    messages = [{"role": "system", "content": system_prompt}]

    MAX_HISTORY = 8
    recent_history = payload.history[-MAX_HISTORY:] if len(payload.history) > MAX_HISTORY else payload.history

    for item in recent_history:
        role = "user" if item.type == "question" else "assistant"
        messages.append({"role": role, "content": item.text})

    messages.append({"role": "user", "content": payload.question})

    try:
        res = await mistral_client.chat.complete_async(
            model="mistral-small-latest",
            messages=messages,
            temperature=0.7
        )
        return {"answer": res.choices[0].message.content}
    except Exception as e:
        print(f"Mistral API Error: {e}")
        return {"answer": "Архивы сейчас недоступны. Ошибка связи."}


@app.post("/suggestions")
async def suggestions(payload: SuggestionsRequest) -> dict:
    global mistral_client

    persona_map = {
        "stalin": "Иосифу Сталину",
        "churchill": "Уинстону Черчиллю",
        "both": "Сталину и Черчиллю (сравнение их взглядов)"
    }
    target_persona = persona_map.get(payload.persona, "историческим лидерам")

    if not payload.history:
        history_text = "Диалог только начинается. Предложи 3 хороших стартовых вопроса."
    else:
        recent_history = payload.history[-4:]
        history_lines = [f"[{h.type}]: {h.text}" for h in recent_history]
        history_text = "Последние сообщения диалога:\n" + "\n".join(history_lines)

    system_prompt = (
        f"Ты — AI-ассистент. Твоя задача — придумать ровно 3 логичных и интересных вопроса, "
        f"которые пользователь может задать {target_persona} для продолжения интервью.\n\n"
        f"Уровень сложности вопросов: {payload.level}.\n\n"
        f"{history_text}\n\n"
        f"Верни ответ СТРОГО в формате JSON с ключом 'suggestions', содержащим массив строк.\n"
        f"Пример: {{\"suggestions\": [\"Вопрос 1?\", \"Вопрос 2?\", \"Вопрос 3?\"]}}"
    )

    try:
        res = await mistral_client.chat.complete_async(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": system_prompt}],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        parsed = json.loads(res.choices[0].message.content)
        suggests = parsed.get("suggestions", [])

        if isinstance(suggests, list) and len(suggests) > 0:
            return {"suggestions": suggests[:3]}
        else:
            return {"suggestions": DEFAULT_SUGGESTIONS}

    except Exception as e:
        print(f"Ошибка при генерации подсказок: {e}")
        return {"suggestions": DEFAULT_SUGGESTIONS}
