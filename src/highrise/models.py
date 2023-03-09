from typing import Literal, TypeAlias

from attrs import Factory, define


@define
class User:
    id: str
    username: str


Position: TypeAlias = tuple[float, float, float]


@define
class Error:
    """
    The client request or parameter was invalid.
    """

    message: str
    rid: str | None = None


@define
class ChatRequest:
    """
    Send a chat message to a room.

    The chat message will be broadcast to everyone in the room, or whispered to `whisper_target_id` if provided.
    """

    message: str
    whisper_target_id: str | None = None


@define
class IndicatorRequest:
    """
    Set the bot indicator to the provided icon, or clear it.

    """

    icon: str | None = None


@define
class ChannelRequest:
    """
    Send a hidden channel message to the room.

    This message not be displayed in the chat, so it can be used to
    communicate between bots or client-side scripts.
    """

    msg: str
    tags: list[str] = Factory(list)
    only_to: set[str] | None = None


@define
class EmoteRequest:
    """
    Perform an emote.

    `target_user_id` can be provided if the emote can be directed toward a player.
    """

    emote_id: str
    target_user_id: str | None = None


@define
class KeepaliveRequest:
    """
    Send a keepalive request.

    This must be sent every 15 seconds or the server will terminate the connection.
    """


@define
class TeleportRequest:
    """
    Teleport the provided `user_id` to the provided `destination`.

    """

    user_id: str
    destination: Position


@define
class FloorHitRequest:
    """
    Move the bot to the given `destination`.

    """

    destination: Position
    facing: Literal["FrontLeft", "FrontRight", "BackLeft", "BackRight"]


@define
class GetRoomUsersRequest:
    """
    Fetch the list of users currently in the room, with their positions.

    """

    rid: str


@define
class GetRoomUsersResponse:
    """
    The list of users in the room, alongside their positions.

    """

    rid: str
    content: list[tuple[User, Position]]


@define
class SessionMetadata:
    """
    Initial data.

    This will be sent once, as the first message when a connection is established.
    """

    user_id: str


@define
class ChatEvent:
    """
    A chat event, sent by a `user` in the room.
    """

    user: User
    message: str
    whisper: bool


@define
class UserJoinedEvent:
    """
    A user has joined the room.
    """

    user: User


@define
class UserLeftEvent:
    """
    A user has left the room.
    """

    user_id: str


@define
class ChannelEvent:
    """
    A hidden channel event.
    """

    sender_id: str
    msg: str
    tags: list[str] = Factory(list)


@define
class Item:
    type: str
    amount: int
    id: str | None = None


@define
class TipReactionEvent:
    """
    The `sender` has sent `receiver` a tip (the `item`) in the current room.
    """

    sender: User
    receiver: User
    item: Item
