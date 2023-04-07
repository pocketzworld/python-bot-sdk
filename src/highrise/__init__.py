"""The Highrise bot SDK."""
from __future__ import annotations

from asyncio import Queue, TaskGroup, sleep
from itertools import count
from typing import TYPE_CHECKING, Any, Callable, Literal, Protocol, TypeVar, Union

from aiohttp import ClientWebSocketResponse
from cattrs.preconf.json import make_converter

from ._unions import configure_tagged_union
from .models import (
    AnchorPosition,
    ChangeRoomPrivilegeRequest,
    ChannelEvent,
    ChannelRequest,
    ChatEvent,
    ChatRequest,
    CurrencyItem,
    EmoteEvent,
    EmoteRequest,
    Error,
    FloorHitRequest,
    GetRoomPrivilegeRequest,
    GetRoomUsersRequest,
    GetWalletRequest,
    IndicatorRequest,
    Item,
    KeepaliveRequest,
    ModerateRoomRequest,
    Position,
    Reaction,
    ReactionEvent,
    ReactionRequest,
    RoomPermissions,
    SessionMetadata,
    TeleportRequest,
    TipReactionEvent,
    User,
    UserJoinedEvent,
    UserLeftEvent,
)

if TYPE_CHECKING:
    from attrs import AttrsInstance
else:

    class AttrsInstance(Protocol):
        pass


__all__ = [
    "BaseBot",
    "Highrise",
    "User",
    "Position",
    "Reaction",
    "AnchorPosition",
    "RoomPermissions",
]
A = TypeVar("A", bound=AttrsInstance)
T = TypeVar("T")


class BaseBot:
    """A base class for Highrise bots.
    Bots join a room and interact with everything in it.

    Subclass this class and implement the handlers you want to use.

    The `self.highrise` attribute can be used to make requests.
    """

    highrise: Highrise

    async def on_start(self, session_metadata: SessionMetadata) -> None:
        """On a connection to the room being established.

        This may be called multiple times, since the connection may be dropped
        and reestablished.
        """
        pass

    async def on_chat(self, user: User, message: str) -> None:
        """On a received room-wide chat."""
        pass

    async def on_whisper(self, user: User, message: str) -> None:
        """On a received room whisper."""
        pass

    async def on_emote(self, user: User, emote_id: str, receiver: User | None) -> None:
        """On a received emote."""
        pass

    async def on_reaction(self, user: User, reaction: Reaction, receiver: User) -> None:
        """Called when someone reacts in the room."""
        pass

    async def on_user_join(self, user: User) -> None:
        """On a user joining the room."""
        pass

    async def on_user_leave(self, user: User) -> None:
        """On a user leaving the room."""
        pass

    async def on_tip(
        self, sender: User, receiver: User, tip: CurrencyItem | Item
    ) -> None:
        """On a tip received in the room."""
        pass

    async def on_channel(self, sender_id: str, message: str, tags: set[str]) -> None:
        """On a hidden channel message."""
        pass


class Highrise:
    ws: ClientWebSocketResponse
    tg: TaskGroup
    _req_id = count()
    _req_id_registry: dict[str, Queue[Any]] = {}

    async def chat(self, message: str) -> None:
        """Broadcast a room-wide chat message."""
        await _do_req_no_resp(self, ChatRequest(message=message))

    async def send_whisper(self, user_id: str, message: str) -> None:
        """Send a whisper to a user in the room."""
        await _do_req_no_resp(
            self, ChatRequest(message=message, whisper_target_id=user_id)
        )

    async def send_emote(
        self, emote_id: str, target_user_id: str | None = None
    ) -> None:
        """Send an emote to room or a user in the room."""
        await _do_req_no_resp(self, EmoteRequest(emote_id, target_user_id))

    async def react(self, reaction: Reaction, target_user_id: str) -> None:
        """
        Send a reaction to a user in the room.

        A reaction can be one of the following:
        * 'clap'
        * 'heart'
        * 'thumbs'
        * 'wave'
        * 'wink'
        """
        await _do_req_no_resp(self, ReactionRequest(reaction, target_user_id))

    async def set_indicator(self, icon: str | None) -> None:
        await _do_req_no_resp(self, IndicatorRequest(icon))

    async def send_channel(self, message: str, tags: set[str] = set()) -> None:
        await _do_req_no_resp(self, ChannelRequest(message, tags))

    async def walk_to(self, destination: Position) -> None:
        await _do_req_no_resp(self, FloorHitRequest(destination))

    async def teleport(self, user_id: str, dest: Position) -> None:
        await _do_req_no_resp(self, TeleportRequest(user_id, dest))

    async def get_room_users(self) -> GetRoomUsersRequest.GetRoomUsersResponse | Error:
        req_id = str(next(self._req_id))
        self._req_id_registry[req_id] = (q := Queue[Any](maxsize=1))
        await self.ws.send_str(
            converter.dumps(GetRoomUsersRequest(str(req_id)), Outgoing)
        )
        return await q.get()

    async def get_wallet(self) -> GetWalletRequest.GetWalletResponse | Error:
        """Fetch the bot wallet."""
        return await do_req_resp(self, GetWalletRequest())

    async def moderate_room(
        self,
        user_id: str,
        action: Literal["kick", "ban", "unban", "mute"],
        action_length: int | None = None,
    ) -> None:
        """Moderate a user in the room."""
        await _do_req_no_resp(self, ModerateRoomRequest(user_id, action, action_length))

    async def get_room_privilege(
        self, user_id: str
    ) -> RoomPermissions | Error:
        """Fetch the room privilege for given user_id."""
        resp = await do_req_resp(self, GetRoomPrivilegeRequest(user_id))
        if isinstance(resp, Error):
            return resp
        return resp.content

    async def change_room_privilege(
        self, user_id: str, permissions: RoomPermissions
    ) -> None:
        """Change the room privilege for given user_id.

        example: self.highrise.change_room_privilege(user_id, RoomPermissions(moderator=True))

        """
        await _do_req_no_resp(self, ChangeRoomPrivilegeRequest(user_id, permissions))

    def call_in(self, callback: Callable, delay: float) -> None:
        self.tg.create_task(_delayed_callback(callback, delay))


class ResponseError(Exception):
    """An API response error."""


class _ClassWithId(AttrsInstance):
    rid: str | None


CID = TypeVar("CID", bound=_ClassWithId, covariant=True)


class _ReqWithId(AttrsInstance, Protocol[CID]):
    rid: str | None

    @property
    def Response(self) -> type[CID]:
        ...


async def do_req_resp(hr: Highrise, req: _ReqWithId[CID]) -> CID | Error:
    rid = str(next(hr._req_id))
    req.rid = rid
    hr._req_id_registry[rid] = (q := Queue[Any](maxsize=1))
    await hr.ws.send_str(converter.dumps(req, Outgoing))
    return await q.get()


async def _do_req_no_resp(hr: Highrise, req: _ReqWithId[CID]) -> None:
    rid = str(next(hr._req_id))
    req.rid = rid
    hr._req_id_registry[rid] = (q := Queue[Any](maxsize=1))
    await hr.ws.send_str(converter.dumps(req, Outgoing))
    resp = await q.get()
    if isinstance(resp, Error):
        raise ResponseError(resp.message)


async def _delayed_callback(callback: Callable, delay: float) -> None:
    await sleep(delay)
    await callback()


converter = make_converter()

Outgoing = (
    ChatRequest
    | IndicatorRequest
    | ReactionRequest
    | EmoteRequest
    | ChannelRequest
    | FloorHitRequest
    | TeleportRequest
    | GetRoomUsersRequest
    | GetWalletRequest
    | GetRoomPrivilegeRequest
    | ChangeRoomPrivilegeRequest
    | ModerateRoomRequest
    | KeepaliveRequest
)
IncomingEvents = (
    Error
    | ChatEvent
    | EmoteEvent
    | ReactionEvent
    | UserJoinedEvent
    | UserLeftEvent
    | ChannelEvent
    | TipReactionEvent
)
Incoming = IncomingEvents | Union[*(r.Response for r in Outgoing.__args__)]  # type: ignore

configure_tagged_union(SessionMetadata | Error, converter)
configure_tagged_union(Incoming, converter)
configure_tagged_union(Outgoing, converter)
