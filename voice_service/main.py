from pathlib import Path
import uuid
import threading

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .tts_engine import VoiceManager

app = FastAPI(title="TTS Service")

voice_service = VoiceManager()

tts_lock = threading.Lock()


class TTSRequest(BaseModel):
    persona: str
    text: str


@app.post("/synthesize")
def synthesize(payload: TTSRequest, background_tasks: BackgroundTasks):
    print(f"[TTS] persona={payload.persona}, text_len={len(payload.text)}")

    output_path = None

    try:
        output_path = Path(f"temp_{uuid.uuid4().hex}.wav")
        with tts_lock:
            print(f"Генерируем голос для {payload.persona}...")
            voice_service.generate_voice(
                text=payload.text,
                speaker_key=payload.persona.lower(),
                output_path=str(output_path)
            )
        print(f"Успешно сгенерирован файл: {output_path}")

    except ValueError as e:
        print(f"Ошибка значения: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        print(f"Ошибка генерации: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    if output_path and output_path.exists():
        background_tasks.add_task(safe_delete, output_path)
        return FileResponse(
            path=output_path,
            media_type="audio/wav",
            filename="voice.wav",
        )
    else:
        raise HTTPException(status_code=500, detail="Файл не был создан")


def safe_delete(path: Path):
    try:
        if path.exists():
            path.unlink()
    except Exception as e:
        print(f"[WARN] Failed to delete file: {e}")
