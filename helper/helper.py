"""
Contains core helper functions required for the Telegram scraper to work.
"""

import datetime
import json
import logging
import random
import time
from enum import Enum
from typing import (
    ContextManager,
)  # to enable static typing with the "with" statement in Python

from requests import get
from telethon.sync import TelegramClient
from telethon.types import *

from configs import API_HASH, API_ID, PROXIES

# Default values for CLI argument variables
max_messages: int = 2500  # max number of messages to collect
min_throttle: int = 1
max_throttle: int = 10
export_to_es: bool = False


class EntityName(Enum):
    BROADCAST_CHANNEL = "broadcast_channel"
    PUBLIC_GROUP = "public_group"
    PRIVATE_GROUP = "private_group"
    DIRECT_MESSAGE = "direct_message"


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
    This class faciliates static typing when using the "with" statement to start a TelegramClient
    and performs necessary setup steps prior to instantiating a TelegramClient, such as setting up
    available proxies.

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
        session_name: str = None  # private var
        proxy: dict = None  # private var

        # Display machine's public IP address (https://stackoverflow.com/a/36205547)
        public_ip: str = get("https://api.ipify.org").content.decode("utf8")
        logging.info(f"Collection public IP address '{public_ip}'")

        # Detect proxy in config file
        if PROXIES is not None and len(PROXIES) > 0:  # There exists at least one proxy
            session_name = "anon_proxy"
            proxy = PROXIES[0]
            logging.info(f"Proxy configuration detected...")
            logging.info(
                f"Setting {proxy['proxy_type']} proxy at '{proxy['addr']}:{proxy['port']}'"
            )
        else:  # No proxies are configured
            session_name = "anon"
            logging.info(f"No proxy detected in configurations...")

        # Create and return a TelegramClient instance
        logging.info(f"Creating Telegram client with session name: {session_name}")
        logging.info(
            "=========================================================================="
        )
        return TelegramClient(session_name, api_id, api_hash, proxy=proxy)

    def __exit__(self, exc_type, exc_value, traceback):
        # Clean up resources if needed
        pass


def setup() -> bool:
    """
    Execute required setup operations prior to running a collection.

    Setup can include, but are not limited to:
    - Creating or connecting to a local database
    - Setup logging configs

    Returns True if the setup completed successfully.
    """
    pass


def get_entity_type_name(entity: Channel | Chat | User) -> str:
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
        logging.error("ERROR: Entity type is not Channel, Chat, or User", e)
        raise  # https://stackoverflow.com/questions/2052390/manually-raising-throwing-an-exception-in-python


def get_entity_info(entity: Channel | Chat | User) -> str:
    """
    Displays the information of a given entity.

    Args:
        entity: An entity of type Channel, Chat, or User

    Returns:
        Nothing
    """
    # Format the name to have a maximum length of 20 characters
    # formatted_entity_name: str = f'{get_entity_type_name(entity)[:20]:<20}'

    result: str = (
        f"{get_entity_type_name(entity)} - "
        f"{entity.id} "
        f"{entity.username if hasattr(entity, 'username') else ''} "
        f"{entity.title if hasattr(entity, 'title') else ''}"
    )

    return result


def generate_user_keys() -> list:
    """
    Generates keys to search users as part of users collection.
    """
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
            keys.append(
                i + j
            )  # __, _a, _b, ..., _z, a_, aa, ab, ac, ..., az, b_, ba, ..., zz
        for j in numbers:
            keys.append(
                i + j
            )  # _1, _2, _3, ..., _9, a1, a2, a3, a4, ..., a9, b1, b2, ..., z9

    # keys: list[str] = []

    # for i in range(97, 123, 1):  # ASCII values of a-z inclusive
    #     keys.append(chr(i))

    # for i in range(48, 58, 1):  # ASCII values of 0-9 inclusive
    #     keys.append(chr(i))

    print(len(keys))

    return keys


def rotate_proxy(client: TelegramClient) -> bool:
    """
    Disconnects from Telegram, sets the new proxy as the next proxy in the list,
    and reconnect to Telegram.

    Args:
        client: the Telegram client session whose new proxy is to be set

    Return:
        True if the proxy rotation was a success
    """

    if PROXIES is None or len(PROXIES) == 0:
        logging.debug(f"No proxies configured. Skipping proxy rotation...")
        return True

    new_proxy: dict = None
    try:
        # Determine the next proxy to rotate to
        new_proxy = random.choice(PROXIES)

        # Set proxy
        logging.info(f"[+] Rotating proxy...")
        logging.info(
            f"[+] Setting {new_proxy['proxy_type']} proxy at '{new_proxy['addr']}:{new_proxy['port']}'"
        )
        client.set_proxy(new_proxy)

        # Disconnect and reconnect Telegram client
        client.disconnect()
        client.connect()
        if client.is_connected():
            return True
        else:
            logging.error(f"[-] Unknown error occured during proxy rotation...")
            return False
    except OSError:
        logging.critical(f"[-] Failed to reconnect to Telegram during proxy rotation")
    except:
        logging.critical(f"[-] Unknown error occured during proxy rotation")


def throttle():
    """
    Delays code execution.

    Used to throttle API calls to prevent API flooding, as Telegram could
    ban the current account for bot behaviour or spamming. This function
    throttles the code by a random number of seconds between a min_throttle
    time and a max_throttle time. By default, the min. is 1 second and the
    max. is 10 seconds. However, the values can be overriden in the CLI
    with `python scrape.py ... --throttle-time <min_time> <max_time>`
    """
    min_throttle_ms: float = min_throttle * 1000  # 1 second is 1000 milliseconds
    max_throttle_ms: float = max_throttle * 1000

    # Generate a random delay between min_throttle_ms and max_throttle_ms
    delay_ms = random.uniform(min_throttle_ms, max_throttle_ms)

    # Convert milliseconds to seconds
    delay_sec = delay_ms / 1000

    logging.info(f"Delaying execution: {delay_sec} second(s)")
    logging.info(f"")
    time.sleep(delay_sec)

    return


def update_argument_variables(
    new_max_messages, new_min_throttle, new_max_throttle, new_export_to_es
):
    """
    Update argument variables with values from CLI arguments.

    For updated values, must reference them with "helper.VARIABLE".
    For example, `helper.max_messages` will work.
    """
    global max_messages, min_throttle, max_throttle, export_to_es
    max_messages = new_max_messages
    min_throttle = new_min_throttle
    max_throttle = new_max_throttle
    export_to_es = new_export_to_es
