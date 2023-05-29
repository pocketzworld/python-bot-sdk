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
    ReactionEvent,
    SessionMetadata,
    TipReactionEvent,
    UserJoinedEvent,
    UserLeftEvent,
    UserMovedEvent,
    VoiceEvent,
)

KEEPALIVE_RATE: Final[int] = 15
READ_TIMEOUT: Final[int] = 20
SDK_PACKAGE: Final[str] = "highrise-bot-sdk"
SDK_NAME: Final[str] = "highrise-python-bot-sdk"


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
    bot_definition_list = [bot_definition] + list(extra_bot)

    definitions = []
    for bot_path, room_id, api_token in bot_definition_list:
        path.append(getcwd())
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
                print("Bot started. Waiting 10 seconds before starting the next bot.")
            await sleep(10)


async def bot_runner(bot: BaseBot, room_id: str, api_key: str) -> None:
    version = pkg_resources.get_distribution(SDK_PACKAGE).version
    async with TaskGroup() as tg:
        t = throttler(5, 5)
        while True:
            await anext(t)
            try:
                async with ClientSession() as session:
                    async with session.ws_connect(
                        environ.get("HR_WEBAPI_URL", "wss://highrise.game/web/webapi"),
                        headers={
                            "room-id": room_id,
                            "api-token": api_key,
                            "user-agent": f"{SDK_NAME}/{version}",
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
                        chat = Highrise()
                        chat.ws = ws
                        chat.tg = tg

                        if (
                            session_metadata.sdk_version is not None
                            and session_metadata.sdk_version != version
                        ):
                            print(
                                f"WARNING: The Highrise Python Bot SDK version ({version}) "
                                f"does not match the recommended version for the API ({session_metadata.sdk_version})"
                            )

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
                                case Error(message=error, rid=None):
                                    print(
                                        f"ERROR: {error} closing connection with ID: {session_metadata.connection_id}"
                                    )
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
                                case UserJoinedEvent(user=user):
                                    tg.create_task(bot.on_user_join(user))
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
            except (ConnectionResetError, WSServerHandshakeError, TimeoutError):
                # The throttler should kick in up-code.
                print("ERROR: reconnecting...")
                pass


async def throttler(
    drops: int = 10, drop_recharge: float = 1.0
) -> AsyncGenerator[Any, None]:
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


if __name__ == "__main__":
    run()
