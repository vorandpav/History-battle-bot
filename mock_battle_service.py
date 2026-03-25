from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Mock Battle Service")


class BattleRequest(BaseModel):
    question: str
    mode: str
    level: str


@app.post("/battle")
def battle(payload: BattleRequest) -> dict:
    turns = [
        {
            "persona": "Сталин",
            "replica": "Главное - материальная устойчивость фронта и концентрация сил на решающем участке.",
        },
        {
            "persona": "Черчилль",
            "replica": "Согласен с важностью ресурсов, но коалиционная стратегия и морские коммуникации не менее критичны.",
        },
        {
            "persona": "Сталин",
            "replica": "Без своевременной логистики даже верные решения штаба теряют эффект.",
        },
        {
            "persona": "Черчилль",
            "replica": "Именно поэтому синхронизация фронтов и поставок определяет темп победы.",
        },
    ]

    return {
        "question": payload.question,
        "mode": payload.mode,
        "level": payload.level,
        "turns": turns,
    }

