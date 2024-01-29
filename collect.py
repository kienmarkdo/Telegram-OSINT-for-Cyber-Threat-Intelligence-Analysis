"""
Author: Kien Do

Performs a batch collection of relevant objects in Telegram groups and stores them in its raw format.
You must first sign in to Telegram on device prior to executing this collection script so that you can
receive a confirmation code when the scripts asks you to enter your phone number.
"""

import os
import requests
from requests import *
from api_keys import USERNAME, PHONE_NUMBER, API_KEY, HTTP_API, API_ID, API_HASH
from telethon import TelegramClient

username: str
phone_number: str
http_api: str
api_hash: str
api_id: int
groups: list[str]  # store group URLs

# class User:
#     username: str
#     phone_number: str
#     http_api: str
#     api_hash: str
#     api_id: int
#     groups: list[str]  # store group URLs

#     def __init__(self) -> None:
#         self.username = USERNAME
#         self.phone_number = (
#             PHONE_NUMBER  # optional. Use with any phone number or even for bot accounts
#         )
#         self.http_api = HTTP_API
#         self.api_hash = API_HASH  # required
#         self.api_id = API_ID  # required

#     def initialize_groups(self) -> bool:
#         pass

#     def collect(self):
#         # The first parameter is the .session file name (absolute paths allowed)
#         with TelegramClient("anon", self.api_id, self.api_hash) as client:
#             client.loop.run_until_complete(client.send_message("me", "Hello, myself!"))
#             client.loop.run_until_complete(client.get_message("bloomberg"))
        
import csv

client: TelegramClient = TelegramClient("anon", API_ID, API_HASH)


async def main():
    result = await client.get_messages("me", limit=100)

    print(result.total)  # large number
    print(len(result))  # 10
    print(result[0])  # latest message

    print("=================================================")

    for x in result:  # show the 10 messages
        print(x.text)
        print("=================================================")

with client:
    client.loop.run_until_complete(main())




# if __name__ == "__main__":
#     user: User = User()
#     user.collect()