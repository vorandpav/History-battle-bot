from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Mock Answer Service")


class AnswerRequest(BaseModel):
    question: str
    mode: str
    level: str


@app.post("/answer")
def answer(payload: AnswerRequest) -> dict:
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

    return {
        "question": payload.question,
        "mode": payload.mode,
        "level": payload.level,
        "answers": {"stalin": stalin, "churchill": churchill},
    }


@app.post("/followups")
def followups(payload: AnswerRequest) -> dict:
    return {
        "question": payload.question,
        "followups": [
            "Какие факторы были решающими в 1942-1943 годах?",
            "Как менялась роль логистики по мере хода войны?",
            "Какие решения союзников усилили эффект друг друга?",
            "Что было бы иначе при задержке второго фронта?",
            "Какие источники стоит сравнить для проверки версии событий?",
        ],
    }
