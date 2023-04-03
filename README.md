# The Highrise Python Bot SDK

---

The Highrise Python Bot SDK is a python library for writing and running Highrise bots.

First, install the library (preferably in a virtual environment):

```shell
$ pip install highrise-bot-sdk==23.1.0b2
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
