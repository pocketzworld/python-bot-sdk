# The Highrise Python Bot SDK

---

The Highrise Python Bot SDK is a python library for writing and running Highrise bots.

First, install the library (preferably in a virtual environment):

```shell
$ pip install highrise-bot-sdk==23.1.0b11
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

## Changelog

### 23.1.0b12 (UNRELEASED)

- Add support for getting information about user outfit if user is in the room (`self.highrise.get_user_outfit(user_id)`).

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
