from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from bot_service.state import ChatState
from bot_service.texts import level_label, mode_label, persona_label

BUTTON_BEGIN = "Начать"
BUTTON_SUGGEST = "Предложить вопросы"
BUTTON_SETTINGS = "Настройки"


def start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BUTTON_BEGIN)]],
        resize_keyboard=True,
    )


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTON_SUGGEST)],
            [KeyboardButton(text=BUTTON_SETTINGS)],
        ],
        resize_keyboard=True,
    )


def settings_keyboard(state: ChatState) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Персона: {persona_label(state.persona)}", callback_data="settings:persona")],
            [InlineKeyboardButton(text=f"Режим: {mode_label(state.mode)}", callback_data="settings:mode")],
            [InlineKeyboardButton(text=f"Уровень: {level_label(state.level)}", callback_data="settings:level")],
        ]
    )


def suggestions_keyboard(questions: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    for idx, question in enumerate(questions):
        button_text = question if len(question) <= 64 else f"{question[:61]}..."
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=f"ask:{idx}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
