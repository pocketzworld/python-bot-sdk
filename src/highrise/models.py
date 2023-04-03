from typing import ClassVar, Literal, TypeAlias

from attrs import Factory, define


@define
class User:
    id: str
    username: str


Reaction: TypeAlias = Literal["clap", "heart", "thumbs", "wave", "wink"]
Facing: TypeAlias = Literal["FrontRight", "FrontLeft", "BackRight", "BackLeft"]


@define
class Position:
    x: float
    y: float
    z: float
    facing: Facing = "FrontRight"


@define
class AnchorPosition:
    entity_id: str
    anchor_ix: int


@define
class CurrencyItem:
    """
    A Highrise currency amount.

    The most used currencies are:
    * `gold`
    * `bubbles`

    Many other currencies exist, however.
    """

    type: str
    amount: int


@define
class Item:
    """A Highrise item."""

    type: Literal["clothing"]
    amount: int
    id: str


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
    rid: str | None = None

    @define
    class ChatResponse:
        rid: str | None = None
        """The successful response to a `ChatResponse."""

    Response: ClassVar = ChatResponse


@define
class IndicatorRequest:
    icon: str | None = None
    rid: str | None = None

    @define
    class IndicatorResponse:
        rid: str | None = None

    Response: ClassVar = IndicatorResponse


@define
class ChannelRequest:
    """
    Send a hidden channel message to the room.

    This message not be displayed in the chat, so it can be used to
    communicate between bots or client-side scripts.
    """

    message: str
    tags: set[str] = Factory(set)
    only_to: set[str] | None = None
    rid: str | None = None

    @define
    class ChannelResponse:
        """The successful response to a `ChannelRequest."""

        rid: str | None = None

    Response: ClassVar = ChannelResponse


@define
class EmoteRequest:
    """
    Perform an emote.

    `target_user_id` can be provided if the emote can be directed toward a player.
    """

    emote_id: str
    target_user_id: str | None = None
    rid: str | None = None

    @define
    class EmoteResponse:
        """The successful response to a `EmoteRequest."""

        rid: str | None = None

    Response: ClassVar = EmoteResponse


@define
class ReactionRequest:
    """
    Send a reaction to a user.
    """

    reaction: Reaction
    target_user_id: str
    rid: str | None = None

    @define
    class ReactionResponse:
        """
        A response to a successful reaction.
        """

        rid: str | None = None

    Response: ClassVar = ReactionResponse


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
    rid: str | None = None

    @define
    class TeleportResponse:
        """The successful response to a `TeleportRequest`."""

        rid: str | None = None

    Response: ClassVar = TeleportResponse


@define
class FloorHitRequest:
    """
    Move the bot to the given `destination`.

    """

    destination: Position
    rid: str | None = None

    @define
    class FloorHitResponse:
        """The successful response to a `TeleportRequest`."""

        rid: str | None = None

    Response: ClassVar = FloorHitResponse


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

        content: list[tuple[User, Position | AnchorPosition]]
        rid: str

    Response: ClassVar = GetRoomUsersResponse


@define
class GetWalletRequest:
    """
    Fetch the bot's wallet.

    The wallet contains Highrise currencies.
    """

    rid: str | None = None

    @define
    class GetWalletResponse:
        """
        The bot's wallet.
        """

        content: list[CurrencyItem]
        rid: str

    Response: ClassVar = GetWalletResponse


@define
class SessionMetadata:
    """
    Initial session data.

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
class EmoteEvent:
    """
    An emote event, performed by a `user` in the room.
    """

    user: User
    emote_id: str
    receiver: User | None = None


@define
class ReactionEvent:
    """
    A reaction event, performed by a `user` in the room.
    """

    user: User
    reaction: Reaction
    receiver: User


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

    user: User


@define
class ChannelEvent:
    """
    A hidden channel event.
    """

    sender_id: str
    msg: str
    tags: list[str] = Factory(list)


@define
class TipReactionEvent:
    """
    The `sender` has sent `receiver` a tip (the `item`) in the current room.
    """

    sender: User
    receiver: User
    item: Item | CurrencyItem
