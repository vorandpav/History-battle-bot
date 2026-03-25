import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    answer_service_url: str
    voice_service_url: str
    battle_service_url: str
    default_mode: str
    default_level: str


def load_settings() -> Settings:
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN is required")

    return Settings(
        bot_token=bot_token,
        answer_service_url=os.getenv("ANSWER_SERVICE_URL", "http://127.0.0.1:8001").rstrip("/"),
        voice_service_url=os.getenv("VOICE_SERVICE_URL", "http://127.0.0.1:8002").rstrip("/"),
        battle_service_url=os.getenv("BATTLE_SERVICE_URL", "http://127.0.0.1:8003").rstrip("/"),
        default_mode=os.getenv("DEFAULT_MODE", "short").strip().lower(),
        default_level=os.getenv("DEFAULT_LEVEL", "easy").strip().lower(),
    )
