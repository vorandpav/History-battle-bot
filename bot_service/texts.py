from bot_service.domain_types import Level, Mode, Persona
from bot_service.state import ChatState


def persona_label(persona: Persona) -> str:
    mapping = {
        "stalin": "Сталин",
        "churchill": "Черчилль",
        "both": "Оба",
        "battle": "Батл",
    }
    return mapping[persona]


def mode_label(mode: Mode) -> str:
    mapping = {
        "short": "Коротко",
        "detailed": "Подробно",
    }
    return mapping[mode]


def level_label(level: Level) -> str:
    mapping = {
        "easy": "Проще",
        "academic": "Академично",
        "exam": "Экзамен",
    }
    return mapping[level]


def product_description() -> str:
    return (
        "Исторический батл - бот по истории ВМВ.\n"
        "Ты задаешь вопрос, а бот отвечает в выбранной персоне: Сталин, Черчилль, отвечают оба или вступают в батл.\n"
        "Можно запросить готовые вопросы и продолжить тему одним нажатием."
    )


def settings_text(state: ChatState) -> str:
    return (
        "Текущие настройки:\n"
        f"- Персона: {persona_label(state.persona)}\n"
        f"- Режим: {mode_label(state.mode)}\n"
        f"- Уровень: {level_label(state.level)}"
    )


def welcome_text(state: ChatState) -> str:
    return f"{product_description()}\n\n{settings_text(state)}"
