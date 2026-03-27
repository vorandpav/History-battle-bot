import os
from dataclasses import dataclass
from typing import cast

from dotenv import load_dotenv

from bot_service.domain_types import LEVEL_VALUES, MODE_VALUES, Level, Mode


@dataclass(frozen=True)
class Settings:
    bot_token: str
    answer_service_url: str
    voice_service_url: str
    battle_service_url: str
    default_mode: Mode
    default_level: Level


def load_settings() -> Settings:
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN is required")

    default_mode_raw = os.getenv("DEFAULT_MODE", "short").strip().lower()
    if default_mode_raw not in MODE_VALUES:
        raise ValueError(f"DEFAULT_MODE must be one of: {', '.join(MODE_VALUES)}")

    default_level_raw = os.getenv("DEFAULT_LEVEL", "easy").strip().lower()
    if default_level_raw not in LEVEL_VALUES:
        raise ValueError(f"DEFAULT_LEVEL must be one of: {', '.join(LEVEL_VALUES)}")

    return Settings(
        bot_token=bot_token,
        answer_service_url=os.getenv("ANSWER_SERVICE_URL", "http://127.0.0.1:8001").rstrip("/"),
        voice_service_url=os.getenv("VOICE_SERVICE_URL", "http://127.0.0.1:8002").rstrip("/"),
        battle_service_url=os.getenv("BATTLE_SERVICE_URL", "http://127.0.0.1:8003").rstrip("/"),
        default_mode=cast(Mode, default_mode_raw),
        default_level=cast(Level, default_level_raw),
    )
