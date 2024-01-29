from telethon import TelegramClient, types
from api_keys import API_ID, API_HASH, PHONE_NUMBER

# Remember to use your own values from my.telegram.org!
api_id = API_ID
api_hash = API_HASH
client = TelegramClient('anon', api_id, api_hash)

async def main():
    # Getting information about yourself
    me = await client.get_me()

    # "me" is a user object. You can pretty-print
    # any Telegram object with the "stringify" method:
    print(me.stringify())
    print("==============================================")

    # When you print something, you see a representation of it.
    # You can access all attributes of Telegram objects with
    # the dot operator. For example, to get the username:
    username = me.username
    print(username)
    print(me.phone)

    print("==============================================")

    # You can print all the dialogs/conversations that you are part of:
    # something: list[types.Dialog] = client.iter_dialogs()
    # for some in something:
    #     some.name

    all_dialog_ids: list[int] = []
    selected_dialog_ids: list[int] = []
    counter: int = 0
    async for dialog in client.iter_dialogs():
        print(f"{counter}. {dialog.name} ({dialog.id})")
        all_dialog_ids.append(dialog.id)
        # if dialog.participants_count == 0:
        #     print(f"{dialog.name} {dialog.id}")
    
    # selected: str = input("Select the dialogs to scrape. Example: '[0,3,5]' or 'all'")
    
    

        
        

    # print("==============================================")

    # # You can send messages to yourself...
    # await client.send_message('me', 'Hello, myself!')
    # # ...to some chat ID
    # # await client.send_message(-100123456, 'Hello, group!')
    # # ...to your contacts
    # # await client.send_message('+34600123123', 'Hello, friend!')
    # # ...or even to any username
    # # await client.send_message('username', 'Testing Telethon!')

    # # You can, of course, use markdown in your messages:
    # message = await client.send_message(
    #     'me',
    #     'This message has **bold**, `code`, __italics__ and '
    #     'a [nice website](https://example.com)!',
    #     link_preview=False
    # )

    # # Sending a message returns the sent message object, which you can use
    # print(message.raw_text)

    # print("==============================================")

    # # You can reply to messages directly if you have a message object
    # await message.reply('Cool!')

    # # # Or send files, songs, documents, albums...
    # # await client.send_file('me', '/home/me/Pictures/holidays.jpg')
    # print("==============================================")
    # print("===============sdfadsasdasdas=================")
    # print("==============================================")
    # # You can print the message history of any chat:
    # async for message in client.iter_messages('me'):
    #     print(message.id, message.text)

    #     print("==============================================")

    #     # You can download media from messages, too!
    #     # The method will return the path where the file was saved.
    #     if message.photo:
    #         path = await message.download_media()
    #         print('File saved to', path)  # printed after download is done

with client:
    client.loop.run_until_complete(main())