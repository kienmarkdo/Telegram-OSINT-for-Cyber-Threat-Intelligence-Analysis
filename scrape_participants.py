from telethon import TelegramClient
from telethon.sync import helpers
from telethon.types import *
from telethon.tl.functions.channels import GetParticipantsRequest

import re
import json
import os
import logging  # 2 TODO: Convert print statements to proper logging to a file
import time
from datetime import datetime
from string import ascii_lowercase

from helper.helper import (
    EntityName,
    JSONEncoder,
    _get_entity_type_name,
    _display_entity_info,
    _generate_user_keys,
    _rotate_proxy,
    DATETIME_CODE_EXECUTED,
    OUTPUT_DIR,
)


def collect_participants_large(
    client: TelegramClient, entity: Channel | Chat | User
) -> bool:
    """
    Collects all participants in a given entity via its API and stores the data in-memory.
    An entity can be a Channel (Broadcast Channel or Public Group),
    a User (direct message), Chat (private group).

    Collection can only be done on public groups, private groups, and direct messages,
    not broadcast channels, as subscribers are hidden from non-admin users at the API
    level and cannot be bypassed.

    Args:
        entity: entity of type Channel, Chat or User

    Return:
        True if collection was successful
    """
    # NOTE: Cannot get channel participants / subscribers unless have admin privilege
    # https://stackoverflow.com/questions/69651904/telethon-get-channel-participants-without-admin-privilages

    # NOTE: There is a an unknown limit on participants collection
    # https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.chats.ChatMethods.iter_participants
    # See documentation for the deprecated "aggressive" argument...
    # > There have been several changes to Telegram’s API that limits the amount of members that can be retrieved,
    #   and this was a hack that no longer works.
    print("[+] Participants collection in progress...")

    # Check that entity type is not a broadcast channel
    if _get_entity_type_name(entity) == EntityName.BROADCAST_CHANNEL.value:
        print(
            f"Cannot collect participants in {EntityName.BROADCAST_CHANNEL.value}. Skipping participants collection..."
        )
        return True

    # Collect participants https://github.com/LonamiWebs/Telethon/issues/580#issuecomment-362802359
    queryKey: list[str] = list(ascii_lowercase)  # ["a", "b", "c", ... , "z"]
    limit: int = 200
    all_participants: list = []

    for key in queryKey:
        offset = 0  # For each query, offest restarts at 0

        while True:
            participants = client(
                GetParticipantsRequest(
                    entity.id, ChannelParticipantsSearch(key), offset, limit, hash=0
                )
            )

            if not participants.users:
                print(f"Done searching for '{key}'")
                break  # No more participants left

            for user in participants.users:
                # Append users whose first name starts with current key character
                try:
                    if re.findall(r"\b[a-zA-Z]", user.first_name)[0].lower() == key:
                        all_participants.append(user)
                except:
                    pass

            offset += len(participants.users)

    if all_participants is None or len(all_participants) == 0:
        print(f"There are no participants to collect. Skipping...")
        return True
    else:
        # Evaluate percentage of participants successfully collected
        collected_amount: int = len(all_participants)
        total_amount: int = entity.participants_count
        print(
            f"{collected_amount} participants collected out of {total_amount} total participants"
        )
        print(
            f"Successfully collected {collected_amount/total_amount * 100}% of participants"
        )

    # Convert the Participants object to JSON
    participants_list: list[dict] = []
    for participant in all_participants:
        participant_dict: dict = participant.to_dict()
        participants_list.append(participant_dict)

    download(participants_list, "participants", entity)


def download(data: list[dict], data_type: str, entity: Channel | Chat | User) -> bool:
    """
    Downloads collected participants into JSON files on the disk

    Args:
        data: list of collected objects (messages, participants...)
        data_type: string description of the type of data collected ("messages", "participants"...)
        entity: channel (public group or broadcast channel), chat (private group), user (direct message)

    Return:
        True if the download was successful
    """
    try:
        # Define the JSON file name
        json_file_name = f"{OUTPUT_DIR}/{DATETIME_CODE_EXECUTED}/{_get_entity_type_name(entity)}_{entity.id}/{data_type}_{entity.id}.json"

        # Check if directory exists, create it if necessary
        os.makedirs(os.path.dirname(json_file_name), exist_ok=True)

        # Write data from JSON object to JSON file
        with open(json_file_name, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, cls=JSONEncoder, indent=2)

        print(f"{len(data)} {data_type} exported to {json_file_name}")

        return True
    except:
        print("[-] Failed to download the collected data into JSON files")
        raise


def scrape(client: TelegramClient, entity: Channel | Chat | User) -> bool:
    """
    Scrapes participants in a particular entity.

    An entity can be a Channel (Broadcast Channel or Public Group),
    a User (direct message), Chat (private group).

    Scraping has the following phases:
    - Collection: fetches participants from the provider API and stores the data in-memory
    - Download: downloads the collected participants from memory into disk (JSON file)

    Collection can only be done on public groups, private groups, and direct messages,
    not broadcast channels, as subscribers are hidden from non-admin users at the API
    level and cannot be bypassed.

    Args:
        entity: entity of type Channel, Chat or User

    Return:
        True if scrape was successful
    """
    collect_participants(client, entity)
