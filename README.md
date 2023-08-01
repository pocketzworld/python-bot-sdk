# The Highrise Python Bot SDK

---

The Highrise Python Bot SDK is a python library for writing and running Highrise bots.

First, install the library (preferably in a virtual environment):

```shell
$ pip install highrise-bot-sdk==23.3.1
```

In the [`Settings` section of the Highrise website](https://highrise.game/account/settings), create a bot and generate the API token. You'll need the token to start your bot later.
You will also need a room ID for your bot to connect to; the room needs to be owned by you or your bot user needs to have designer rights to enter it.

Open a new file, and paste the following to get started (into `mybot.py` for example):

```python
from highrise import BaseBot

class Bot(BaseBot):
    pass
```

Override methods from `BaseBot` as needed.

When you're ready, run the bot from the terminal using the SDK, giving it the Python path to the Bot class:

```
$ highrise mybot:Bot <room ID> <API token>
```
Ñ
## Changelog

### 23.3.1 (UNRELEASED)

- Add position to `on_user_join` handle, this will allow bots to know what the user's location is on room join.

### 23.3.0 (2023-07-17)
- Add support for bot to get its inventory(`self.highrise.get_inventory()`). It returns list of items that bot has in its inventory.
- Add support for bot to get its own outfit(`self.highrise.get_outfit()`). It returns list of items that bot has equipped.
- Add support for bot to change his outfit(`self.highrise.set_outfit(outfit)`). It takes list of items that bot should equip. Bot can equip free items or items in his own inventory.
- Add support for buying items as a bot(`self.highrise.buy_item(item_id)`). It takes item id and attempts to buy this item from highrise. Note bot can only use his own wallet to buy items. Some items are not available for purchase. Take note that bots can only equip those items and not trade them, there is no use in buying items more than one time.
- Added items and grabs helper methods for Highrise Web API: 
    - `self.webapi.get_item()`: Fetches a specific item by id.
    - `self.webapi.get_items()`: Retrieves a list of items.
    - `self.webapi.get_grab()`: Fetches a specific grab by id.
    - `self.webapi.get_grabs()`: Retrieves a list of rooms.

### 23.2.0 (2023-07-5)
- Add support to tip users in the room (`self.highrise.tip_user(user_id, amount)`). Amount needs to be expressed in gold bars. Possible values are:
  "gold_bar_1",
  "gold_bar_5",
  "gold_bar_10",
  "gold_bar_50",
  "gold_bar_100",
  "gold_bar_500",
  "gold_bar_1k",
  "gold_bar_5000",
  "gold_bar_10k",

### 23.1.0b16 (2023-07-03)
- Hotfix web-api models issue.

### 23.1.0b15 (2023-06-30)
- Hotfix dependency issue with cattrs.

### 23.1.0b14 (2023-06-30)
- Added Highrise Web API Support: Introduced helper methods within the BaseBot class accessible through `self.webapi`. This enables easy communication with the Highrise Web API to gain access to public information about the game. Included are the following methods:
    - `self.webapi.get_user()`: Fetches a specific user by id.
    - `self.webapi.get_users()`: Retrieves a list of users.
    - `self.webapi.get_room()`: Fetches a specific room by id.
    - `self.webapi.get_rooms()`: Retrieves a list of rooms.
    - `self.webapi.get_post()`: Fetches a specific post by id.
    - `self.webapi.get_posts()`: Retrieves a list of posts.
- Add a method to buy room boost for a room (`self.highrise.buy_room_boost(payment_type, amount)`).
- Add a method to buy voice time for a room (`self.highrise.buy_voice_time(payment_type)`).
- Both methods support several payment options `bot_wallet_only`, `bot_wallet_priority`, `user_wallet_only` allowing bot to use its own wallet or user's wallet to pay for the purchase. Or to try to prioritize bot's wallet over user's wallet.
- Get wallet method will now return room_boost_tokens and voice_tokens if bot has any.

### 23.1.0b13 (2023-06-19)

- Add optional hook that is triggered on bot startup (`async def before_start(self) -> None:`). All bot initialization should be done here, and most things like reading from files, setting up database connections can be done here instead of on_connect.
- Enable support for bot to get access to inbox features, direct conversation and ability to respond to messages if messaged by user.
- Add handler that is triggered when bot received message from user (`async def on_message(user_id, conversation_id, is_new_conversation)`). It is triggered when user sends in game message to bot, using either new conversation or existing conversation. If this is new conversation `is_new_conversation` will be set to True, otherwise it will be set to False.
- Add support for bot to send message to user (`self.highrise.send_message(conversation_id, message, type, room_id)`). This can be only used on existing conversation, and will fail if conversation is not found. Bot can only send two types of messages, `text` and `invite`. Text is the normal message in which bot can send text to user, and invite is used to invite user to room. If type is invite then room_id must be provided in order to generate room invite for users.
- Add support for bot to list conversations (`self.highrise.get_conversations(not_joined, last_id)`). This will return list of conversations opened with bot, there are two types of conversations, the ones bot has joined and unjoined. If `not_joined` is set to True then only unjoined conversations will be returned, otherwise only joined conversations will be returned. Response will also return number of unjoined conversations that bot has. This method will return at most 20 conversations ordered from newest to the oldest,  If `last_id` is provided then only conversations that are older than specified id will be returned.
- Add support for bot to list messages in conversation (`self.highrise.get_messages(conversation_id, last_id)`). This will return list of messages in conversation, at most 20 messages will be returned ordered from newest to the oldest. If `last_id` is provided then only messages that are older than specified id will be returned. conversation_id must be from conversation that is available to bot.
- Add support for bot to leave conversation (`self.highrise.leave_conversation(conversation_id)`). This will leave conversation, and bot will no longer receive messages from user in that conversation or have that conversation in his list. 

### 23.1.0b12 (2023-06-06)

- Add support for getting information about user outfit if user is in the room (`self.highrise.get_user_outfit(user_id)`).
- Enable automatic filtering of events based on bot usage.

### 23.1.0b11 (2023-05-29)

- Add support for running multiple bots in the same process.
- Add additional room information such as owner's id and room name to session metadata on connection
- Add support for voice chat management and info, bots can now get information about voice chat in the room if bot owner has privileges to get info or manage bots in the room (`self.highrise.get_voice_status()`)
- Add support for bots to invite users to voice chat (`self.highrise.add_user_to_voice(user_id)`
- Add support for bots to remove users from voice chat (`self.highrise.remove_user_from_voice(user_id)`
- Add handler that is triggered when state of voice in the room changed(`self.on_voice_change(users, seconds_left)`


### 23.1.0b10 (2023-05-12)

- Fix bug with handling of error responses.

### 23.1.0b9 (2023-05-11)

- Add support for moving bot to an anchor in walk_to command (`self.highrise.walk_to(AnchorPosition)`).
- Change the way client ws messages are parsed, return error if message is not valid json.

### 23.1.0b8 (2023-04-25)

- Add support for moving users to another room (`self.highrise.move_user_to_room(user_id, room_id)`).
- Add handler that is triggered when user moves inside a room  (`self.on_user_move(user_id, position)`).) 
- Expand session_metadata information with information about client rates
- Expand session_metadata with information about sdk versions if client uses skd

### 23.1.0b6 (2023-04-17)

- Add Python 3.10 support

### 23.1.0b5 (2023-04-11)

- Add support for getting room permissions for users (`self.highrise.get_room_privilege(user_id)`).
- Add support changing room permissions for users (`self.highrise.set_room_privilege(user_id, privilege)`).
- Add support for moderating rooms (`self.highrise.moderate_room(user_id, moderate_action, action_length)`). 
- Rework how keepalive is handled

### 23.1.0b4 (2023-04-05)

- Methods mapping to requests with empty responses (`chat`, `send_whisper`, `send_emote`, `react`, `set_indicator`, `send_channel`, `walk_to`, `teleport`) now return `None`, and raise a `highrise.ResponseError` on an error response.
- Fix the emote API.
- Internally rework request handling to improve robustness.

### 23.1.0b3 (2023-04-03)

- Fix the chatting API.

### 23.1.0b2 (2023-04-03)

- Add support for receiving and sending reactions.
- Fix support for hidden channels.
- Migrate to the new message for avatars leaving.
- Improve concurrency when awaiting bot methods.
- Fix issues with teleporting users.
- Fix issues with user coordinates.
- Add support for fetching the bot wallet (`self.highrise.get_wallet()`).

### 23.1.0b1 (2023-03-28)

- Add support for emotes and hidden channel messages.

### 23.1.0b0 (2023-03-10)

- Initial beta release.
