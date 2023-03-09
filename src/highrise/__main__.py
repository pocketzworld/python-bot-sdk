from __future__ import annotations

from asyncio import TaskGroup
from asyncio import run as arun
from asyncio import sleep
from importlib import import_module
from json import loads
from math import ceil
from os import environ, getcwd
from sys import path
from time import monotonic
from typing import Any, AsyncGenerator

from aiohttp import ClientSession, WebSocketError, WSServerHandshakeError
from cattrs.preconf.json import make_converter
from cattrs.strategies import configure_tagged_union
from click import argument, command

from . import BaseBot, Highrise
from .models import ChatEvent, Error, SessionMetadata

converter = make_converter()
configure_tagged_union(SessionMetadata | Error, converter)


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
                        session_metadata = converter.loads(
                            await ws.receive_str(), SessionMetadata | Error
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
                        await bot.on_start(session_metadata)
                        async for frame in ws:
                            if isinstance(frame.data, WebSocketError):
                                print("Websocket error, exiting.")
                                return
                            msg = loads(frame.data)
                            match msg:
                                case {"rid": rid} if rid is not None and int(
                                    rid
                                ) in chat._req_id_registry:
                                    queue = chat._req_id_registry.pop(int(rid))
                                    queue.put_nowait(msg["content"])
                                case {
                                    "_type": "ChatEvent",
                                    "message": message,
                                    "user": {"id": user_id, "username": username},
                                    "whisper": whisper,
                                }:
                                    if user_id == bot_id:
                                        continue
                                    if bool(whisper):
                                        tg.create_task(
                                            bot.on_whisper(user_id, username, message)
                                        )
                                    else:
                                        tg.create_task(
                                            bot.on_chat(user_id, username, message)
                                        )
                                case {
                                    "_type": "UserJoinedEvent",
                                    "user": {"id": user_id, "username": username},
                                }:
                                    await bot.on_user_join(user_id, username)
                                case {
                                    "_type": "TipReactionEvent",
                                    "user": tip_sender,
                                    "receiver": tip_receiver,
                                    "tip": tip,
                                }:
                                    await bot.on_tip(
                                        tip_sender["id"],
                                        tip_sender["username"],
                                        tip_receiver["id"],
                                        tip_receiver["username"],
                                        tip["type"],
                                        int(tip["amount"]),
                                    )
            except (ConnectionResetError, WSServerHandshakeError):
                # The throttler should kick in up-code.
                print("ERROR")
                pass


async def throttler(
    drops: int = 10, drop_recharge: float = 5.0
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
