# Quick Start — Короткие команды запуска

Открой PowerShell в папке проекта и копируй нужную команду.

## Запуск каждого сервиса отдельно

### Answer Service (порт 8001)

```powershell
python -m uvicorn answer_service.main:app --host 127.0.0.1 --port 8001
```

### Voice Service (порт 8002)

```powershell
python -m uvicorn voice_service.main:app --host 127.0.0.1 --port 8002
```

### Battle Service (порт 8003)

```powershell
python -m uvicorn mock_battle_service:app --host 127.0.0.1 --port 8003
```

### Bot Service (Telegram polling)

```powershell
python -m bot_service.app
```
