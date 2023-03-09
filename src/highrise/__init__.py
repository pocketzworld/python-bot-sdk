"""The slides bot."""
from __future__ import annotations

from asyncio import Queue, TaskGroup, sleep
from itertools import count
from typing import Any, Callable, Literal

from aiohttp import ClientWebSocketResponse

from .models import SessionMetadata


class BaseBot:
    """A base class for Highrise bots.
    Bots join a room and interact with everything in it.

    Subclass this class and implement the handlers you want to use.

    The `self.highrise` attribute can be used to make requests.
    """

    highrise: Highrise

    async def on_start(self, session_metadata: SessionMetadata) -> None:
        """On a connection to the room being established."""
        pass

    async def on_chat(self, user_id: str, username: str, message: str) -> None:
        """On a received room-wide chat."""
        pass

    async def on_whisper(self, user_id: str, username: str, message: str) -> None:
        """On a received room whisper."""
        pass

    async def on_user_join(self, user_id: str, username: str) -> None:
        """On a user joining the room."""
        pass

    async def on_tip(
        self,
        sender_id: str,
        sender_username: str,
        receiver_id: str,
        receiver_username: str,
        tip_type: str,
        tip_amount: int,
    ) -> None:
        """On a tip received in the room."""
        pass


class Highrise:
    ws: ClientWebSocketResponse
    tg: TaskGroup
    _req_id = count()
    _req_id_registry: dict[int, Queue[Any]] = {}

    async def chat(self, message: str) -> None:
        """Broadcast a room-wide chat message."""
        await self.ws.send_json({"_type": "ChatRequest", "message": message})

    async def send_whisper(self, user_id: str, message: str) -> None:
        await self.ws.send_json(
            {"_type": "ChatRequest", "message": message, "whisper_target_id": user_id}
        )

    async def send_emote(
        self, emote_id: str, target_user_id: str | None = None
    ) -> None:
        payload = {"_type": "EmoteRequest", "emote_id": emote_id}
        if target_user_id is not None:
            payload["target_user_id"] = target_user_id
        await self.ws.send_json(payload)

    async def set_indicator(self, icon: str | None) -> None:
        payload = {"_type": "IndicatorRequest", "icon": icon}
        await self.ws.send_json(payload)

    async def walk_to(
        self,
        dest: tuple[float, float, float],
        facing: Literal["FrontRight", "FrontLeft", "BackRight", "BackLeft"],
    ) -> None:
        await self.ws.send_json(
            {"_type": "FloorHitRequest", "destination": dest, "facing": facing}
        )

    async def teleport(self, user_id: str, dest: tuple[float, float, float]) -> None:
        await self.ws.send_json(
            {"_type": "TeleportRequest", "user_id": user_id, "destination": dest}
        )

    async def get_room_users(
        self,
    ) -> list[tuple[dict[str, Any], tuple[float, float, float]]]:
        req_id = next(self._req_id)
        self._req_id_registry[req_id] = (q := Queue[Any](maxsize=1))
        await self.ws.send_json({"_type": "GetRoomUsersRequest", "rid": req_id})
        return await q.get()

    def call_in(self, callback: Callable, delay: float) -> None:
        self.tg.create_task(self._delayed_callback(callback, delay))

    @staticmethod
    async def _delayed_callback(callback: Callable, delay: float) -> None:
        await sleep(delay)
        await callback()
