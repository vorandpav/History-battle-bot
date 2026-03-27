from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Mock TTS Service")

AUDIO_FILE = Path(__file__).with_name("mock_audio.ogg")


class TTSRequest(BaseModel):
    persona: str
    text: str


@app.post("/synthesize")
def synthesize(payload: TTSRequest) -> FileResponse:
    print(f"[mock_tts_service:/synthesize] persona={payload.persona} text_len={len(payload.text)}")

    if not AUDIO_FILE.exists():
        raise HTTPException(status_code=500, detail="mock_audio.ogg not found")

    return FileResponse(
        path=AUDIO_FILE,
        media_type="audio/ogg",
        filename="voice.ogg",
    )
