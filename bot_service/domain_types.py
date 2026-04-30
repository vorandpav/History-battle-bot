from typing import Literal

Mode = Literal["short", "detailed"]
Level = Literal["easy", "academic", "exam"]
Persona = Literal["battle", "both", "stalin", "churchill"]
PersonaAnswer = Literal["stalin", "churchill"]
HistoryItemType = Literal["question", "stalin", "churchill"]

MODE_VALUES: tuple[Mode, ...] = ("short", "detailed")
LEVEL_VALUES: tuple[Level, ...] = ("easy", "academic", "exam")
PERSONA_VALUES: tuple[Persona, ...] = ("battle", "both", "stalin", "churchill")
PERSONA_ANSWER_VALUES: tuple[PersonaAnswer, ...] = ("stalin", "churchill")
