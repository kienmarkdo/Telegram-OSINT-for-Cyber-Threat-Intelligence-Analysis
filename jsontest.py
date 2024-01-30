from telethon.types import *
import json
import datetime

message = Message(id=3, peer_id=PeerChat(chat_id=4199887938), date=datetime.datetime(2024, 1, 17, 5, 22, 44, tzinfo=datetime.timezone.utc), message='Hi', out=True, mentioned=False, media_unread=False, silent=False, post=False, from_scheduled=False, legacy=False, edit_hide=False, pinned=False, noforwards=False, invert_media=False, from_id=PeerUser(user_id=6599524796), fwd_from=None, via_bot_id=None, reply_to=None, media=None, reply_markup=None, entities=[], views=None, forwards=None, replies=None, edit_date=None, post_author=None, grouped_id=None, reactions=None, restriction_reason=[], ttl_period=None)

# Convert Message object to a dictionary
message_dict = message.to_dict()

# Convert the dictionary to JSON
json_data = json.dumps(message_dict, default=str)

# Write the JSON data to a file
with open('output.json', 'w', encoding='utf-8') as json_file:
    json_file.write(json_data)