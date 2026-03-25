from dataclasses import dataclass

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot_service.clients import ServiceClientError, ServiceClients

router = Router()


@dataclass
class ChatState:
    mode: str = "detailed"
    level: str = "easy"
    battle_enabled: bool = False


CHAT_STATES: dict[int, ChatState] = {}


def _get_state(chat_id: int, default_mode: str, default_level: str) -> ChatState:
    if chat_id not in CHAT_STATES:
        CHAT_STATES[chat_id] = ChatState(mode=default_mode, level=default_level)
    return CHAT_STATES[chat_id]


def _format_followups(items: list[str]) -> str:
    lines = ["Что спросить дальше:"]
    for idx, item in enumerate(items, start=1):
        lines.append(f"{idx}. {item}")
    return "\n".join(lines)


def _format_battle(turns: list[dict[str, str]]) -> str:
    lines = ["Исторический батл:"]
    for turn in turns:
        persona = turn.get("persona", "Персона")
        replica = turn.get("replica", "")
        lines.append(f"- {persona}: {replica}")
    return "\n".join(lines)


@router.message(Command("start"))
async def cmd_start(message: Message, clients: ServiceClients, default_mode: str, default_level: str) -> None:
    state = _get_state(message.chat.id, default_mode, default_level)
    text = (
        "Привет! Я помогу разобраться в ВМВ через формат исторического батла.\n"
        f"Текущие настройки: mode={state.mode}, level={state.level}, battle={state.battle_enabled}.\n"
        "Команды: /battle_on, /battle_off, /mode_detailed, /mode_short, /level_easy, /level_academic, /level_exam"
    )
    await message.answer(text)


@router.message(Command("battle_on"))
async def cmd_battle_on(message: Message, default_mode: str, default_level: str) -> None:
    state = _get_state(message.chat.id, default_mode, default_level)
    state.battle_enabled = True
    await message.answer("Режим батла включен.")


@router.message(Command("battle_off"))
async def cmd_battle_off(message: Message, default_mode: str, default_level: str) -> None:
    state = _get_state(message.chat.id, default_mode, default_level)
    state.battle_enabled = False
    await message.answer("Режим батла выключен.")


@router.message(Command("mode_detailed"))
async def cmd_mode_detailed(message: Message, default_mode: str, default_level: str) -> None:
    state = _get_state(message.chat.id, default_mode, default_level)
    state.mode = "detailed"
    await message.answer("Режим ответа: подробно.")


@router.message(Command("mode_short"))
async def cmd_mode_short(message: Message, default_mode: str, default_level: str) -> None:
    state = _get_state(message.chat.id, default_mode, default_level)
    state.mode = "short"
    await message.answer("Режим ответа: коротко.")


@router.message(Command("level_easy"))
async def cmd_level_easy(message: Message, default_mode: str, default_level: str) -> None:
    state = _get_state(message.chat.id, default_mode, default_level)
    state.level = "easy"
    await message.answer("Уровень объяснения: проще.")


@router.message(Command("level_academic"))
async def cmd_level_academic(message: Message, default_mode: str, default_level: str) -> None:
    state = _get_state(message.chat.id, default_mode, default_level)
    state.level = "academic"
    await message.answer("Уровень объяснения: академично.")


@router.message(Command("level_exam"))
async def cmd_level_exam(message: Message, default_mode: str, default_level: str) -> None:
    state = _get_state(message.chat.id, default_mode, default_level)
    state.level = "exam"
    await message.answer("Уровень объяснения: экзамен.")


@router.message(F.voice)
async def handle_voice(message: Message, clients: ServiceClients, default_mode: str, default_level: str) -> None:
    await message.answer("Эта функция сейчас недоступна")


@router.message(F.text)
async def handle_text(message: Message, clients: ServiceClients, default_mode: str, default_level: str) -> None:
    await _process_question(message, message.text.strip(), clients, default_mode, default_level)


async def _process_question(
        message: Message,
        question: str,
        clients: ServiceClients,
        default_mode: str,
        default_level: str,
) -> None:
    if not question:
        await message.answer("Задай вопрос про события Второй мировой войны.")
        return

    state = _get_state(message.chat.id, default_mode, default_level)
    await message.answer("Готовлю ответы Сталина и Черчилля...")

    try:
        answers = await clients.get_answers(question=question, mode=state.mode, level=state.level)
        followups = await clients.get_followups(question=question, mode=state.mode, level=state.level)

        stalin_text = answers["answers"]["stalin"]
        churchill_text = answers["answers"]["churchill"]

        stalin_voice = await clients.synthesize_voice(persona="stalin", text=stalin_text)
        churchill_voice = await clients.synthesize_voice(persona="churchill", text=churchill_text)

        await message.answer(f"🎙 Сталин (mock voice): {stalin_voice['voice_text']}")
        await message.answer(f"🎙 Черчилль (mock voice): {churchill_voice['voice_text']}")

        followup_text = _format_followups(followups.get("followups", []))
        await message.answer(followup_text)

        if state.battle_enabled:
            battle = await clients.get_battle(question=question, mode=state.mode, level=state.level)
            battle_text = _format_battle(battle.get("turns", []))
            await message.answer(battle_text)
    except ServiceClientError:
        await message.answer("Не удалось получить ответ от микросервисов. Проверь, что mock API запущены.")
