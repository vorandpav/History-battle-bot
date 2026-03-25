from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Mock Voice Service")


class VoiceRequest(BaseModel):
    persona: str
    text: str


@app.post("/synthesize")
def synthesize(payload: VoiceRequest) -> dict:
    persona_title = "Сталин" if payload.persona.lower() == "stalin" else "Черчилль"
    return {
        "persona": payload.persona,
        "voice_text": f"[{persona_title}] {payload.text}",
        "format": "mock-text",
    }

