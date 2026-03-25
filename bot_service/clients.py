from typing import Any

import httpx


class ServiceClientError(RuntimeError):
    pass


class ServiceClients:
    def __init__(
        self,
        answer_service_url: str,
        voice_service_url: str,
        battle_service_url: str,
        timeout_seconds: float = 20.0,
    ) -> None:
        self._answer_base = answer_service_url
        self._voice_base = voice_service_url
        self._battle_base = battle_service_url
        self._client = httpx.AsyncClient(timeout=timeout_seconds)

    async def close(self) -> None:
        await self._client.aclose()

    async def get_answers(self, question: str, mode: str, level: str) -> dict[str, Any]:
        payload = {"question": question, "mode": mode, "level": level}
        return await self._post_json(f"{self._answer_base}/answer", payload)

    async def get_followups(self, question: str, mode: str, level: str) -> dict[str, Any]:
        payload = {"question": question, "mode": mode, "level": level}
        return await self._post_json(f"{self._answer_base}/followups", payload)

    async def synthesize_voice(self, persona: str, text: str) -> dict[str, Any]:
        payload = {"persona": persona, "text": text}
        return await self._post_json(f"{self._voice_base}/synthesize", payload)

    async def get_battle(self, question: str, mode: str, level: str) -> dict[str, Any]:
        payload = {"question": question, "mode": mode, "level": level}
        return await self._post_json(f"{self._battle_base}/battle", payload)

    async def _post_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            raise ServiceClientError(f"Service call failed: {url}") from exc

