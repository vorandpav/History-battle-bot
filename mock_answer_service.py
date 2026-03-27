from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Mock Answer Service")

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
    "Почему открытие второго фронта произошло в 1944 году?",
    "Как союзники координировали действия на разных фронтах?",
    "Какие стратегические ошибки допустила Германия в ВМВ?",
]


@app.post("/answer")
def answer(payload: AnswerRequest) -> dict:
    print(f"[mock_answer_service:/answer] history={payload.history}")
    q = payload.question.lower()

    if "ленд" in q:
        stalin = (
            "Тезис: ленд-лиз усилил промышленную и транспортную устойчивость фронта. "
            "Причины: поставки грузовиков, связи и сырья закрывали узкие места снабжения. "
            "Контекст: ключевую нагрузку несла советская индустрия, но внешняя помощь ускоряла операции. "
            "Вывод: вклад был важным множителем, особенно в логистике."
        )
        churchill = (
            "Thesis: lend-lease helped synchronize coalition warfare at scale. "
            "Reasons: maritime logistics and equipment transfers reduced operational delays. "
            "Context: combined pressure across theaters constrained Axis strategy. "
            "Conclusion: aid did not replace Soviet effort, but improved tempo and resilience."
        )
    elif "сталинград" in q:
        stalin = (
            "Тезис: Сталинград стал переломом войны на Восточном фронте. "
            "Причины: истощение вермахта, удержание города и окружение 6-й армии. "
            "Контекст: борьба за инициативу в 1942-1943 годах. "
            "Вывод: после битвы СССР перешел к стратегическому наступлению."
        )
        churchill = (
            "Thesis: Stalingrad was the strategic rupture in Germany's eastern campaign. "
            "Reasons: overextended lines and catastrophic losses in a key urban battle. "
            "Context: Allied coordination increased pressure in multiple directions. "
            "Conclusion: the Axis lost momentum that it never fully restored."
        )
    else:
        stalin = (
            "Тезис: ключ к пониманию темы ВМВ - связь решений с ресурсами и временем. "
            "Причины: экономика, логистика и коалиции определяли исход операций. "
            "Контекст: фронты влияли друг на друга, а не существовали изолированно. "
            "Вывод: анализируйте вопрос через причины, контекст и последствия."
        )
        churchill = (
            "Thesis: WWII outcomes emerged from strategy, industry, and coalition discipline. "
            "Reasons: command decisions only worked when supply and diplomacy aligned. "
            "Context: theaters were interconnected through shipping, timing, and political commitments. "
            "Conclusion: compare alternatives and constraints, not only final results."
        )

    if payload.persona == "stalin":
        return {
            "answer": stalin,
        }
    else:
        return {
            "answer": churchill,
        }


@app.post("/suggestions")
def suggestions(payload: SuggestionsRequest) -> dict:
    print(f"[mock_answer_service:/suggestions] history={payload.history}")
    if not payload.history:
        return {
            "suggestions": DEFAULT_SUGGESTIONS,
        }

    last_question = payload.history[-1].text.lower()

    if "сталинград" in last_question:
        items = [
            "Какие решения командования СССР обеспечили успех операции 'Уран'?",
            "Почему городские бои в Сталинграде оказались настолько изнурительными?",
            "Как победа под Сталинградом повлияла на стратегию союзников?",
            "Какие риски были у СССР, если бы операция окружения провалилась?",
            "Как Сталинград связан с последующим сражением на Курской дуге?",
        ]
    elif "ленд" in last_question:
        items = [
            "Какие категории поставок ленд-лиза были наиболее критичны для фронта?",
            "Как ленд-лиз влиял на скорость наступательных операций СССР?",
            "Какие ограничения и политические условия сопровождали помощь союзников?",
            "Что в советской экономике ленд-лиз не мог заменить?",
            "Как по-разному оценивали вклад ленд-лиза в СССР и Великобритании?",
        ]
    else:
        items = [
            "Какие причины события можно выделить на уровне стратегии и ресурсов?",
            "Как тема связана с действиями союзников на других фронтах?",
            "Какие решения были альтернативными и к чему они могли привести?",
            "Какие последствия стали заметны через 6-12 месяцев после события?",
            "Какие источники помогут проверить разные интерпретации?",
        ]

    return {
        "suggestions": items,
    }
