from collections import Counter
from datetime import datetime
from typing import ClassVar, Literal, TypeAlias

from attrs import Factory, define


@define
class User:
    id: str
    username: str


Reaction: TypeAlias = Literal["clap", "heart", "thumbs", "wave", "wink"]
Facing: TypeAlias = Literal["FrontRight", "FrontLeft", "BackRight", "BackLeft"]


@define
class RoomPermissions:
    moderator: bool | None = None
    designer: bool | None = None


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
    account_bound: bool = False
    active_palette: int | None = None


@define
class Message:
    """
    A Highrise conversation message.
    """

    message_id: str
    conversation_id: str
    createdAt: datetime | None

    content: str
    sender_id: str

    category: Literal["text", "invite"]


@define
class Conversation:
    """
    A Highrise conversation. Bots can join direct conversations, but not group conversations.
    Bots can respond to messages in conversations, but cannot initiate messages.
    """

    id: str
    did_join: bool
    unread_count: int
    last_message: Message | None
    muted: bool
    member_ids: list[str] | None = None
    name: str | None = None
    owner_id: str | None = None


@define
class Error:
    """
    The client request or parameter was invalid.
    """

    message: str
    do_not_reconnect: bool = False
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
        """The successful response to a `ChatRequest`."""

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
        """The successful response to a `EmoteRequest`."""

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

    rid: str | None = None

    @define
    class KeepaliveResponse:
        """
        A response to a successful reaction.
        """

        rid: str | None = None

    Response: ClassVar = KeepaliveResponse


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
class AnchorHitRequest:
    """
    Move the bot to the given `destination`.

    """

    anchor: AnchorPosition
    rid: str | None = None

    @define
    class AnchorHitResponse:
        """The successful response to a `TeleportRequest`."""

        rid: str | None = None

    Response: ClassVar = AnchorHitResponse


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
class ModerateRoomRequest:
    """
    Moderate the room.

    This can be used to kick, ban, unban, or mute a user.
    """

    user_id: str
    moderation_action: Literal["kick", "ban", "unban", "mute"]
    action_length: int | None = None
    rid: str | None = None

    @define
    class ModerateRoomResponse:
        """
        The successful response to a `ModerateRoomRequest`.
        """

        rid: str | None = None

    Response: ClassVar = ModerateRoomResponse


@define
class GetRoomPrivilegeRequest:
    """
    Fetch the room privileges for provided `user_id`.
    """

    user_id: str
    rid: str | None = None

    @define
    class GetRoomPrivilegeResponse:
        """
        The room privileges for provided `user_id`.
        """

        content: RoomPermissions
        rid: str

    Response: ClassVar = GetRoomPrivilegeResponse


@define
class ChangeRoomPrivilegeRequest:
    """
    Change the room privileges for provided `user_id`.
    This can be used to both give and take moderation and designer privileges for current room.

    Bots have to be in the room to change privileges.
    Bots are using their owner's privileges.
    """

    user_id: str
    permissions: RoomPermissions
    rid: str | None = None

    @define
    class ChangeRoomPrivilegeResponse:
        """
        The successful response to a `ChangeRoomPrivilegeRequest`.
        """

        rid: str

    Response: ClassVar = ChangeRoomPrivilegeResponse


@define
class MoveUserToRoomRequest:
    """
    Move user to another room using room_id as a target room id
    Bot operator must be owner of the target room, or has designer privileges in the target room, this will also work
    if bot has designer privileges in the target room.

    All other restriction to room movement apply, ie if target room is full this will fail.

    """

    user_id: str
    room_id: str

    rid: str | None = None

    @define
    class MoveUserToRoomResponse:
        rid: str

    Response: ClassVar = MoveUserToRoomResponse


@define
class RoomInfo:
    """
    Information about the room.
    """

    owner_id: str
    room_name: str


@define
class GetBackpackRequest:
    """
    Fetch a user's world backpack.
    """

    user_id: str
    rid: str | None = None

    @define
    class GetBackpackResponse:
        backpack: Counter[str]
        rid: str | None = None

    Response: ClassVar = GetBackpackResponse


@define
class ChangeBackpackRequest:
    user_id: str
    changes: Counter[str]
    rid: str | None = None

    @define
    class ChangeBackpackResponse:
        rid: str | None = None

    Response: ClassVar = ChangeBackpackResponse


@define
class SessionMetadata:
    """
    Initial session data.

    This will be sent once, as the first message when a connection is established.
    user_id is the bot's user id.
    room_info is additional information about the connected room.
    rate_limits is a dictionary of rate limits, with the key being the rate limit name and the value being a tuple of
    (limit, period).
    connection_id is the connection id of the websocket used in bot connection.
    sdk_versions is a string containing the SDK versions recommended by the server if user is using SDK.


    """

    user_id: str
    room_info: RoomInfo
    rate_limits: dict[str, tuple[int, float]]
    connection_id: str
    sdk_version: str | None = None


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
    position: Position | AnchorPosition


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


@define
class UserMovedEvent:
    """
    A user has moved in the room.
    user: User that moved
    position: New position of the user or anchor position
    """

    user: User
    position: Position | AnchorPosition


@define
class VoiceEvent:
    """
    Event that is sent when status of voice is changed in the room.

    users: The list of users that currently have voice chat privileges in the room and status of their voice.
    seconds_left: The number of seconds left until the voice chat ends.
    """

    users: list[tuple[User, Literal["voice", "muted"]]]
    seconds_left: int


@define
class MessageEvent:
    """
    A message event, indicating that bot has received a message from someone. If the message is from a new conversation,
     `is_new_conversation` field will be True.
    """

    user_id: str
    conversation_id: str
    is_new_conversation: bool


@define
class RoomModeratedEvent:
    """A moderation event happened in room. This event is sent when a user is muted, unmuted, kicked, banned or unbanned.
    Muted and banned events can also have duration field which indicates how long the user is muted or banned for.
    """

    moderatorId: str
    targetUserId: str
    moderationType: Literal["kick", "mute", "unmute", "ban", "unban"]
    duration: int | None


@define
class CheckVoiceChatRequest:
    """
    Check the voice chat status in the room.
    """

    rid: str | None = None

    @define
    class CheckVoiceChatResponse:
        """

        Returns the status of voice chat in the room.
        seconds_left: The number of seconds left until the voice chat ends.
        auto_speakers: The list of users that automatically have voice chat privileges in the room like moderators and
        owner.
        users: The list of users that currently have voice chat privileges in the room.

        """

        seconds_left: int
        auto_speakers: set[str]
        users: dict[str, Literal["invited", "voice", "muted"]]
        rid: str | None = None

    Response: ClassVar = CheckVoiceChatResponse


@define
class InviteSpeakerRequest:
    """
    Invite a user to speak in the room.
    """

    user_id: str
    rid: str | None = None

    @define
    class InviteSpeakerResponse:
        rid: str | None = None

    Response: ClassVar = InviteSpeakerResponse


@define
class RemoveSpeakerRequest:
    """
    Remove a user from speaking in the room.
    """

    user_id: str
    rid: str | None = None

    @define
    class RemoveSpeakerResponse:
        rid: str | None = None

    Response: ClassVar = RemoveSpeakerResponse


@define
class GetUserOutfitRequest:
    """
    Get the outfit of a user.
    """

    user_id: str
    rid: str | None = None

    @define
    class GetUserOutfitResponse:
        """
        The outfit of a user. Returns list of items user is currently wearing.
        """

        outfit: list[Item]
        rid: str | None = None

    Response: ClassVar = GetUserOutfitResponse


@define
class GetConversationsRequest:
    """
    Get the conversations of a bat. if not_joined is true, only get the conversations that bot has not joined yet will
    be returned. 20 conversations will be returned at most, if all 20 conversations are returned, the last_id can be used
    to retrieve the next 20 conversations.
    """

    not_joined: bool = False
    last_id: str | None = None
    rid: str | None = None

    @define
    class GetConversationsResponse:
        conversations: list[Conversation]
        not_joined: int
        rid: str | None = None

    Response: ClassVar = GetConversationsResponse


@define
class SendMessageRequest:
    """
    Send a message to a conversation. If bot wishes to send room invite, the room_id must be provided. If bot wishes to
    send world invite, the world_id must be provided.
    """

    conversation_id: str
    content: str
    type: Literal["text", "invite"]
    room_id: str | None = None
    world_id: str | None = None
    rid: str | None = None

    @define
    class SendMessageResponse:
        rid: str | None = None

    Response: ClassVar = SendMessageResponse


@define
class SendBulkMessageRequest:
    """
    Send a message to a multiple users, with limit being 100. If bot wishes to send room invite, the room_id must
    be provided. If bot wishes to send world invite, the world_id must be provided.
    """

    user_ids: list[str]
    content: str
    type: Literal["text", "invite"]
    room_id: str | None = None
    world_id: str | None = None
    rid: str | None = None

    @define
    class SendBulkMessageResponse:
        rid: str | None = None

    Response: ClassVar = SendBulkMessageResponse


@define
class GetMessagesRequest:
    """
    Get the messages of a conversation.
    20 messages will be returned at most, if all 20 messages are returned, the
     last_message_id can be used to retrieve the next 20 messages.
    """

    conversation_id: str
    last_message_id: str | None = None
    rid: str | None = None

    @define
    class GetMessagesResponse:
        messages: list[Message]
        rid: str | None = None

    Response: ClassVar = GetMessagesResponse


@define
class LeaveConversationRequest:
    """
    Leave a conversation.
    """

    conversation_id: str
    rid: str | None = None

    @define
    class LeaveConversationResponse:
        """
        The leave conversation success response.
        """

        rid: str | None = None

    Response: ClassVar = LeaveConversationResponse


@define
class BuyVoiceTimeRequest:
    """Buy a voice time for a room."""

    payment_method: Literal["bot_wallet_only"]
    rid: str | None = None

    @define
    class BuyVoiceTimeResponse:
        """Buy a voice token."""

        result: Literal["success", "insufficient_funds", "only_token_bought"]
        rid: str | None = None

    Response: ClassVar = BuyVoiceTimeResponse


@define
class BuyRoomBoostRequest:
    """Buy a room boost."""

    payment_method: Literal["bot_wallet_only"]
    amount: int = 1
    rid: str | None = None

    @define
    class BuyRoomBoostResponse:
        """Buy a room boost."""

        result: Literal["success", "insufficient_funds", "only_token_bought"]
        rid: str | None = None

    Response: ClassVar = BuyRoomBoostResponse


@define
class TipUserRequest:
    """Tip a user."""

    user_id: str
    gold_bar: Literal[
        "gold_bar_1",
        "gold_bar_5",
        "gold_bar_10",
        "gold_bar_50",
        "gold_bar_100",
        "gold_bar_500",
        "gold_bar_1k",
        "gold_bar_5000",
        "gold_bar_10k",
    ]
    rid: str | None = None

    @define
    class TipUserResponse:
        """Tip a user."""

        result: Literal["success", "insufficient_funds"]
        rid: str | None = None

    Response: ClassVar = TipUserResponse


@define
class GetInventoryRequest:
    """Get the inventory of a bot."""

    rid: str | None = None

    @define
    class GetInventoryResponse:
        """Get the inventory of a bot."""

        items: list[Item]
        rid: str | None = None

    Response: ClassVar = GetInventoryResponse


@define
class SetOutfitRequest:
    """Set the outfit of a bot."""

    outfit: list[Item]
    rid: str | None = None

    @define
    class SetOutfitResponse:
        """Set the outfit of a bot."""

        rid: str | None = None

    Response: ClassVar = SetOutfitResponse


@define
class BuyItemRequest:
    """Buy an item."""

    item_id: str
    rid: str | None = None

    @define
    class BuyItemResponse:
        """Buy an item."""

        result: Literal["success", "insufficient_funds"]
        rid: str | None = None

    Response: ClassVar = BuyItemResponse
