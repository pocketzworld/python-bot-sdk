from __future__ import annotations

from asyncio import TaskGroup
from asyncio import run as arun
from asyncio import sleep
from importlib import import_module
from math import ceil
from os import environ, getcwd
from sys import path
from time import monotonic
from typing import Any, AsyncGenerator

from aiohttp import ClientSession, WebSocketError, WSServerHandshakeError
from click import argument, command

from . import BaseBot, Highrise, Incoming, converter
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
)


@command()
@argument("bot_path")
@argument("room_id")
@argument("api_token")
def run(bot_path: str, room_id: str, api_token: str) -> None:
    """Run a Highrise bot.

    Import the bot class from BOT_PATH (format: `module_path:ClassName`),
    and connect it to the room associated with the ROOM_ID
    using the provided API_TOKEN.
    """
    path.append(getcwd())
    mod, name = bot_path.split(":")
    return arun(main(getattr(import_module(mod), name)(), room_id, api_token))


async def main(bot: BaseBot, room_id: str, api_key: str) -> None:
    async with TaskGroup() as tg:
        t = throttler(5, 5)
        while True:
            await anext(t)
            try:
                async with ClientSession() as session:
                    async with session.ws_connect(
                        environ.get("HR_WEBAPI_URL", "wss://highrise.game/web/webapi"),
                        headers={"room-id": room_id, "api-token": api_key},
                    ) as ws:

                        async def send_keepalive() -> None:
                            while True:
                                await sleep(15)
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

                        bot.highrise = chat
                        tg.create_task(bot.on_start(session_metadata))
                        async for frame in ws:
                            if isinstance(frame.data, WebSocketError):
                                print("Websocket error, exiting.")
                                return
                            msg: Incoming = converter.loads(frame.data, Incoming)  # type: ignore
                            match msg:
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
            except (ConnectionResetError, WSServerHandshakeError):
                # The throttler should kick in up-code.
                print("ERROR")
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
