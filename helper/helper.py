import json
import datetime
from enum import Enum
from credentials import (
    API_ID, 
    API_HASH, 
    PHONE_NUMBER, 
    PROXIES
)
from telethon.sync import TelegramClient
from telethon.types import *
from typing import ContextManager  # to enable static typing with the "with" statement in Python

proxy_index: int = 0

class EntityName(Enum):
    BROADCAST_CHANNEL = "broadcast_channel"
    PUBLIC_GROUP = "public_group"
    PRIVATE_GROUP = "private_group"
    DIRECT_MESSAGE = "direct_message"

class CollectionType(Enum):
    MESSAGES = "messages"
    PARTICIPANTS = "participants"


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
        if isinstance(o, datetime):  # encode datetime object to isoformat
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
        session_name: str = None    # private var
        proxy: dict = None          # private var
        
        # Detect proxy in config file
        if PROXIES is not None and len(PROXIES) > 0:  # There exists at least one proxy
            session_name = "anon_proxy"
            proxy = PROXIES[proxy_index]
            print(f"Proxy configuration detected...")
            print(f"Setting {proxy["proxy_type"]} at '{proxy["addr"]}:{proxy["port"]}'")
        else:  # No proxies are configured
            session_name = "anon"
            print(f"No proxy detected in configurations...")
        
        # Create and return a TelegramClient instance
        print(f"Creating Telegram client with session name: {session_name}")
        print("==========================================================================")
        return TelegramClient(
            session_name,
            api_id,
            api_hash,
            proxy=proxy
        )


    def __exit__(self, exc_type, exc_value, traceback):
        # Clean up resources if needed
        pass

def _get_entity_type_name(entity: Channel | Chat | User) -> str:
    """Takes an entity and returns the entity's type as a string common name.

    Args:
        Channel:  Entity of type Channel, which can be a broadcast channel or a public group
        Chat:     Entity of type Chat representing a private group chat
        User:     Entity of type User representing a direct message with another user

    Returns:
        Common name of entity as a string.
        "Broadcast Channel", "Public Group", "Private Group" or "Direct Message"
    """
    try:
        if type(entity) is Channel and entity.broadcast is True:
            return EntityName.BROADCAST_CHANNEL.value
        elif type(entity) is Channel and entity.broadcast is False:
            return EntityName.PUBLIC_GROUP.value
        elif type(entity) is Chat:
            return EntityName.PRIVATE_GROUP.value
        elif type(entity) is User:
            return EntityName.DIRECT_MESSAGE.value
    except ValueError as e:
        print("ERROR: Entity type is not Channel, Chat, or User", e)
        raise  # https://stackoverflow.com/questions/2052390/manually-raising-throwing-an-exception-in-python

def _display_entity_info(entity: Channel | Chat | User) -> None:
    """
    Displays the information of a given entity.

    Args:
        entity: An entity of type Channel, Chat, or User
    
    Returns:
        Nothing
    """
    # Format the name to have a maximum length of 20 characters
    formatted_entity_name: str = f'{_get_entity_type_name(entity)[:20]:<20}'
    print(
        f"{formatted_entity_name} - "
        f"{entity.id} "
        f"{entity.username if hasattr(entity, "username") else ''} "
        f"{entity.title if hasattr(entity, "title") else ""}"
    )

    return None

def _generate_user_keys() -> list:
    a_z_underscore = []
    numbers = []

    for i in range(97, 123, 1):  # ASCII values of a-z inclusive
        a_z_underscore.append(chr(i))

    for i in range(48, 58, 1):  # ASCII values of 0-9 inclusive
        numbers.append("_")
        numbers.append(chr(i))

    keys = []

    for i in a_z_underscore:  # ASCII values of a-z inclusive
        for j in a_z_underscore:
            keys.append(i + j)  # __, _a, _b, ..., _z, a_, aa, ab, ac, ..., az, b_, ba, ..., zz
        for j in numbers:
            keys.append(i + j)  # _1, _2, _3, ..., _9, a1, a2, a3, a4, ..., a9, b1, b2, ..., z9

    # keys: list[str] = []

    # for i in range(97, 123, 1):  # ASCII values of a-z inclusive
    #     keys.append(chr(i))

    # for i in range(48, 58, 1):  # ASCII values of 0-9 inclusive
    #     keys.append(chr(i))

    print(len(keys))

    return keys

def _rotate_proxy(client: TelegramClient) -> bool:
    """
    Disconnects from Telegram, sets the new proxy as the next proxy in the list,
    and reconnect to Telegram.

    Args:
        client: the Telegram client session whose new proxy is to be set
    
    Return:
        True if the proxy rotation was a success
    """
    # https://stackoverflow.com/questions/74412503/cannot-access-local-variable-a-where-it-is-not-associated-with-a-value-but
    global proxy_index  # Allow modification of variables declared outside of scope

    if PROXIES is None or len(PROXIES) == 0:
        print(f"No proxies configured. Skipping proxy rotation...")
        return True

    new_proxy: dict = None
    try:
        # Determine the next proxy to rotate to
        if proxy_index + 1 <= len(PROXIES) - 1:  # If not last proxy...
            proxy_index += 1  # Rotate to next proxy
        else:  # If last proxy...
            proxy_index = 0  # Rotate to first proxy
        new_proxy = PROXIES[proxy_index]
        
        # Set proxy
        print(f"Rotating to new {new_proxy["proxy_type"]} proxy at {new_proxy["addr"]}:{new_proxy["port"]}")
        client.set_proxy(new_proxy)
        
        # Disconnect and reconnect Telegram client
        client.disconnect()
        client.connect()
        if client.is_connected():
            return True
        else:
            print(f"Unknown error occured during proxy rotation...")
            return False
    except OSError:
        print(f"Failed to reconnect to Telegram during proxy rotation")
    except:
        print(f"Unknown error occured during proxy rotation")
