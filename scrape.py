from telethon.sync import TelegramClient, helpers
from telethon.types import *

import csv
import json
import datetime
import logging

from helper.helper import TelegramClientContext, JSONEncoder
from api_keys import API_ID, API_HASH, PHONE_NUMBER

# Replace these with your own values in the "api_keys.py" file
api_id: str = str(API_ID)
api_hash: str = API_HASH
phone_number: str = PHONE_NUMBER
channel_usernames: list[str] = []




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
        messages: helpers.TotalList = client.get_messages(channel, limit=20)

        # Define the JSON file name
        json_file_name = f'messages_json_{channel_username}.json'

        # Convert the Message object to JSON
        messages_list = []
        for message in messages:
            if type(message) is Message:
                message_dict = message.to_dict()
                messages_list.append(message_dict)

        with open(json_file_name, 'w', encoding='utf-8') as json_file:
            json.dump(messages_list, json_file, cls=JSONEncoder, indent=2)

        print(f'Messages exported to {json_file_name}')
    
    # Create Public Groups Channel files


