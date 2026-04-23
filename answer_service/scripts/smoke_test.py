import asyncio

import httpx


async def main() -> None:
    answer_url = "http://127.0.0.1:8001/answer"
    followups_url = "http://127.0.0.1:8001/followups"
    voice_url = "http://127.0.0.1:8002/synthesize"
    battle_url = "http://127.0.0.1:8003/battle"

    payload = {
        "question": "Почему Сталинград считают переломом войны?",
        "mode": "detailed",
        "level": "easy",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        answer_resp = await client.post(answer_url, json=payload)
        followups_resp = await client.post(followups_url, json=payload)
        battle_resp = await client.post(battle_url, json=payload)

        answer_resp.raise_for_status()
        followups_resp.raise_for_status()
        battle_resp.raise_for_status()

        answer_json = answer_resp.json()
        stalin_text = answer_json["answers"]["stalin"]

        voice_resp = await client.post(
            voice_url,
            json={"persona": "stalin", "text": stalin_text},
        )
        voice_resp.raise_for_status()

    print("OK: answer service")
    print("OK: followups service")
    print("OK: battle service")
    print("OK: voice service")


if __name__ == "__main__":
    asyncio.run(main())

