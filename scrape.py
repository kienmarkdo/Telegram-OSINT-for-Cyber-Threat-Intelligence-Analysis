from telethon.sync import helpers
from telethon.types import *
from telethon import functions
from telethon.tl.functions.channels import GetParticipantsRequest
from db import start_database, messages_get_offset_id, messages_insert_offset_id

import re
import json
import os
import logging  # 2 TODO: Convert print statements to proper logging to a file
import time

from helper.helper import (
    EntityName,
    TelegramClientContext,
    JSONEncoder,
    _get_entity_type_name,
    _display_entity_info,
    _generate_user_keys,
    _rotate_proxy,
    DATETIME_CODE_EXECUTED,
)

import scrape_messages
import scrape_participants
import scrape_entities
from credentials import API_ID, API_HASH, PHONE_NUMBER

# Replace these with your own values in the "credentials.py" file
api_id: str = str(API_ID)
api_hash: str = API_HASH
phone_number: str = PHONE_NUMBER

OUTPUT_DIR: str = "output"
# DATETIME_CODE_EXECUTED: str = str(int(time.time()))


def collect_participants_new(entity: Channel | Chat | User) -> bool:
    """
    Performs a collection of all participants in a given entity.
    An entity can be a Channel (Broadcast Channel or Public Group),
    a User (direct message), Chat (private group)

    Args:
        entity: entity of type Channel, Chat or User

    Return:
        True if collection was successful
    """
    try:
        print("[+] Participants collection in progress...")

        chunk_size: int = 1000  # Number of messages to retrieve per iteration
        counter: int = 0
        counter_rotate_proxy: int = 2  # Number of iterations until next proxy is set
        participants_collected: helpers.TotalList = None
        offset_id_value: int = 0

        # participants_collected = client.get_participants(entity, limit=None)
        # print(f"LENGTHHH: {len(participants_collected)}")
        # return True

        while True:
            # Proxy rotation...
            counter += 1
            if counter == counter_rotate_proxy:
                print(f"Rotating proxy...")
                _rotate_proxy(client)
                counter = 0

            # chunk: helpers.TotalList = client.get_participants(
            #     entity, limit=chunk_size, reverse=True, offset_id=offset_id_value
            # )
            # something = client.iter_participants()
            chunk = client(
                functions.channels.GetParticipantsRequest(
                    channel=entity.id,
                    filter=ChannelParticipantsSearch(""),
                    offset=offset_id_value,
                    limit=chunk_size,
                    hash=0,
                )
            )
            if chunk.users is None:
                print(f"No users")
                break
            chunk = chunk.users

            if len(chunk) > 0:  # Partci were returned
                if participants_collected is None:
                    participants_collected = chunk  # First chunk
                else:
                    participants_collected.extend(
                        chunk
                    )  # Append to existing messages collected
                print(f"Collecting {len(chunk)} participants...")
                # break
            else:  # No messages returned... All messages have been collected
                print(f"No participants left to collect")
                break
            # offset_id_value = chunk[-1].to_dict()["id"]
            offset_id_value += len(chunk)
            # TODO: Fetch/update the offset id above in an SQL database

        if participants_collected is None or len(participants_collected) == 0:
            print(f"There are no participants to collect. Skipping...")
            return True

        # Define the JSON file name
        json_file_name = f"output/{_get_entity_type_name(entity)}_{entity.id}/participants_{entity.id}.json"

        # Check if directory exists, create it if necessary
        os.makedirs(os.path.dirname(json_file_name), exist_ok=True)

        # Convert the Message object to JSON
        participants_list: list[dict] = []
        for participant in participants_collected:
            # Known message types: Message, MessageService
            participant_dict: dict = participant.to_dict()
            participants_list.append(participant_dict)

        # Write messages in JSON object to JSON file
        with open(json_file_name, "w", encoding="utf-8") as json_file:
            json.dump(participants_list, json_file, cls=JSONEncoder, indent=2)

        print(f"{len(participants_list)} participants exported to {json_file_name}")
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
    if _get_entity_type_name(entity) == EntityName.BROADCAST_CHANNEL.value:
        print(
            f"Cannot collect participants in {EntityName.BROADCAST_CHANNEL.value}. Skipping participants collection..."
        )
        return True

    # # Collect participants
    # _rotate_proxy(client)  # Start collection with new proxy
    participants_collected: helpers.TotalList = client.get_participants(entity)

    # Define the JSON file name
    json_file_name = f"output/{_get_entity_type_name(entity)}_{entity.id}/participants_{entity.id}.json"

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

    print(f"{len(participants_list)} participants exported to {json_file_name}")
    return True


def collect_participants_test(entity: Channel | Chat | User):
    # queryKey = _generate_user_keys()
    # all_participants = []
    # channel = entity.id
    # counter = 0
    # counter_rotate_proxy = 3

    # for key in queryKey:
    #     print("KEYYYYYYYYYYYY: " + key)
    #     offset = 0
    #     limit = 300
    #     while True:
    #         # counter += 1
    #         # if counter == counter_rotate_proxy:
    #         #     print(f"Rotating proxy...")
    #         #     _rotate_proxy(client)
    #         #     counter = 0

    #         participants = client(GetParticipantsRequest(
    #             channel, ChannelParticipantsSearch(key), offset, limit,
    #             hash=0
    #         ))
    #         if not participants.users:
    #             break
    #         for user in participants.users:
    #             try:
    #                 if re.findall(r"\b[a-zA-Z]{2}", user.first_name)[0].lower() == key:
    #                     print(user.first_name)
    #                     all_participants.append(user)

    #             except:
    #                 pass

    #         offset += len(participants.users)
    #         # print(offset)
    #     # counter += 1
    #     # if counter == 10:
    #     #     break
    # print(f"{len(all_participants)} users collected...")
    # print(f"Example user:")
    # print(all_participants[0])
    queryKey = [
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "h",
        "i",
        "j",
        "k",
        "l",
        "m",
        "n",
        "o",
        "p",
        "q",
        "r",
        "s",
        "t",
        "u",
        "v",
        "w",
        "x",
        "y",
        "z",
    ]
    all_participants = []
    channel = entity.id
    counter = 0
    counter_rotate_proxy = 3

    for key in queryKey:
        counter += 1
        if counter == counter_rotate_proxy:
            _rotate_proxy(client)
            counter = 0

        offset = 0
        limit = 100
        while True:
            participants = client(
                GetParticipantsRequest(
                    channel, ChannelParticipantsSearch(key), offset, limit, hash=0
                )
            )
            if not participants.users:
                break
            for user in participants.users:
                try:
                    if re.findall(r"\b[a-zA-Z]", user.first_name)[0].lower() == key:
                        all_participants.append(user)

                except:
                    pass

            offset += len(participants.users)
            # print(offset)
    print(f"{len(all_participants)} users collected...")
    print(f"Example user:")
    print(all_participants[0])
    print(entity.participants_count)
    # pass


def setup() -> bool:
    """
    Sets up the environment prior to starting a collection

    Return:
        True if the setup was successful
    """
    try:
        start_database()
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        return True
    except:
        raise


with TelegramClientContext() as client:
    # Setup operations
    if setup() is not True:
        raise "[-] Failed to setup the environment. Cannot begin collection."

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

    # Iterate through all inboxes aka dialogs (DMs, public groups, private groups, broadcast channels)
    # https://docs.telethon.dev/en/stable/quick-references/client-reference.html#dialogs
    # https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.dialogs.DialogMethods.iter_dialogs
    # scrape_entities.scrape(client)
    for dialog in client.iter_dialogs():

        entity: Channel | Chat | User = dialog.entity
        if entity.id != 1647639783 and entity.id != 1012147388:
            continue
        # if entity.id != 1012147388:
        #     continue
        # if entity.id != 1488156064:
        #     continue

        # Retrieve entity by its ID and display logs
        # entity: Channel | User | Chat = client.get_entity(id)
        print("[+] Collection in progress...")
        _display_entity_info(entity)
        print()

        # scrape_entities.scrape(client)
        scrape_entities.download_entity(entity)
        scrape_messages.scrape(client, entity)
        print()
        # scrape_participants.scrape(client, entity)
        # collect_participants(entity)
        # collect_participants_test(entity)
        # collect_participants_new(entity)
        print("------------------------------------------------------")
        if entity.id == 1647639783:  # russian
            break
        # if entity.id == 1012147388:
        #     break
        # if entity.id == 1488156064:
        #     break
