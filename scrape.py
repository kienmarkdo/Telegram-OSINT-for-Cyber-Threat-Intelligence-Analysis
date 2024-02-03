from telethon.sync import helpers
from telethon.types import *

import json
import os
import datetime
import logging  # #2 TODO: Convert print statements to proper logging to a file
from enum import Enum

from helper.helper import TelegramClientContext, JSONEncoder
from api_keys import API_ID, API_HASH, PHONE_NUMBER

# Replace these with your own values in the "api_keys.py" file
api_id: str = str(API_ID)
api_hash: str = API_HASH
phone_number: str = PHONE_NUMBER

entity_ids: list[str] = []


class EntityName(Enum):
    BROADCAST_CHANNEL = "broadcast_channel"
    PUBLIC_GROUP = "public_group"
    PRIVATE_GROUP = "private_group"
    DIRECT_MESSAGE = "direct_message"


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


def collect_messages(entity_id: str) -> bool:
    """
    Performs a collection of all messages in a given entity.
    An entity can be a Channel (Broadcast Channel or Public Group),
    a User (direct message), Chat (private group)

    Args:
        entity_id: ID of an entity of type Channel, User, or Chat

    Return:
        True if collection was successful
    """
    try:
        # Retrieve entity by its ID
        entity: Channel | User | Chat = client.get_entity(entity_id)
        print("Collection in progress...")
        _display_entity_info(entity)
        
        # Collect messages from entity
        messages_collected: helpers.TotalList = client.get_messages(entity, limit=1)  # TODO: Limit here

        # Define the JSON file name
        json_file_name = f"output_{_get_entity_type_name(entity)}_{entity_id}/messages_{entity_id}.json"

        # Check if directory exists, create it if necessary
        os.makedirs(os.path.dirname(json_file_name), exist_ok=True)

        # Convert the Message object to JSON
        messages_list = []
        for message in messages_collected:
            if type(message) in (Message, MessageService):
                message_dict = message.to_dict()
                messages_list.append(message_dict)
        
        # Write messages in JSON object to JSON file
        with open(json_file_name, "w", encoding="utf-8") as json_file:
            json.dump(messages_list, json_file, cls=JSONEncoder, indent=2)

        print(f"Messages exported to {json_file_name}")
        return True
    except:
        print(f"Collection failed")
        raise


# TODO: Collect others...

with TelegramClientContext() as client:
    # Connect to Telegram
    client.start(phone_number)

    # Channel, Chat, User types explained: https://stackoverflow.com/questions/76683847/telethon-same-entity-type-for-a-group-and-channel-in-telethon
    #                                      https://docs.telethon.dev/en/stable/concepts/chats-vs-channels.html
    # Channel (Broadcast or Public Group): channel.broadcast == True/False
    # Chat    (Private group)            : No chat.username attribute
    # User    (User/DM)                  : No user.title attribute

    # Example of Group/Channel name change/migration
    # action=MessageActionChatMigrateTo(channel_id=2016527483)
    # action=MessageActionChannelMigrateFrom(title='Harry Testing', chat_id=4199887938)
    # NOTE: Merge two JSONs or let Neo4j do that?

    # Iterate through all inboxes aka dialogs (DMs, public groups, private groups, broadcast channels)
    # https://docs.telethon.dev/en/stable/quick-references/client-reference.html#dialogs
    # https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.dialogs.DialogMethods.iter_dialogs
    for dialog in client.iter_dialogs():

        entity: Channel | User | Chat = dialog.entity
        entity_ids.append(entity.id)

        for id in entity_ids:
            collect_messages(id)
            print("------------------------------------------------------")