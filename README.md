# Historical Battle Bot MVP

MVP for a history Telegram bot with one real microservice (`bot_service`) and three mock API microservices (`answer`, `voice`, `battle`).

## Implemented

- Telegram bot on `aiogram`
- Input: text and voice (voice is accepted, transcription is mocked)
- Output:
  - two persona responses (Stalin and Churchill) through mock voice pipeline
  - follow-up questions (3-5)
  - optional short battle mode (2-4 turns)
- Separate API emulator processes with hardcoded responses

## Project structure

- `bot_service/app.py` - bot entrypoint
- `bot_service/handlers.py` - Telegram handlers and flow orchestration
- `bot_service/clients.py` - async HTTP clients for external microservices
- `bot_service/config.py` - environment config
- `mock_answer_service.py` - hardcoded answer/followups API
- `mock_voice_service.py` - hardcoded synth API
- `mock_battle_service.py` - hardcoded battle API
- `scripts/smoke_test.py` - tiny local API smoke test

## Quick start

1) Create and activate virtual environment
2) Install dependencies
3) Copy `.env.example` to `.env` and fill `BOT_TOKEN`
4) Run mock services (3 separate terminals)
5) Run bot service

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Terminal 1:
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn mock_answer_service:app --host 127.0.0.1 --port 8001
```

Terminal 2:
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn mock_voice_service:app --host 127.0.0.1 --port 8002
```

Terminal 3:
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn mock_battle_service:app --host 127.0.0.1 --port 8003
```

Terminal 4:
```powershell
.\.venv\Scripts\Activate.ps1
python -m bot_service.app
```

## Local API smoke test

Run after mock services are started:

```powershell
.\.venv\Scripts\Activate.ps1
python scripts\smoke_test.py
```

