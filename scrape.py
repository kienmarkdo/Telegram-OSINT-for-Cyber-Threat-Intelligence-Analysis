import requests
from telethon.sync import helpers
from telethon.types import *
from telethon import functions

import json
import os
import logging  # #2 TODO: Convert print statements to proper logging to a file

from helper.helper import (
    TelegramClientContext,
    JSONEncoder,
    _get_entity_type_name,
    _display_entity_info,
    _rotate_proxy
)
from credentials import API_ID, API_HASH, PHONE_NUMBER, PROXIES

# Replace these with your own values in the "credentials.py" file
api_id: str = str(API_ID)
api_hash: str = API_HASH
phone_number: str = PHONE_NUMBER


def collect_messages(entity: Channel | Chat | User) -> bool:
    """
    Performs a collection of all messages in a given entity.
    An entity can be a Channel (Broadcast Channel or Public Group),
    a User (direct message), Chat (private group)

    Args:
        entity: entity of type Channel, Chat or User

    Return:
        True if collection was successful
    """
    try:
        print("[+] Messages collection in progress...")

        # Collect messages from entity
        # https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.messages.MessageMethods.get_messages
        # Or check client.iter_messages() documentation to see how client.get_messages() works
        # Due to limitations with the API retrieving more than 3000 messages will take longer than half a minute or more.
        chunk_size: int = 80  # Number of messages to retrieve per iteration
        min_id: int = -1  # Retrieve IDs > min_id
        max_id: int = chunk_size  # Retrieve IDs < max_id
        counter: int = 0
        counter_rotate_proxy: int = 2  # Number of iterations until next proxy is set
        messages_collected: helpers.TotalList = None

        while True:
            counter += 1
            if counter == counter_rotate_proxy:
                print(f"Rotating proxy...")
                _rotate_proxy(client)
                counter = 0

            chunk: helpers.TotalList = client.get_messages(
                entity, min_id=min_id, max_id=max_id, reverse=True
            )
            # print("length ", len(chunk))

            if len(chunk) > 0:
                if messages_collected is None:
                    messages_collected = chunk  # First chunk
                else:
                    messages_collected.extend(chunk)
                min_id += chunk_size
                max_id += chunk_size
            else:
                break
        
        if messages_collected is None or len(messages_collected) == 0:
            print(f"There are no messages to collect. Skipping...")
            return True

        # Define the JSON file name
        json_file_name = f"output_{_get_entity_type_name(entity)}_{entity.id}/messages_{entity.id}.json"

        # Check if directory exists, create it if necessary
        os.makedirs(os.path.dirname(json_file_name), exist_ok=True)

        # Convert the Message object to JSON
        messages_list: list[dict] = []
        for message in messages_collected:
            if type(message) in (Message, MessageService):
                message_dict: dict = message.to_dict()
                messages_list.append(message_dict)

        # Write messages in JSON object to JSON file
        with open(json_file_name, "w", encoding="utf-8") as json_file:
            json.dump(messages_list, json_file, cls=JSONEncoder, indent=2)

        print(f"{len(messages_list)} messages exported to {json_file_name}")
        return True
    except:
        print(f"Collection failed")
        raise


def collect_participants(entity: Channel | Chat | User) -> bool:
    """
    Performs a collection of all messages in a given entity.
    An entity can be a Channel (Broadcast Channel or Public Group),
    a User (direct message), Chat (private group)

    Args:
        entity: entity of type Channel, Chat or User

    Return:
        True if collection was successful
    """
    # NOTE: Cannot get channel participants / subscribers unless have admin privilege
    # https://stackoverflow.com/questions/69651904/telethon-get-channel-participants-without-admin-privilages
    # Only works for private groups

    print("[+] Participants collection in progress...")

    # Collect participants from entity
    # https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.chats.ChatMethods.get_participants
    # Or check client.iter_partcipants() documentation to see how client.get_participants() works
    """
    Types of participants:
    - ChannelParticipant: 
        ChannelParticipant, ChannelParticipantBanned, ChannelParticipantLeft, 
        ChannelParticipantAdmin, ChannelParticipantCreator
        # The filter ChannelParticipantsBanned will return restricted users. 
        # If you want banned users you should use ChannelParticipantsKicked instead.
    - ChatParticipant(s)
        ChatParticipant, ChatParticipantCreator, ChatParticipantAdmin
        ChatParticipants, ChatParticipantsForbidden
    - ReadParticipantDate
    and more... search for "participants" on https://tl.telethon.dev/
    """
    # NOTE: There is a an unknown limit on participants collection
    # https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.chats.ChatMethods.iter_participants
    # See documentation for the "aggressive" argument...
    # > There have been several changes to Telegram’s API that limits the amount of members that can be retrieved,
    #   and this was a hack that no longer works.
    participants_collected: helpers.TotalList = client.get_participants(entity, limit=5)

    # Define the JSON file name
    json_file_name = f"output_{_get_entity_type_name(entity)}_{entity.id}/participants_{entity.id}.json"

    # Check if directory exists, create it if necessary
    os.makedirs(os.path.dirname(json_file_name), exist_ok=True)

    # Convert the Message object to JSON
    participants_list: list[dict] = []
    for participant in participants_collected:
        participant_dict: dict = participant.to_dict()
        participants_list.append(participant_dict)

    # Write messages in JSON object to JSON file
    with open(json_file_name, "w", encoding="utf-8") as json_file:
        json.dump(participants_list, json_file, cls=JSONEncoder, indent=2)

    print(f"Messages exported to {json_file_name}")
    return True


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

        entity: Channel | Chat | User = dialog.entity

        # Retrieve entity by its ID and display logs
        # entity: Channel | User | Chat = client.get_entity(id)
        print("[+] Collection in progress...")
        _display_entity_info(entity)
        print()

        collect_messages(entity)
        print()
        # collect_participants(entity)
        print("------------------------------------------------------")
        break
