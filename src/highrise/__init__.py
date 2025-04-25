"""The Highrise bot SDK."""
from __future__ import annotations

import json
import re
from asyncio import Queue, sleep
from collections import Counter
from itertools import count
from typing import TYPE_CHECKING, Any, Callable, Literal, Protocol, TypeVar, Union

from aiohttp import ClientWebSocketResponse
from cattrs.preconf.json import make_converter
from quattro import TaskGroup
import pickle as pkl

from ._unions import configure_tagged_union
from .models import (
    AnchorHitRequest,
    AnchorPosition,
    BuyItemRequest,
    BuyRoomBoostRequest,
    BuyVoiceTimeRequest,
    ChangeBackpackRequest,
    ChangeRoomPrivilegeRequest,
    ChannelEvent,
    ChannelRequest,
    ChatEvent,
    ChatRequest,
    CheckVoiceChatRequest,
    CurrencyItem,
    EmoteEvent,
    EmoteRequest,
    Error,
    FloorHitRequest,
    GetBackpackRequest,
    GetConversationsRequest,
    GetInventoryRequest,
    GetMessagesRequest,
    GetRoomPrivilegeRequest,
    GetRoomUsersRequest,
    GetUserOutfitRequest,
    GetWalletRequest,
    IndicatorRequest,
    InviteSpeakerRequest,
    Item,
    KeepaliveRequest,
    LeaveConversationRequest,
    MessageEvent,
    ModerateRoomRequest,
    MoveUserToRoomRequest,
    Position,
    Reaction,
    ReactionEvent,
    ReactionRequest,
    RemoveSpeakerRequest,
    RoomModeratedEvent,
    RoomPermissions,
    SendBulkMessageRequest,
    SendMessageRequest,
    SessionMetadata,
    SetOutfitRequest,
    TeleportRequest,
    TipReactionEvent,
    TipUserRequest,
    User,
    UserJoinedEvent,
    UserLeftEvent,
    UserMovedEvent,
    VoiceEvent,
)
from .webapi import WebAPI
from .models_webapi import Rarity

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
    webapi: WebAPI

    async def before_start(self, tg: TaskGroup) -> None:
        """Called before the bot starts."""
        pass

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

    async def on_user_join(
        self, user: User, position: Position | AnchorPosition
    ) -> None:
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

    async def on_user_move(
        self, user: User, destination: Position | AnchorPosition
    ) -> None:
        """On a user moving in the room."""
        pass

    async def on_voice_change(
        self, users: list[tuple[User, Literal["voice", "muted"]]], seconds_left: int
    ) -> None:
        """On a change in voice status in the room."""
        pass

    async def on_message(
        self, user_id: str, conversation_id: str, is_new_conversation: bool
    ) -> None:
        """On a inbox message received from a user."""
        pass

    async def on_moderate(
        self,
        moderator_id: str,
        target_user_id: str,
        moderation_type: Literal["kick", "mute", "unmute", "ban", "unban"],
        duration: int | None,
    ) -> None:
        """When room moderation event is triggered."""
        pass

    async def equip(self: BaseBot, user: User, message: list[str]) -> Optional[Error]:
        args = message[1:]
        if not args:
            return Error("Invalid command format. You need to specify the item.")
        color = 0
        index = 0
        item_tokens: list[str] = []
        for tok in args:
            m = re.fullmatch(r'\[(\d+)\]', tok)
            if m:
                index = int(m.group(1))
                continue
            if tok.isdigit():
                color = int(tok)
                continue
            item_tokens.append(tok)
        item_name = " ".join(item_tokens).strip()
        if not item_name:
            return Error("Could not parse item name.")
        items = (await self.webapi.get_items(item_name=item_name, limit=100)).items
        if not items:
            await self.highrise.chat(f"Item '{item_name}' not found.")
            return Error(f"Item '{item_name}' not found.")
        if index >= len(items):
            await self.highrise.chat(f"Index {index} out of range for items matching '{item_name}'.")
            return Error(f"Index {index} out of range for '{item_name}'.")
        if len(items) > 1:
            chosen = items[index]
            await self.highrise.chat(f"Multiple items found for '{item_name}':")
            max_length = 255
            current_message = ""
            for i, item in enumerate(items):
                item_str = f"[{i}] {item.item_name}"
                if len(current_message) + len(item_str) + 1 > max_length:  # +1 for newline
                    await self.highrise.chat(current_message)
                    current_message = item_str
                else:
                    if current_message:
                        current_message += "\n" + item_str
                    else:
                        current_message = item_str
            if current_message:
                await self.highrise.chat(current_message)
            await self.highrise.chat(f"Using [{index}] {chosen.item_name}.")
        item = items[index]
        item_id = item.item_id
        category = item.category
        owned_ids = {inv.id for inv in (await self.highrise.get_inventory()).items}
        if item_id not in owned_ids:
            if item.rarity != Rarity.NONE and item.is_purchasable:
                resp = await self.highrise.buy_item(item_id)
                if resp == "success":
                    await self.highrise.chat(f"Item '{item_name}' purchased.")
                else:
                    await self.highrise.chat(f"Item '{item_name}' can't be purchased.")
                    return Error(f"Buy failed for '{item_name}'.")
            elif not item.is_purchasable:
                await self.highrise.chat(f"Item '{item_name}' can't be purchased.")
                return Error(f"Item '{item_name}' can't be purchased.")
        new_item = Item(
            type="clothing",
            amount=1,
            id=item_id,
            account_bound=False,
            active_palette=color,
        )
        outfit = (await self.highrise.get_my_outfit()).outfit
        outfit = [
            outf
            for outf in outfit
            if outf.id.split("-")[0] != category
        ]
        if category == "hair_front" and item.link_ids:
            outfit = [
                outf
                for outf in outfit
                if outf.id.split("-")[0] != "hair_back"
            ]
            back_id = item.link_ids[0]
            outfit.append(
                Item(
                    type="clothing",
                    amount=1,
                    id=back_id,
                    account_bound=False,
                    active_palette=color,
                )
            )
        outfit.append(new_item)
        await self.highrise.set_outfit(outfit)
        await self.highrise.chat(f"Item '{item_name}' equipped.")
        return None


    async def change_skin_tone(self: BaseBot, user: User, message: str) -> Error|None:
        if len(message) < 2:
            return Error("Invalid command format. You need to specify the color.")
        try:
            color = int(message[1])
        except:
            return Error("Invalid color.")
        outfit = (await self.highrise.get_my_outfit()).outfit
        for outfit_item in outfit:
            if outfit_item.id == "body-flesh":
                outfit_item.active_palette = color
                break
        return await self.highrise.set_outfit(outfit)

    async def remove(self: BaseBot, user: User, message: str) -> Error|None:
            categories = ["aura","bag","blush","body","dress","earrings","emote","eye","eyebrow","fishing_rod","freckle","fullsuit","glasses",
"gloves","hair_back","hair_front","handbag","hat","jacket","lashes","mole","mouth","necklace","nose","pants","rod","shirt","shoes",
"shorts","skirt","sock","tattoo","watch"]
            if len(message) != 2:
                return Error("Invalid command format. You need to specify the category.")
            if message[1] not in categories:
                return Error("Invalid category.")
            category = message[1].lower()
            outfit = (await self.highrise.get_my_outfit()).outfit
            for outfit_item in outfit:
                #the category of the item in an outfit can be found by the first string in the id before the "-" character
                item_category = outfit_item.id.split("-")[0]
                if item_category == category:
                    try:
                        outfit.remove(outfit_item)
                    except:
                        return Error(f"The bot isn't using any item from the category '{category}'.")
            return await self.highrise.set_outfit(outfit)


class Highrise:
    my_id: str
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

    async def walk_to(self, destination: Position | AnchorPosition) -> None:
        if isinstance(destination, AnchorPosition):
            await _do_req_no_resp(self, AnchorHitRequest(destination))
        else:
            await _do_req_no_resp(self, FloorHitRequest(destination))

    async def teleport(self, user_id: str, dest: Position) -> None:
        await _do_req_no_resp(self, TeleportRequest(user_id, dest))
        
    async def set_position(self, user: User) -> None:
        """Sets the bot position to the user's position"""
        room_users = (await self.get_room_users()).content
        for room_user, pos in room_users:
            if room_user == user:
                pkl.dump(pos, open(f'data/{self.my_id}_position.pkl', 'wb'))
                if isinstance(pos, AnchorPosition):
                    await self.walk_to(pos)
                else:
                    await self.teleport(self.my_id, pos)
                    await self.walk_to(pos)

    async def load_position(self) -> None:
        """Defines the Bot's position based on a {bot_id}_position.pkl file."""
        try:
            pos = pkl.load(open(f'data/{self.my_id}_position.pkl', 'rb'))
            if isinstance(pos, AnchorPosition):
                await self.walk_to(pos)
            else:
                await self.teleport(self.my_id, pos)
                await self.walk_to(pos)
            return
        except:
            return 

    async def tip(self, user: User, amount: int) -> Error|None:
        bot_wallet = await self.get_wallet()
        bot_amount = bot_wallet.content[0].amount
        if bot_amount <= amount:
            await self.chat("Not enough funds")
            return Error("Not enough funds")
        """Possible values are: "gold_bar_1",
        "gold_bar_5", "gold_bar_10", "gold_bar_50", 
        "gold_bar_100", "gold_bar_500", 
        "gold_bar_1k", "gold_bar_5000", "gold_bar_10k" """
        bars_dictionary = {10000: "gold_bar_10k", 
                            5000: "gold_bar_5000",
                            1000: "gold_bar_1k",
                            500: "gold_bar_500",
                            100: "gold_bar_100",
                            50: "gold_bar_50",
                            10: "gold_bar_10",
                            5: "gold_bar_5",
                            1: "gold_bar_1"}
        fees_dictionary = {10000: 1000,
                            5000: 500,
                            1000: 100,
                            500: 50,
                            100: 10,
                            50: 5,
                            10: 1,
                            5: 1,
                            1: 1}
        tip = []
        total = 0
        for bar in bars_dictionary:
            if amount >= bar:
                bar_amount = amount // bar
                amount = amount % bar
                for i in range(bar_amount):
                    tip.append(bars_dictionary[bar])
                    total = bar+fees_dictionary[bar]
        if total > bot_amount:
            await self.chat("Not enough funds")
            return Error("Not enough funds")
        for bar in tip:
            await self.tip_user(user.id, bar)

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

    async def get_backpack(
        self, user_id: str
    ) -> GetBackpackRequest.GetBackpackResponse | Error:
        """Fetch a user's backpack."""
        return await do_req_resp(self, GetBackpackRequest(user_id))

    async def change_backpack(
        self, user_id: str, changes: dict[str, int]
    ) -> ChangeBackpackRequest.ChangeBackpackResponse | Error:
        """Change a user's backpack."""
        return await do_req_resp(self, ChangeBackpackRequest(user_id, Counter(changes)))

    async def moderate_room(
        self,
        user_id: str,
        action: Literal["kick", "ban", "unban", "mute"],
        action_length: int | None = None,
    ) -> None:
        """Moderate a user in the room."""
        await _do_req_no_resp(self, ModerateRoomRequest(user_id, action, action_length))

    async def get_room_privilege(self, user_id: str) -> RoomPermissions | Error:
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

    async def move_user_to_room(self, user_id: str, room_id: str) -> None:
        """Attempt to move user to a different room.

        This will only work if the bot belongs to owner of target room, or has designer privileges.
        """
        await _do_req_no_resp(self, MoveUserToRoomRequest(user_id, room_id))

    async def get_voice_status(
        self,
    ) -> CheckVoiceChatRequest.CheckVoiceChatResponse | Error:
        """Fetch the voice status for the room."""
        return await do_req_resp(self, CheckVoiceChatRequest())

    async def add_user_to_voice(self, user_id: str) -> None:
        """Add a user to voice chat."""
        await _do_req_no_resp(self, InviteSpeakerRequest(user_id))

    async def remove_user_from_voice(self, user_id: str) -> None:
        """Remove a user from voice chat."""
        await _do_req_no_resp(self, RemoveSpeakerRequest(user_id))

    async def get_user_outfit(
        self, user_id: str
    ) -> GetUserOutfitRequest.GetUserOutfitResponse | Error:
        """Fetch the outfit for a user."""
        return await do_req_resp(self, GetUserOutfitRequest(user_id))

    async def get_conversations(
        self, not_joined: bool = False, last_id: str | None = None
    ) -> GetConversationsRequest.GetConversationsResponse | Error:
        """Fetch the conversations for the bot."""
        return await do_req_resp(self, GetConversationsRequest(not_joined, last_id))

    async def send_message(
        self,
        conversation_id: str,
        content: str,
        message_type: Literal["text", "invite"] = "text",
        room_id: str | None = None,
        world_id: str | None = None,
    ) -> None | Error:
        """Send a message to conversation."""
        res = await do_req_resp(
            self,
            SendMessageRequest(
                conversation_id, content, message_type, room_id, world_id
            ),
        )
        if isinstance(res, Error):
            return res
        return None

    async def send_message_bulk(
        self,
        user_ids: list[str],
        content: str,
        message_type: Literal["text", "invite"] = "text",
        room_id: str | None = None,
        world_id: str | None = None,
    ) -> None | Error:
        """Send a message to conversation."""
        res = await do_req_resp(
            self,
            SendBulkMessageRequest(user_ids, content, message_type, room_id, world_id),
        )
        if isinstance(res, Error):
            return res
        return None

    async def get_messages(
        self, conversation_id: str, last_id: str | None = None
    ) -> GetMessagesRequest.GetMessagesResponse | Error:
        """Fetch messages from a conversation."""
        return await do_req_resp(self, GetMessagesRequest(conversation_id, last_id))

    async def leave_conversation(self, conversation_id: str) -> None:
        """Leave a conversation."""
        await _do_req_no_resp(self, LeaveConversationRequest(conversation_id))

    async def buy_voice_time(
        self,
        payment: Literal["bot_wallet_only"] = "bot_wallet_only",
    ) -> Literal["success", "insufficient_funds", "only_token_bought"] | Error:
        """Buy voice time."""
        res = await do_req_resp(self, BuyVoiceTimeRequest(payment))
        if isinstance(res, Error):
            return res
        return res.result

    async def buy_room_boost(
        self,
        payment: Literal["bot_wallet_only"] = "bot_wallet_only",
        amount: int = 1,
    ) -> Literal["success", "insufficient_funds", "only_token_bought"] | Error:
        """Buy room boost."""
        res = await do_req_resp(self, BuyRoomBoostRequest(payment, amount))
        if isinstance(res, Error):
            return res
        return res.result

    async def tip_user(
        self,
        user_id: str,
        tip: Literal[
            "gold_bar_1",
            "gold_bar_5",
            "gold_bar_10",
            "gold_bar_50",
            "gold_bar_100",
            "gold_bar_500",
            "gold_bar_1k",
            "gold_bar_5000",
            "gold_bar_10k",
        ],
    ) -> Literal["success", "insufficient_funds"] | Error:
        """Tip a user."""
        res = await do_req_resp(self, TipUserRequest(user_id, tip))
        if isinstance(res, Error):
            return res
        return res.result

    async def get_my_outfit(self) -> GetUserOutfitRequest.GetUserOutfitResponse | Error:
        """Get the bot's outfit."""
        res = await do_req_resp(self, GetUserOutfitRequest(self.my_id))
        if isinstance(res, Error):
            return res
        return res

    async def get_inventory(self) -> GetInventoryRequest.GetInventoryResponse | Error:
        """Get the bot's inventory."""
        res = await do_req_resp(self, GetInventoryRequest())
        if isinstance(res, Error):
            return res
        return res

    async def set_outfit(self, outfit: list[Item]) -> None | Error:
        """Set the bot's outfit."""
        resp = await do_req_resp(self, SetOutfitRequest(outfit))
        if isinstance(resp, Error):
            return resp
        return None

    async def buy_item(
        self, item_id: str
    ) -> Literal["success", "insufficient_funds"] | Error:
        """Buy an item."""
        resp = await do_req_resp(self, BuyItemRequest(item_id))
        if isinstance(resp, Error):
            return resp
        return resp.result

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
    | MoveUserToRoomRequest
    | AnchorHitRequest
    | CheckVoiceChatRequest
    | InviteSpeakerRequest
    | RemoveSpeakerRequest
    | GetUserOutfitRequest
    | GetBackpackRequest
    | ChangeBackpackRequest
    | GetConversationsRequest
    | SendMessageRequest
    | GetMessagesRequest
    | LeaveConversationRequest
    | BuyVoiceTimeRequest
    | BuyRoomBoostRequest
    | TipUserRequest
    | SetOutfitRequest
    | GetInventoryRequest
    | BuyItemRequest
    | SendBulkMessageRequest
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
    | UserMovedEvent
    | VoiceEvent
    | MessageEvent
    | RoomModeratedEvent
)


Incoming = IncomingEvents | Union[tuple(r.Response for r in Outgoing.__args__)]  # type: ignore


configure_tagged_union(SessionMetadata | Error, converter)
configure_tagged_union(Incoming, converter)
configure_tagged_union(Outgoing, converter)
