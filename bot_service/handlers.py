from typing import TypeVar
import os

from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, ChatMemberUpdated, Message, FSInputFile

from bot_service.clients import ServiceClientError, ServiceClients
from bot_service.domain_types import (
    LEVEL_VALUES,
    MODE_VALUES,
    PERSONA_VALUES,
    Level,
    Mode,
    Persona,
    PersonaAnswer,
)
from bot_service.keyboards import (
    BUTTON_BEGIN,
    BUTTON_SETTINGS,
    BUTTON_SUGGEST,
    main_keyboard,
    settings_keyboard,
    start_keyboard,
    suggestions_keyboard,
)
from bot_service.state import (
    ChatState,
    add_history_item,
    clear_state,
    get_state,
    history_as_payload,
    set_last_suggestions,
    update_settings,
)
from bot_service.texts import settings_text, welcome_text

router = Router()

PERSONA_ORDER = PERSONA_VALUES
MODE_ORDER = MODE_VALUES
LEVEL_ORDER = LEVEL_VALUES

T = TypeVar("T", bound=str)


def _cycle_value(current: T, values: tuple[T, ...]) -> T:
    idx = values.index(current)
    return values[(idx + 1) % len(values)]


@router.message(F.text.startswith("/start"))
async def cmd_start(message: Message) -> None:
    clear_state(message.chat.id)
    await message.answer(
        "Нажми кнопку 'Начать', чтобы открыть интерфейс бота.",
        reply_markup=start_keyboard(),
    )


@router.message(F.text == "/reset")
async def cmd_reset(message: Message) -> None:
    clear_state(message.chat.id)
    await message.answer("История чата очищена.", reply_markup=start_keyboard())


@router.my_chat_member()
async def on_my_chat_member(update: ChatMemberUpdated) -> None:
    if update.new_chat_member.status in {"kicked", "left"}:
        clear_state(update.chat.id)


@router.message(F.text == BUTTON_BEGIN)
async def start_flow(message: Message, default_mode: Mode, default_level: Level) -> None:
    state = get_state(message.chat.id, default_mode, default_level)
    await message.answer(welcome_text(state), reply_markup=main_keyboard())


@router.message(F.text == BUTTON_SETTINGS)
async def open_settings(message: Message, default_mode: Mode, default_level: Level) -> None:
    state = get_state(message.chat.id, default_mode, default_level)
    await message.answer(settings_text(state), reply_markup=settings_keyboard(state))


@router.callback_query(F.data == "settings:persona")
async def rotate_persona(callback: CallbackQuery, default_mode: Mode, default_level: Level) -> None:
    if not callback.message:
        await callback.answer()
        return

    state = get_state(callback.message.chat.id, default_mode, default_level)
    state.persona = _cycle_value(state.persona, PERSONA_ORDER)
    update_settings(callback.message.chat.id, state)
    await callback.message.edit_text(settings_text(state), reply_markup=settings_keyboard(state))
    await callback.answer("Персона обновлена")


@router.callback_query(F.data == "settings:mode")
async def rotate_mode(callback: CallbackQuery, default_mode: Mode, default_level: Level) -> None:
    if not callback.message:
        await callback.answer()
        return

    state = get_state(callback.message.chat.id, default_mode, default_level)
    state.mode = _cycle_value(state.mode, MODE_ORDER)
    update_settings(callback.message.chat.id, state)
    await callback.message.edit_text(settings_text(state), reply_markup=settings_keyboard(state))
    await callback.answer("Режим обновлен")


@router.callback_query(F.data == "settings:level")
async def rotate_level(callback: CallbackQuery, default_mode: Mode, default_level: Level) -> None:
    if not callback.message:
        await callback.answer()
        return

    state = get_state(callback.message.chat.id, default_mode, default_level)
    state.level = _cycle_value(state.level, LEVEL_ORDER)
    update_settings(callback.message.chat.id, state)
    await callback.message.edit_text(settings_text(state), reply_markup=settings_keyboard(state))
    await callback.answer("Уровень обновлен")


@router.message(F.text == BUTTON_SUGGEST)
async def suggest_questions(
        message: Message,
        clients: ServiceClients,
        default_mode: Mode,
        default_level: Level,
) -> None:
    state = get_state(message.chat.id, default_mode, default_level)

    history_payload = history_as_payload(state)

    try:
        response = await clients.get_suggestions(
            history=history_payload,
            mode=state.mode,
            level=state.level,
            persona=state.persona
        )
    except ServiceClientError:
        await message.answer("Сервис предложений недоступен.")
        return

    suggestions = response.get("suggestions", [])
    if not suggestions:
        await message.answer("Сейчас не удалось подобрать вопросы. Попробуй позже.")
        return

    set_last_suggestions(message.chat.id, state, suggestions)
    await message.answer("Выбери один из предложенных вопросов:", reply_markup=suggestions_keyboard(suggestions))


@router.callback_query(F.data.startswith("ask:"))
async def ask_from_suggestion(
        callback: CallbackQuery,
        clients: ServiceClients,
        default_mode: Mode,
        default_level: Level,
) -> None:
    if not callback.message:
        await callback.answer()
        return

    state = get_state(callback.message.chat.id, default_mode, default_level)
    idx = int(callback.data.split(":", 1)[1])
    if idx < 0 or idx >= len(state.last_suggestions):
        await callback.answer("Эта подсказка уже устарела", show_alert=True)
        return

    question = state.last_suggestions[idx]

    await callback.answer()
    await _send_suggestion_question(callback.message, question)
    await _process_question(callback.message, question, clients, default_mode, default_level)


@router.message(F.voice)
async def handle_voice(message: Message) -> None:
    await message.answer("Голос пока в разработке. Отправь вопрос текстом.")


@router.message(F.text)
async def handle_text(
        message: Message,
        clients: ServiceClients,
        default_mode: Mode,
        default_level: Level,
) -> None:
    text = message.text.strip()
    if text in {BUTTON_BEGIN, BUTTON_SUGGEST, BUTTON_SETTINGS, "/start"}:
        return
    await _process_question(message, text, clients, default_mode, default_level)


async def _process_question(
        message: Message,
        question: str,
        clients: ServiceClients,
        default_mode: Mode,
        default_level: Level,
) -> None:
    if not question:
        await message.answer("Задай вопрос по теме Второй мировой войны.")
        return

    state = get_state(message.chat.id, default_mode, default_level)
    add_history_item(message.chat.id, state, item_type="question", text=question)

    history_payload = history_as_payload(state)

    if state.persona == "both":
        waiting_msg = await message.answer("⚔️ Начинаем исторические дебаты...")
        try:
            response = await clients.get_battle(
                question=question,
                history=history_payload,
                mode=state.mode,
                level=state.level,
            )
            turns = response.get("turns", [])

            for turn in turns:
                speaker_id = "stalin" if turn["persona"] == "Сталин" else "churchill"
                await _send_persona_answer(message, clients, state, speaker_id, turn["replica"], waiting_msg)

        except ServiceClientError:
            await message.answer("Не удалось получить дебаты от сервиса баттла.")

        return

    try:
        waiting_msg = await message.answer("Генерирую ответ ⏳")
        response = await clients.get_answer(
            question=question,
            history=history_payload,
            mode=state.mode,
            level=state.level,
            persona=state.persona,
        )
        answer_text = response.get("answer", f"Ответ {state.persona} недоступен")
        await _send_persona_answer(message, clients, state, state.persona, answer_text, waiting_msg)
    except ServiceClientError:
        await message.answer("Не удалось получить ответ от микросервисов.")


async def _send_suggestion_question(
        message: Message,
        question: str,
) -> None:
    await message.answer(question)


def _personas_for_answers(persona: Persona) -> list[PersonaAnswer]:
    if persona == "both":
        return ["stalin", "churchill"]
    return [persona]


def _persona_title(persona: PersonaAnswer) -> str:
    titles = {
        "stalin": "Иосиф Сталин 🎖",
        "churchill": "Уинстон Черчилль 🎩",
    }
    return titles[persona]


async def _send_persona_answer(
        message: Message,
        clients: ServiceClients,
        state: ChatState,
        persona: PersonaAnswer,
        answer_text: str,
        waiting_msg: Message | None,
) -> None:
    voice_bytes = None
    try:
        voice_bytes = await clients.synthesize_voice(
            persona=persona,
            text=answer_text,
        )
    except ServiceClientError:
        pass

    if waiting_msg is not None:
        try:
            await waiting_msg.delete()
        except:
            pass

    title = _persona_title(persona)
    photo_path = f"bot_service/avatars/{persona}.jpg"

    if os.path.exists(photo_path):
        await message.answer_photo(FSInputFile(photo_path), caption=title)
    else:
        await message.answer(title)

    if voice_bytes:
        await message.answer_voice(
            BufferedInputFile(voice_bytes, filename=f"{persona}.ogg")
        )
    else:
        await message.answer(answer_text)

    add_history_item(message.chat.id, state, item_type=persona, text=answer_text)
