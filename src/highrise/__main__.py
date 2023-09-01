from __future__ import annotations

from asyncio import run as arun
from asyncio import sleep
from asyncio.exceptions import TimeoutError
from importlib import import_module
from math import ceil
from os import environ, getcwd
from sys import path
from time import monotonic
from typing import Any, AsyncGenerator, Final

import pkg_resources
from aiohttp import ClientSession, WebSocketError, WSMsgType, WSServerHandshakeError
from attrs import define
from click import argument, command, option
from quattro import TaskGroup

from . import BaseBot, Highrise, Incoming, IncomingEvents, converter
from .models import (
    ChannelEvent,
    ChatEvent,
    EmoteEvent,
    Error,
    MessageEvent,
    ReactionEvent,
    RoomModeratedEvent,
    SessionMetadata,
    TipReactionEvent,
    UserJoinedEvent,
    UserLeftEvent,
    UserMovedEvent,
    VoiceEvent,
)
from .models_control import (
    ControlEvent,
    ControlSessionMetadata,
    InstanceStartedEvent,
    InstanceStoppedEvent,
)
from .models_control import converter as control_converter
from .webapi import WebAPI

KEEPALIVE_RATE: Final = 15
READ_TIMEOUT: Final = 20
SDK_PACKAGE: Final = "highrise-bot-sdk"
SDK_NAME: Final = "highrise-python-bot-sdk"
VERSION: Final = pkg_resources.get_distribution(SDK_PACKAGE).version


@define
class BotDefinition:
    bot: BaseBot
    room_id: str
    api_token: str


@command()
@argument("bot_definition", type=(str, str, str))
@option("--extra_bot", type=(str, str, str), multiple=True)
def run(
    bot_definition: tuple[str, str, str], extra_bot: list[tuple[str, str, str]]
) -> None:
    """Run a Highrise bot.

    Import the bot class from BOT_PATH (format: `module_path:ClassName`),
    and connect it to the room associated with the ROOM_ID
    using the provided API_TOKEN.

    Multiple bots can be run at once by providing multiple bot definitions.
    """
    path.append(getcwd())
    if bot_definition[1].startswith("3d/"):
        room_id = bot_definition[1][3:]
        bot_path = bot_definition[0]
        mod, name = bot_path.split(":")
        bot_cls = getattr(import_module(mod), name)
        return arun(control_runner(bot_cls, room_id, bot_definition[2]))
    else:
        bot_definition_list = [bot_definition] + list(extra_bot)

        definitions = []
        for bot_path, room_id, api_token in bot_definition_list:
            mod, name = bot_path.split(":")
            definitions.append(
                BotDefinition(getattr(import_module(mod), name)(), room_id, api_token)
            )

        return arun(main(definitions))


async def main(definitions: list[BotDefinition]) -> None:
    async with TaskGroup() as tg:
        for bot_definition in definitions:
            bot = bot_definition.bot
            room_id = bot_definition.room_id
            api_key = bot_definition.api_token

            tg.create_task(bot_runner(bot, room_id, api_key))
            if len(definitions) > 1:
                print("Bot started. Waiting 1 second(s) before starting the next bot.")
            await sleep(1)


async def bot_runner(bot: BaseBot, room_id: str, api_key: str) -> None:
    async with TaskGroup() as tg:
        t = throttler(5, 5)
        while True:
            await anext(t)
            await bot.before_start(tg)
            try:
                async with ClientSession() as session:
                    base_url = environ.get(
                        "HR_BOTAPI_URL",
                        "wss://highrise.game/web/botapi",
                    )
                    async with session.ws_connect(
                        f"{base_url}{gather_subscriptions(bot)}",
                        headers={
                            "room-id": room_id,
                            "api-token": api_key,
                            "user-agent": f"{SDK_NAME}/{VERSION}",
                        },
                    ) as ws:

                        async def send_keepalive() -> None:
                            while True:
                                await sleep(KEEPALIVE_RATE)
                                try:
                                    await ws.send_json({"_type": "KeepaliveRequest"})
                                except ConnectionResetError:
                                    # We don't want to close the entire TaskGroup.
                                    return

                        ka_task = tg.create_task(send_keepalive())
                        session_metadata: SessionMetadata | Error = converter.loads(
                            await ws.receive_str(), SessionMetadata | Error  # type: ignore
                        )
                        if isinstance(session_metadata, Error):
                            print(f"ERROR: {session_metadata}")
                            ka_task.cancel()
                            return
                        bot_id = str(session_metadata.user_id)
                        webapi = WebAPI()
                        chat = Highrise()
                        chat.my_id = bot_id
                        chat.ws = ws
                        chat.tg = tg

                        if (
                            session_metadata.sdk_version is not None
                            and session_metadata.sdk_version != VERSION
                        ):
                            print(
                                f"WARNING: The Highrise Python Bot SDK version ({VERSION}) "
                                f"does not match the recommended version for the API ({session_metadata.sdk_version})"
                            )

                        bot.webapi = webapi
                        bot.highrise = chat
                        tg.create_task(bot.on_start(session_metadata))
                        while True:
                            frame = await ws.receive(READ_TIMEOUT)
                            if frame.type in [WSMsgType.CLOSE, WSMsgType.CLOSED]:
                                print(
                                    f"ERROR connection with ID: {session_metadata.connection_id} closed."
                                )
                                # Close frame
                                ka_task.cancel()
                                return
                            if isinstance(frame.data, WebSocketError):
                                print("Websocket error, exiting.")
                                return
                            msg: IncomingEvents = converter.loads(frame.data, Incoming)  # type: ignore
                            match msg:
                                case Error(
                                    message=error,
                                    rid=None,
                                    do_not_reconnect=dont_reconnect,
                                ):
                                    print(
                                        f"ERROR: {error} closing connection with ID: {session_metadata.connection_id}"
                                    )
                                    if dont_reconnect:
                                        ka_task.cancel()
                                        return
                                    raise ConnectionResetError
                                case object(rid=rid) if hasattr(msg, "rid"):  # type: ignore
                                    if rid not in chat._req_id_registry:
                                        continue
                                    chat._req_id_registry.pop(rid).put_nowait(msg)
                                case ChatEvent(
                                    message=message, user=user, whisper=whisper
                                ):
                                    if user.id == bot_id:
                                        continue
                                    if whisper:
                                        tg.create_task(bot.on_whisper(user, message))
                                    else:
                                        tg.create_task(bot.on_chat(user, message))
                                case ChannelEvent(
                                    sender_id=channel_sender_id, msg=message, tags=tags
                                ):
                                    tg.create_task(
                                        bot.on_channel(
                                            channel_sender_id, message, set(tags)
                                        )
                                    )
                                case EmoteEvent(
                                    user=user, emote_id=emote_id, receiver=receiver
                                ):
                                    tg.create_task(
                                        bot.on_emote(user, emote_id, receiver)
                                    )
                                case ReactionEvent(
                                    user=user, reaction=reaction, receiver=receiver
                                ):
                                    tg.create_task(
                                        bot.on_reaction(user, reaction, receiver)
                                    )
                                case UserJoinedEvent(user=user, position=pos):
                                    tg.create_task(bot.on_user_join(user, pos))
                                case UserLeftEvent(user=user):
                                    tg.create_task(bot.on_user_leave(user))
                                case TipReactionEvent(
                                    sender=sender, receiver=receiver, item=tip
                                ):
                                    tg.create_task(bot.on_tip(sender, receiver, tip))
                                case UserMovedEvent(user=user, position=pos):
                                    tg.create_task(bot.on_user_move(user, pos))
                                case VoiceEvent(users=users, seconds_left=seconds_left):
                                    tg.create_task(
                                        bot.on_voice_change(users, seconds_left)
                                    )
                                case MessageEvent(
                                    user_id=user_id,
                                    conversation_id=conv_id,
                                    is_new_conversation=is_new,
                                ):
                                    tg.create_task(
                                        bot.on_message(user_id, conv_id, is_new)
                                    )
                                case RoomModeratedEvent(
                                    moderatorId=moderator_id,
                                    targetUserId=target_user_id,
                                    moderationType=moderation_type,
                                    duration=duration,
                                ):
                                    tg.create_task(
                                        bot.on_moderate(
                                            moderator_id,
                                            target_user_id,
                                            moderation_type,
                                            duration,
                                        )
                                    )
            except (ConnectionResetError, WSServerHandshakeError, TimeoutError):
                # The throttler should kick in up-code.
                print("ERROR: reconnecting...")
                pass


async def throttler(
    drops: int = 10, drop_recharge: float = 1.0
) -> AsyncGenerator[Any, None]:
    """Connect throttler."""
    next_full = monotonic()
    while True:
        now = monotonic()
        if next_full <= now:
            # We're full.
            next_full = now + drop_recharge
            yield
        else:
            missing_drops = ceil((next_full - now) / drop_recharge)
            effective_drops = drops - missing_drops
            if effective_drops > 0:
                effective_drops -= 1
                next_full = next_full + drop_recharge
                yield
            else:
                to_wait = next_full - ((drops - 1) * drop_recharge) - now
                await sleep(to_wait)
                next_full = next_full + drop_recharge
                yield None


def gather_subscriptions(bot: BaseBot) -> str:
    method_map: dict[str, str] = {
        "on_chat": "chat",
        "on_whisper": "chat",
        "on_emote": "emote",
        "on_reaction": "reaction",
        "on_user_join": "user_joined",
        "on_user_leave": "user_left",
        "on_user_move": "user_moved",
        "on_tip": "tip_reaction",
        "on_voice_change": "voice",
        "on_channel": "channel",
        "on_message": "message",
        "on_moderate": "moderation",
    }

    subscriptions = {
        event_name
        for method_name, event_name in method_map.items()
        if getattr(BaseBot, method_name) != getattr(type(bot), method_name)
    }

    return f"?events={','.join(subscriptions)}" if subscriptions else ""


async def control_runner(bot_cls: type[BaseBot], room_id: str, api_key: str) -> None:
    """Run a control websocket handler."""
    async with TaskGroup() as tg:
        instances_to_bots = {}
        while True:
            async with ClientSession() as session:
                url = environ.get("HR_WEBAPI_URL", "wss://highrise.game/web/botapi")
                url = f"{url}/control/{room_id}"
                async with session.ws_connect(
                    url,
                    headers={
                        "api-token": api_key,
                        "user-agent": f"{SDK_NAME}/{VERSION}",
                    },
                ) as ws:

                    async def send_keepalive() -> None:
                        while True:
                            await sleep(KEEPALIVE_RATE)
                            try:
                                await ws.send_json({"_type": "KeepaliveRequest"})
                            except ConnectionResetError:
                                # We don't want to close the entire TaskGroup.
                                return

                    ka_task = tg.create_task(send_keepalive())
                    session_metadata: ControlSessionMetadata | Error = control_converter.loads(
                        await ws.receive_str(), ControlSessionMetadata | Error  # type: ignore
                    )
                    if isinstance(session_metadata, Error):
                        print(f"ERROR: {session_metadata}")
                        ka_task.cancel()
                        return
                    for instance_id in session_metadata.instance_ids:
                        if instance_id in instances_to_bots:
                            # Could be in here from before, if the control socket
                            # gets reset.
                            continue
                        print(f"Starting bot for instance {instance_id}")
                        bot_task = tg.create_task(
                            bot_runner(bot_cls(), f"3d/{instance_id}", api_key)
                        )
                        instances_to_bots[instance_id] = bot_task
                    while True:
                        frame = await ws.receive(READ_TIMEOUT)
                        if frame.type in [WSMsgType.CLOSE, WSMsgType.CLOSED]:
                            print(
                                f"ERROR connection with ID: {session_metadata.connection_id} closed."
                            )
                            ka_task.cancel()
                            return
                        if isinstance(frame.data, WebSocketError):
                            print("Websocket error, exiting.")
                            ka_task.cancel()
                            return
                        msg: ControlEvent = control_converter.loads(
                            frame.data, ControlEvent
                        )
                        match msg:
                            case InstanceStartedEvent(
                                instance_id=instance_id
                            ) if instance_id not in instances_to_bots:
                                bot_task = tg.create_task(
                                    bot_runner(bot_cls(), f"3d/{instance_id}", api_key)
                                )
                                instances_to_bots[instance_id] = bot_task
                            case InstanceStoppedEvent(
                                instance_id=instance_id
                            ) if instance_id in instances_to_bots:
                                instances_to_bots.pop(instance_id).cancel()


if __name__ == "__main__":
    run()
