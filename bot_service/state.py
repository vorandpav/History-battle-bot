from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from bot_service.domain_types import HistoryItemType, Level, Mode, Persona

DATA_DIR = Path("data") / "chat_state"


@dataclass
class HistoryItem:
    type: HistoryItemType
    text: str


@dataclass
class ChatState:
    mode: Mode
    level: Level
    persona: Persona
    history: list[HistoryItem] = field(default_factory=list)
    last_suggestions: list[str] = field(default_factory=list)


CHAT_STATES: dict[int, ChatState] = {}


def _state_file(chat_id: int) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / f"{chat_id}.json"


def _load_state_from_disk(chat_id: int, default_mode: Mode, default_level: Level) -> ChatState:
    file_path = _state_file(chat_id)
    if not file_path.exists():
        return ChatState(mode=default_mode, level=default_level, persona="both")

    raw = json.loads(file_path.read_text(encoding="utf-8"))
    history_items = [HistoryItem(type=item["type"], text=item["text"]) for item in raw["history"]]

    return ChatState(
        mode=raw["mode"],
        level=raw["level"],
        persona=raw["persona"],
        history=history_items,
        last_suggestions=raw.get("last_suggestions", []),
    )


def save_state(chat_id: int, state: ChatState) -> None:
    file_path = _state_file(chat_id)
    payload = {
        "mode": state.mode,
        "level": state.level,
        "persona": state.persona,
        "history": [asdict(item) for item in state.history],
        "last_suggestions": state.last_suggestions,
    }
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def get_state(chat_id: int, default_mode: Mode, default_level: Level) -> ChatState:
    if chat_id not in CHAT_STATES:
        CHAT_STATES[chat_id] = _load_state_from_disk(chat_id, default_mode, default_level)
    return CHAT_STATES[chat_id]


def clear_state(chat_id: int) -> None:
    CHAT_STATES.pop(chat_id, None)
    file_path = _state_file(chat_id)
    if file_path.exists():
        file_path.unlink()


def add_history_item(
        chat_id: int,
        state: ChatState,
        item_type: HistoryItemType,
        text: str,
        limit: int = 30,
) -> None:
    state.history.append(HistoryItem(type=item_type, text=text))
    if len(state.history) > limit:
        state.history[:] = state.history[-limit:]
    save_state(chat_id, state)


def set_last_suggestions(chat_id: int, state: ChatState, suggestions: list[str]) -> None:
    state.last_suggestions = suggestions
    save_state(chat_id, state)


def update_settings(chat_id: int, state: ChatState) -> None:
    save_state(chat_id, state)


def history_as_payload(state: ChatState) -> list[dict[str, str]]:
    return [asdict(item) for item in state.history]
