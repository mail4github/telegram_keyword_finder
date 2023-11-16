from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.tl.functions.messages import GetHistoryRequest
# from telethon.tl.types import PeerChannel
from telethon import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
import csv
import base64
import requests
import json
from datetime import datetime
import time
import os

# name: consalappbot4
api_id = '';
api_hash = '';
phone = '';
api_url = '';
messages_file_path = 'sent_messages.txt'
last_log_message_file_path = 'last_message.txt'
credentials_file_path = 'credentials.txt'

all_messages = []
offset_id = 0
limit = 100
maximum_messages = 100
cur_username = ''
history = None
chats = []
last_date = None
chunk_size = 200
groups = []
sent_messages_arr = []
parse_messages_for_last_hours = 24

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
    log_message_e = base64.b64encode(log_message.encode('utf-8')).decode("utf-8")
    asss = '{"message" : "' + log_message_e + '", "color" : "' + log_color + '", "unixtime" : "' + str(
        round(time.time())) + '"}'
    asss = base64.b64encode(asss.encode('utf-8')).decode("utf-8")
    #print(f'{api_url}?command=add_log&log={asss}')
    result = requests.get(api_url, params={'command': 'add_log', 'log': asss})
    print(f'\033[93m sent alert: {result.text} \033[0m')

def save_exception(ex_message):
    f = open(last_log_message_file_path, "w")
    f.write(ex_message)
    f.close()

# read telegram API credentials from file
try:
    f = open(credentials_file_path, "r")
    credentials = f.read()
    f.close()
    if credentials and len(credentials) > 0:
        arr = json.loads(credentials)
        api_id = arr['api_id']
        api_hash = arr['api_hash']
        phone = arr['phone']
        api_url = arr['api_url']
        if 'maximum_messages' in arr:
            maximum_messages = arr['maximum_messages']
        if 'parse_messages_for_last_hours' in arr:
            parse_messages_for_last_hours = arr['parse_messages_for_last_hours']
    else:
        print('Error: no credentials')
        exit()
except Exception as err:
    print(f"Exception reading credentials file '{credentials_file_path}' {err=}, {type(err)=}")
    exit()

# read last exception message and send it to the log on web server
try:
    f = open(last_log_message_file_path, "r")
    last_message = f.read()
    f.close()
    os.remove(last_log_message_file_path)
    if last_message and len(last_message) > 0:
        save_log(last_message, 'R')
        print('sent log: ' + last_message)
except Exception:
    pass

#save_log("Cannot read messages from group ", 'O')
#exit()

# Connect to the Telegram
client = TelegramClient(phone, api_id, api_hash)

client.start()

# Search for chats
with client:
    client.loop.run_until_complete(find_chats())

# Add to the groups array chats, which are created by owner or which are megagroups
for chat in chats:
    try:
        #if chat.creator == True or chat.megagroup == True:
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

requests.post(api_url, data={'groups_json': groups_json})

# Retrieve the list of keywords from the admin web server
keywords_arr = []
result = requests.get(api_url, params={'command': 'get_keywords'})
try:
    res_json = json.loads(result.text)
    if res_json['success']:
        keywords_json = res_json['values']
        if type(keywords_json) == str and len(keywords_json) > 0:
            keywords_arr = json.loads(keywords_json)
            for i in range(len(keywords_arr)):
                keywords_arr[i] = base64.b64decode(keywords_arr[i]).decode('utf-8')
                #print('keyword: ' + keywords_arr[i])
        else:
            print(f'\033[93m' + "Error: no keywords specified. Add some keywords" + '\033[0m')
except Exception as err:
    print(f"\033[91m Exception reading keywords {err=}, {type(err)=} \033[0m")
    save_exception(f"Exception reading keywords {err=}, {type(err)=}")
    exit()

# Retrieve the list of stop words from the admin web server
stopwords_arr = []
result = requests.get(api_url, params={'command': 'get_stopwords'})
try:
    res_json = json.loads(result.text)
    if res_json['success']:
        keywords_json = res_json['values']
        if type(keywords_json) == str and len(keywords_json) > 0:
            stopwords_arr = json.loads(res_json['values'])
            for i in range(len(stopwords_arr)):
                stopwords_arr[i] = base64.b64decode(stopwords_arr[i]).decode('utf-8')
        else:
            print(f'\033[93m' + "No stop words specified" + '\033[0m')
except Exception as err:
    print(f"\033[91m Exception reading stopwords {err=}, {type(err)=} \033[0m")
    save_exception(f"Exception reading stopwords {err=}, {type(err)=}")

# Read list of already processed messages
sent_messages_txt = ''
try:
    f = open(messages_file_path, "r")
    sent_messages_txt = f.read()
    f.close()
except Exception:
    pass

if sent_messages_txt and len(sent_messages_txt) > 0:
    sent_messages_arr = json.loads(sent_messages_txt)

# Retrieve the list of groups from the admin web server
result = requests.get(api_url, params={'command': 'get_groups_to_listen'})

debug_step = "0"
try:
    res_json = json.loads(result.text)
    if res_json['success']:
        groups_to_monitor = res_json['values']
        for group_to_monitor in groups_to_monitor:
            # if group does not have the "listen" flag then reject it
            if group_to_monitor['group_status'] != 'l':
                continue
            
            # search for the group object by given id
            group_id = group_to_monitor['group_id']
            grop_found = False
            for g in groups:
                if group_id == str(g.id):
                    target_group = g
                    grop_found = True
                    print('Searching in group: ' + target_group.title)
                    break

            debug_step = "1"

            offset_id = 0

            while grop_found:

                # retrive the group messages
                with client:
                    try:
                        client.loop.run_until_complete(find_messages(group=target_group))
                    except Exception as err:
                        print(f'\033[93m' + "Cannot read messages from group: " + target_group.title + '\033[0m')
                        #save_log("Cannot read messages from group: " + target_group.title, 'O')
                
                debug_step = "12"

                if not history or not history.messages:
                    break
                messages = history.messages
                
                debug_step = "2"

                # discard messages which are created long time ago
                if len(messages) > 0 and time.time() - time.mktime(messages[0].date.timetuple()) > parse_messages_for_last_hours * 60 * 60:
                    break

                for message in messages:
                    try:
                        if time.time() - time.mktime(message.date.timetuple()) < parse_messages_for_last_hours * 60 * 60:
                            msg_user_id = message.sender_id  # message.from_id.user_id
                            
                            if not message.message or len(message.message) == 0:
                               continue
                            
                            # look for any of stopword in message
                            stopword_found = False
                            for stopword in stopwords_arr:
                                if message.message.lower().find(stopword.lower()) >= 0:
                                    stopword_found = True
                                    break
                            if stopword_found:
                                continue
                            
                            debug_step = "3"

                            # look for any of keyword in message
                            keyword_found = False
                            keyword_which_found = ''
                            for keyword in keywords_arr:
                                
                                if message.message.lower().find(keyword.lower()) >= 0:
                                    keyword_found = True
                                    keyword_which_found = keyword
                                    break

                            if keyword_found:
                                # make sure that this message has not been processed before
                                message_already_processed = False
                                for sent_message_id in sent_messages_arr:
                                    if sent_message_id == message.id:
                                        message_already_processed = True
                                        break
                                debug_step = "4"
                                if not message_already_processed:
                                    all_messages.append(message.date.strftime('%Y-%m-%d') + ' ' + message.message)
                                    sent_messages_arr.append(message.id)

                                    print('Found message: ' + message.date.strftime('%Y-%m-%d') + ' id: ' + str(message.id))
                                    save_log('Found new message', 'G')

                                    cur_username = '';

                                    with client:
                                        client.loop.run_until_complete(find_user_name(msg_user_id))

                                    if not isinstance(cur_username, str):
                                        cur_username = ""
                                    
                                    debug_step = "5"

                                    if len(cur_username) <= 0:
                                        cur_username = target_group.username
                                    message_text = '<a href="https://t.me/' + target_group.username + "/" + str(message.id) + '/">' + cur_username + "</a>\n" + '&#128273;<b>' + keyword_which_found + '</b>\n' + message.message

                                    # forward this message to the admin groups
                                    for group_of_admins in groups_to_monitor:
                                        if group_of_admins['group_status'] == 'a':
                                            for group_object in groups:
                                                if group_of_admins['group_id'] == str(group_object.id):
                                                    debug_step = "6"
                                                    with client:
                                                        client.loop.run_until_complete(
                                                            send_mess(group=group_object, message=message_text))
                                                    print('\033[92m' + 'Sent message id: ' + str(message.id) + ' to group: ' + group_object.title + '\033[0m')
                                                    break

                        if maximum_messages != 0 and len(all_messages) >= maximum_messages:
                            break
                    except Exception as err:
                        print('\033[91m' + f"Unexpected {err=}, {type(err)=}, {debug_step=}"+ '\033[0m')
                        print('\033[91m' + f"mes: {message.message=}, {keyword=}"+ '\033[0m')
                        # save_exception(f"eception in processing message {err=}, {type(err)=}")

                offset_id = messages[len(messages) - 1].id
                if maximum_messages != 0 and len(all_messages) >= maximum_messages:
                    break

        f = open(messages_file_path, "w")
        f.write(json.dumps(sent_messages_arr))
        f.close()

        messages_json = ""
        for message in all_messages:
            try:
                if message:
                    b64_enc = base64.b64encode(message.encode('utf-8')).decode('utf-8')
                    item_json = f'"message" : "{b64_enc}"'
                    messages_json = messages_json + (',' if len(messages_json) > 0 else '') + '{' + item_json + '}'
            except Exception as err:
                print(f"Was exception: {err=}, {type(err)=}")

        messages_json = '[' + messages_json + ']';
        messages_json = base64.b64encode(messages_json.encode('utf-8')).decode('utf-8')
        res = requests.post(api_url + "?command=add_found_messages", data={'messages': messages_json})


except Exception as err:
    print(f"Global exception: {err=}, {type(err)=} {debug_step=}")
    save_exception(f"Global exception: {err=}, {type(err)=}, {debug_step=}")

