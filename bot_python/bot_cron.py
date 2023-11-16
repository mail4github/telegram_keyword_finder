#
# this software is calling from cron
#
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.tl.functions.messages import GetHistoryRequest
from telethon import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
import csv
import base64
import requests
import json
from datetime import datetime
import time
import os
import sys
import asyncio

api_id = '';
api_hash = '';
phone = '';
limit = 100
maximum_messages = 100
parse_messages_for_last_hours = 24
chunk_size = 200

all_messages = []
offset_id = 0
cur_username = ''
history = None
chats = []
last_date = None

groups = []
sent_messages_arr = []

async def find_chats():
    res = await client(GetDialogsRequest(
        offset_date=last_date,
        offset_id=0,
        offset_peer=InputPeerEmpty(),
        limit=chunk_size,
        hash=0
    ))
    chats.extend(res.chats)

async def find_user(id_):
    return await client(GetFullUserRequest(int(id_)))

async def find_user_name(user_id):
    full = await find_user(user_id)
    try:
        global cur_username
        cur_username = ''

        if full.users and full.users[0] and full.users[0].username:
            cur_username = cur_username + ' |@' + full.users[0].username + '|'
        if full.full_user and full.full_user.about:
            cur_username = cur_username + ' ' + full.full_user.about
        if full.users and full.users[0] and full.users[0].first_name:
            cur_username = cur_username + ' ' + full.users[0].first_name
        if full.users and full.users[0] and full.users[0].last_name:
            cur_username = cur_username + ' ' + full.users[0].last_name
        if full.users and full.users[0] and full.users[0].phone:
            cur_username = cur_username + ' +' + full.users[0].phone

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")

async def find_messages(group=None):
    global history
    history = None
    if group:
        history = await client(GetHistoryRequest(
            peer=group,
            offset_id=offset_id,
            offset_date=None,
            add_offset=0,
            limit=limit,
            max_id=0,
            min_id=0,
            hash=0
        ))

async def send_mess(group, message):
    await client.send_message(entity=group, message=message, parse_mode = 'HTML')

def save_log(log_message='', log_color=''):
    return False
    '''
    log_message_e = base64.b64encode(log_message.encode('utf-8')).decode("utf-8")
    asss = '{"message" : "' + log_message_e + '", "color" : "' + log_color + '", "unixtime" : "' + str(
        round(time.time())) + '"}'
    asss = base64.b64encode(asss.encode('utf-8')).decode("utf-8")
    result = requests.get(api_url, params={'command': 'add_log', 'log': asss})
    print(f'\033[93m sent alert: {result.text} \033[0m')
    '''

def save_exception(ex_message):
    return False
    '''
    f = open(last_log_message_file_path, "w")
    f.write(ex_message)
    f.close()
    '''

customers_file_path = os.path.dirname(os.path.realpath(__file__)) + '/customers.json'
print(customers_file_path)

f = open(customers_file_path)
customers = f.read()
f.close()
print(f"{customers=}")
if customers and len(customers) > 0:
    customers_arr = json.loads(customers)
    #print(customers_arr[0]['phone'])
    api_id = customers_arr[0]['api_id']
    api_hash = customers_arr[0]['api_hash']
    phone = customers_arr[0]['phone']
    if 'maximum_messages' in customers_arr[0]:
        maximum_messages = customers_arr[0]['maximum_messages']
    if 'parse_messages_for_last_hours' in customers_arr[0]:
        parse_messages_for_last_hours = customers_arr[0]['parse_messages_for_last_hours']
    
    # Connect to the Telegram
    client = TelegramClient(phone, api_id, api_hash)
    '''
    client.connect()
    if not client.is_user_authorized():
        print(f"\033[91m user {phone=} not authorized \033[0m")
        save_exception(f"user not authorized")
        sys.exit()
    '''
    client.start()
    # Search for chats
    with client:
        client.loop.run_until_complete(find_chats())

    # Add to the groups array chats, which are created by owner or which are megagroups
    for chat in chats:
        try:
            groups.append(chat)
        except:
            continue

    # Send the list with groups to the admin web server
    print('Found groups:')
    groups_json = ''
    i = 0
    for g in groups:
        group_n = base64.b64encode(g.title.encode('utf-8')).decode('utf-8')
        item_json = f'"group_name" : "{group_n}", "group_id" : "{g.id}", "username" : "{"unknown" if not hasattr(g, "username") else g.username}"'
        groups_json = groups_json + (',' if len(groups_json) > 0 else '') + '{' + item_json + '}'
        print(str(i) + '- ' + g.title)
        i += 1

    groups_json = '[' + groups_json + ']'
    groups_json = base64.b64encode(groups_json.encode('utf-8')).decode("utf-8")

    #requests.post(api_url, data={'groups_json': groups_json})
