from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Mock Battle Service")

HistoryItemType = Literal["question", "stalin", "churchill"]
ModeType = Literal["short", "detailed"]
LevelType = Literal["easy", "academic", "exam"]


class HistoryItem(BaseModel):
    type: HistoryItemType
    text: str


class BattleRequest(BaseModel):
    question: str
    history: list[HistoryItem] = Field(default_factory=list)
    mode: ModeType
    level: LevelType


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
        "turns": turns,
    }
