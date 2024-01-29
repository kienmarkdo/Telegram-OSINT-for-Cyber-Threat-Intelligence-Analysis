from telethon.sync import TelegramClient, helpers
from telethon.types import Channel
from api_keys import API_ID, API_HASH, PHONE_NUMBER
from typing import ContextManager  # to enable static typing with the "with" statement in Python
import csv

# Replace these with your own values in the "api_keys.py" file
api_id = str(API_ID)
api_hash = API_HASH
phone_number = PHONE_NUMBER
channel_username = 'bloomberg'


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

    # Get the channel entity
    channel: Channel = client.get_entity(channel_username)

    # Get all messages from oldest to newest
    # TotaList class https://docs.telethon.dev/en/stable/modules/helpers.html
    # Message class https://tl.telethon.dev/constructors/message.html
    #               https://docs.telethon.dev/en/v2/concepts/messages.html
    messages: helpers.TotalList = client.get_messages(channel, limit=None)
    counter: int = 0
    # for message in messages:
    #     print(message)
    #     print("============================================")

    # Define the CSV file name
    csv_file_name = f'messages_{channel_username}.csv'

    # Write messages to CSV file
    with open(csv_file_name, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['date', 'from_id', 'message']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write CSV header
        writer.writeheader()

        # Write messages to CSV
        for message in messages:
            writer.writerow({
                'date': message.date,
                'from_id': message.from_id,
                'message': message.text
            })

    print(f'Messages exported to {csv_file_name}')


