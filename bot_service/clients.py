from typing import Any

import httpx

from bot_service.domain_types import Level, Mode, Persona, PersonaAnswer


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

    async def get_answer(
            self,
            question: str,
            history: list[dict[str, str]],
            mode: Mode,
            level: Level,
            persona: PersonaAnswer,
    ) -> dict[str, Any]:
        payload = {
            "question": question,
            "history": history,
            "mode": mode,
            "level": level,
            "persona": persona,
        }
        return await self._post_json(f"{self._answer_base}/answer", payload)

    async def get_suggestions(
            self,
            history: list[dict[str, str]],
            mode: Mode,
            level: Level,
            persona: Persona,
    ) -> dict[str, Any]:
        payload = {
            "history": history,
            "mode": mode,
            "level": level,
            "persona": persona,
        }
        return await self._post_json(f"{self._answer_base}/suggestions", payload)

    async def synthesize_voice(
            self,
            persona: PersonaAnswer,
            text: str,
    ) -> bytes:
        payload = {"persona": persona, "text": text}
        return await self._post_bytes(f"{self._voice_base}/synthesize", payload)

    async def get_battle(
            self,
            question: str,
            history: list[dict[str, str]],
            mode: Mode,
            level: Level,
    ) -> dict[str, Any]:
        payload = {"question": question, "history": history, "mode": mode, "level": level}
        return await self._post_json(f"{self._answer_base}/battle", payload)

    async def _post_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            raise ServiceClientError(f"Service call failed: {url}") from exc

    async def _post_bytes(self, url: str, payload: dict[str, Any]) -> bytes:
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            return response.content
        except Exception as exc:
            raise ServiceClientError(f"Service call failed: {url}") from exc
