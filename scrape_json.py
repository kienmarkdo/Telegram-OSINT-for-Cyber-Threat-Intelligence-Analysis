from telethon.sync import TelegramClient, helpers
from telethon.types import *
from api_keys import API_ID, API_HASH, PHONE_NUMBER
from typing import ContextManager  # to enable static typing with the "with" statement in Python
import csv
import json
import datetime
import logging

# Replace these with your own values in the "api_keys.py" file
api_id: str = str(API_ID)
api_hash: str = API_HASH
phone_number: str = PHONE_NUMBER
channel_usernames: list[str] = []

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


with TelegramClientContext() as client:
    # Connect to Telegram
    client.start(phone_number)
    
    # Channel, Chat, User types explained: https://stackoverflow.com/questions/76683847/telethon-same-entity-type-for-a-group-and-channel-in-telethon
    #                                      https://docs.telethon.dev/en/stable/concepts/chats-vs-channels.html
    # Channel (Broadcast or Public Group): channel.broadcast == True/False
    # Chat    (Private group)            : No chat.username attribute
    # User    (User/DM)                  :
    
    # Example of Group/Channel name change/migration
    # action=MessageActionChatMigrateTo(channel_id=2016527483)
    # action=MessageActionChannelMigrateFrom(title='Harry Testing', chat_id=4199887938)

    # channel_usernames.append(-4199887938)
    for dialog in client.iter_dialogs():
        # Append channel username to list, but only channels with at least 1 user
        # https://stackoverflow.com/questions/69651904/telethon-get-channel-participants-without-admin-privilages
        entity_type: Channel | User | Chat = type(dialog.entity)
        if (
            entity_type is Channel
            and dialog.entity.broadcast is True
            and dialog.entity.participants_count > 0
        ):
            print(f"CHANNEL - {dialog.entity.id} / {dialog.id} / {dialog.entity.username} / {dialog.entity.title}")
            channel_usernames.append(dialog.entity.username)
        elif entity_type is User:
            print(f"USER    - {dialog.entity.id} / {dialog.id} / {dialog.entity.username} / {dialog.name}")
        elif entity_type is Chat:  # does not have dialog.entity.username
            print(f"CHAT    - {dialog.entity.id} / {dialog.id} / {dialog.name}")
        print("------------------------------------------------------")

    # Create Broadcast Channel messages files
    for channel_username in channel_usernames:
        print(f"Collecting broadcast channels...")
        # Get the channel entity
        channel: Channel = client.get_entity(channel_username)
        print(channel_username, " | ", channel.broadcast)
        # Get all messages from oldest to newest
        # TotaList class https://docs.telethon.dev/en/stable/modules/helpers.html
        # Message class https://tl.telethon.dev/constructors/message.html
        #               https://docs.telethon.dev/en/v2/concepts/messages.html
        # messages: helpers.TotalList = client.get_messages(channel, limit=20)

        # # Define the JSON file name
        # json_file_name = f'messages_json_{channel_username}.json'

        # # Convert the Message object to JSON
        # messages_list = []
        # for message in messages:
        #     if type(message) is Message:
        #         message_dict = message.to_dict()
        #         messages_list.append(message_dict)

        # with open(json_file_name, 'w', encoding='utf-8') as json_file:
        #     json.dump(messages_list, json_file, cls=JSONEncoder)

        # print(f'Messages exported to {json_file_name}')
    
    # Create Public Groups Channel files


