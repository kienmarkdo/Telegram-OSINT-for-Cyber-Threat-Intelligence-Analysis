import json
import datetime
from api_keys import API_ID, API_HASH, PHONE_NUMBER
from telethon.sync import TelegramClient
from typing import ContextManager  # to enable static typing with the "with" statement in Python


class JSONEncoder(json.JSONEncoder):
    """
    Encodes objects that are not parsable by JSON into objects that can be parsed by JSON.

    For example:
    - Cannot insert datetime object into JSON, so this class converts the datetime object
    into ISO format.
    - Cannot insert byte object into JSON (i.e.: image or video files), so it is converted
        to a normal string.
    """
    def default(self, o):
        if isinstance(o, datetime.datetime):  # encode datetime object to isoformat
            return o.isoformat()
        if isinstance(o, bytes):  # encode byte data into string
            return str(o)
        return super().default(o)

class TelegramClientContext(ContextManager[TelegramClient]):
    """
    This class faciliates static typing when using the "with" statement to start a TelegramClient.

    Normally, starting a TelegramClient would be done using async/await as follows:
    ```
    # Create a TelegramClient
    client = TelegramClient('anon', api_id, api_hash)

    async def main():
        # Connect to Telegram
        await client.start(phone_number)  # await is needed to run the method asynchronously

        # Get the channel entity
        channel = await client.get_entity(channel_username)  # await is needed to run the method asynchronously
        ...

    if __name__ == '__main__':
        client.loop.run_until_complete(main())
        client.disconnect()
    ```
    To avoid using the "await" statement for network functions (i.e.: get_messages, get_entity...) 
    TelegramClient can also be started using the "with" clause:

    ```
    with TelegramClient(...) as client:
        print(client.get_me().username)
        #     ^ notice the lack of await, or loop.run_until_complete().
        #       Since there is no loop running, this is done behind the scenes.
        #
        message = client.send_message('me', 'Hi!')
        client.run_until_disconnected()
    ```
    However, the "client" object does not have any static typing. When hovering over
    the "client" word, Python would not provide any hints as to what methods the "client"
    object has.

    By using a ContextManager the TelegramClient object and self defining the __enter__ 
    and __exit__ methods, it allows for static typing when using the "with" statement.
    """
    def __enter__(self) -> TelegramClient:
        api_id = API_ID
        api_hash = API_HASH
        phone_number = PHONE_NUMBER
        
        # Create and return a TelegramClient instance
        return TelegramClient('anon', api_id, api_hash)

    def __exit__(self, exc_type, exc_value, traceback):
        # Clean up resources if needed
        pass