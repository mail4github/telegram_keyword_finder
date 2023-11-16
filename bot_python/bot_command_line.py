# -*- coding: utf-8 -*-
#
# this software is called by the 'bot_init_connect.php' script with parameters passed through command line
#
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.tl.functions.messages import GetHistoryRequest
from telethon import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.errors import SessionPasswordNeededError

import csv
import base64
import json
from datetime import datetime
import time
import os
import sys
import traceback
from pathlib import Path
import random
import re
import string
import nltk
nltk.data.path.append("/var/www/telegram_bot/bot_python/nltk_data/")
from nltk import word_tokenize
from nltk.probability import FreqDist
from nltk.corpus import stopwords
from nltk.stem.snowball import RussianStemmer
from string import punctuation
from html import escape
sys.path.insert(1, os.path.dirname(os.path.realpath(__file__)) + '/langdetect')
from langdetect import detect as detect_language
#from langid import classify

script_started = time.time()

ERROR_NOT_AUTHORIZED = '1001'
ERROR_NO_PHONE = '1002'
ERROR_NO_CODE_FILE_NAME = '1003'
ERROR_NO_SUCH_GROUP = '1004'
WARNING_WRONG_STOPWORD = '10001'
WARNING_WRONG_KEYWORD = '10002'

api_id = ''
api_hash = ''
phone = ''
bot_token = ''
api_url = ''
sign_code = ''
code_file_name = ''
waiting_code_file_name = ''
tl_code = ''
password_2FA = ''
command_to_perfdorm = 'do_job'  # 'connect_to_debug'
exit_error = '0000'
exit_message = 'ok'
passed_data = ''
debug_mode = False
write_messages_on_screen = False
debug_keyword = ''
debug_stopword = ''
debug_group_to_forward = ''
debug_step = '0'
debug_dont_save_found_messages = False
send_message_recipient = ''
send_message_text = ''
ignore_messages_with_no_username = False
group_username = ''

max_messages_in_return = 100
maximum_messages = 20
parse_messages_for_last_hours = 24
max_chats_in_return = 200
max_exec_time_in_secs = 20

all_messages = []
offset_id = 0
cur_username = ''
history = None
chats = []
last_date = None
message_user_name = ""
groups = []
found_messages_arr = []
ignore_message_ids_arr = []

def save_log(log_message='', log_file_path=''):
    # return False

    script_dir = Path(__file__).parent.absolute()
    if len(log_file_path) == 0:
        log_file_path = str(script_dir) + '/bot_command_line_log.txt'

    # if log file is big then raname it and start new log
    try:
        log_file_size = os.stat(log_file_path).st_size
        # print("log_file_size=", log_file_size)
        if log_file_size > 1000000:
            file_name_to_save_old_log = log_file_path + '.old'
            try:
                os.remove(file_name_to_save_old_log)
            except Exception:
                pass
            os.rename(log_file_path, file_name_to_save_old_log)
    except Exception:
        pass

    now = datetime.now()
    if os.path.exists(log_file_path):
        append_write = 'a'  # append if already exists
    else:
        append_write = 'w'  # make a new file if not
    f = open(log_file_path, append_write, encoding="utf8")

    # try:
    # global phone
    # phone = phone + ''
    # except BaseException as e:
    # phone = ""
    # pass
    f.write(now.strftime("%d/%m/%Y %H:%M") + " " + str(phone) + " " + log_message + "\r\n")
    f.close()


def save_exception(ex_message):
    return False
    '''
    f = open(last_log_message_file_path, "w")
    f.write(ex_message)
    f.close()
    '''


async def find_chats():
    res = await client(GetDialogsRequest(
        offset_date=last_date,
        offset_id=0,
        offset_peer=InputPeerEmpty(),
        limit=max_chats_in_return,
        hash=0
    ))
    chats.extend(res.chats)


async def find_group(group_username):
    global grp
    grp = await client.get_entity(group_username)


async def get_group_info(group_obj):
    global group_info
    group_info = await client(GetFullChannelRequest(group_obj))


async def find_user(id_):
    try:
        return await client(GetFullUserRequest(int(id_)))
    except Exception as err:
        save_log(f"eception in find_user {err=}, {type(err)=}")


async def find_user_name(user_id):
    full = await find_user(user_id)
    try:
        global cur_username
        global message_user_name
        cur_username = ''
        debug_find = "1"
        if not full is None:
            if full.users and full.users[0] and hasattr(full.users[0], "username") and not full.users[
                                                                                               0].username is None:
                debug_find = "2"
                message_user_name = full.users[0].username
                debug_find = "3"
                cur_username = cur_username + '<a href="https://t.me/' + full.users[0].username + '">@' + full.users[
                    0].username + '</a>|'  # + 'userid:'# + str(user_id)
            if full.full_user and hasattr(full.full_user, "about") and not full.full_user.about is None:
                debug_find = "4"
                cur_username = cur_username + ' ' + full.full_user.about
            if full.users and full.users[0] and hasattr(full.users[0], "first_name") and not full.users[
                                                                                                 0].first_name is None:
                debug_find = "5"
                cur_username = cur_username + ' ' + full.users[0].first_name
            if full.users and full.users[0] and hasattr(full.users[0], "last_name") and not full.users[0].last_name is None:
                debug_find = "6"
                cur_username = cur_username + ' ' + full.users[0].last_name
            if full.users and full.users[0] and hasattr(full.users[0], "phone") and not full.users[0].phone is None:
                debug_find = "7"
                cur_username = cur_username + ' +' + full.users[0].phone

    except Exception as err:
        save_log(f"eception in find_user_name {err=}, {type(err)=} {debug_find=}")


async def find_messages(group=None):
    global history
    history = None
    if group:
        history = await client(GetHistoryRequest(
            peer=group,
            offset_id=offset_id,
            offset_date=None,
            add_offset=0,
            limit=max_messages_in_return,
            max_id=0,
            min_id=0,
            hash=0
        ))
        # print('group: ', offset_id, max_messages_in_return, '<br>')


async def send_mess(recipient, message):
    await client.send_message(entity=recipient, message=message, parse_mode='HTML')


def generate_answer(success=1, message='', values='', error_code=''):
    message = escape(message)
    message = message.replace('\\', '&#92;').replace('{', '&#123;').replace('[', '&#91;')

    return '{"success":' + str(
        success) + ', "message":"' + message + '", "error_code":"' + error_code + '", "values":' + json.dumps(
        values) + '}'


def read_code_from_file(file_name):
    for i in range(1, 1000):
        try:
            f = open(file_name)
            tel_code = f.read()
            f.close()
            if tel_code and len(tel_code) > 0:
                return tel_code
            time.sleep(1)
        except Exception:
            time.sleep(1)
    return False


def load_params_from_file_to_debug():
    global api_id, api_hash, phone, customer_id, debug_mode, max_exec_time_in_secs, debug_keyword, debug_stopword, debug_group_to_forward, maximum_messages, parse_messages_for_last_hours, passed_data, write_messages_on_screen, command_to_perfdorm, send_message_recipient, send_message_text, debug_dont_save_found_messages, ignore_messages_with_no_username, group_username

    save_log(f"load json file to debug")

    customers_file_path = os.path.dirname(os.path.realpath(__file__)) + '/customers.json'

    f = open(customers_file_path, encoding="utf8")
    customers = f.read()
    f.close()

    if customers and len(customers) > 0:
        customers_arr = json.loads(customers)
        api_id = customers_arr[0]['api_id']
        api_hash = customers_arr[0]['api_hash']
        phone = customers_arr[0]['phone']
        customer_id = customers_arr[0]['customer_id']
        try:
            debug_mode = customers_arr[0]['debug_mode']
            if debug_mode:
                max_exec_time_in_secs = 10000000
        except Exception:
            pass
        try:
            debug_keyword = customers_arr[0]['keywords']
            if 'stopwords' in customers_arr[0]:
                debug_stopword = customers_arr[0]['stopwords']

        except Exception:
            pass
        try:
            if 'group_to_forward' in customers_arr[0]:
                debug_group_to_forward = customers_arr[0]['group_to_forward']
            if 'maximum_messages' in customers_arr[0]:
                maximum_messages = int(customers_arr[0]['maximum_messages'])
            if 'parse_messages_for_last_hours' in customers_arr[0]:
                parse_messages_for_last_hours = customers_arr[0]['parse_messages_for_last_hours']
            if 'passed_data' in customers_arr[0]:
                passed_data = customers_arr[0]['passed_data']
            if 'write_messages_on_screen' in customers_arr[0]:
                write_messages_on_screen = customers_arr[0]['write_messages_on_screen']
            if 'command_to_perfdorm' in customers_arr[0]:
                command_to_perfdorm = customers_arr[0]['command_to_perfdorm']
            if "send_message_recipient" in customers_arr[0]:
                send_message_recipient = customers_arr[0]['send_message_recipient']
            if "send_message_text" in customers_arr[0]:
                send_message_text = customers_arr[0]['send_message_text']
            if "debug_dont_save_found_messages" in customers_arr[0]:
                debug_dont_save_found_messages = customers_arr[0]['debug_dont_save_found_messages']
            if "ignore_messages_with_no_username" in customers_arr[0]:
                ignore_messages_with_no_username = customers_arr[0]['ignore_messages_with_no_username']
            if "group_username" in customers_arr[0]:
                group_username = customers_arr[0]['group_username']

        except Exception:
            pass


# reading parameters from command line
n = len(sys.argv)
for i in range(1, n):
    key, value = sys.argv[i].split("=")

    if key == "api_id":
        api_id = value
    elif key == "api_hash":
        api_hash = value
    elif key == "phone":
        phone = value
    elif key == "bot_token":
        bot_token = value
    elif key == "password":
        password = value
    elif key == "password_2FA":
        password_2FA = value
    elif key == "code":
        sign_code = value
    elif key == "code_file_name":
        code_file_name = str(Path(__file__).parent.absolute()) + '/' + value
    elif key == "waiting_code_file_name":
        waiting_code_file_name = str(Path(__file__).parent.absolute()) + '/' + value
    elif key == "command":
        command_to_perfdorm = value
    elif key == "data":
        passed_data = value
        # save_log(f"data from command line: {value}")
    elif key == "debug_mode":
        debug_mode = value == '1'
    elif key == "write_messages_on_screen":
        write_messages_on_screen = value == '1'
    elif key == "send_message_recipient":
        send_message_recipient = value
    elif key == "send_message_text":
        send_message_text = value
    elif key == "maximum_messages":
        maximum_messages = int(value)
    elif key == "debug_dont_save_found_messages":
        debug_dont_save_found_messages = value == '1'
    elif key == "ignore_messages_with_no_username":
        ignore_messages_with_no_username = value == '1'
    elif key == "group_username":
        group_username = value
    elif key == "parse_messages_for_last_hours":
        parse_messages_for_last_hours = int(value)
    elif key == "ignore_message_ids":
        ignore_message_ids_arr = value.split('|')
        save_log(f"ignore_message_ids: {value}")
     

if len(phone) == 0:
    # load json file to debug
    load_params_from_file_to_debug()

if command_to_perfdorm == 'connect_to_debug':
    try:
        # Connect to the Telegram
        client = TelegramClient(phone, api_id, api_hash)
        client.start()
        print("client started")

    except Exception as err:
        print(f"Exception: {err=}", traceback.format_exc())

    sys.exit()

if command_to_perfdorm == 'send_code_request':
    if len(code_file_name) > 0:
        try:
            os.remove(code_file_name)
        except Exception:
            pass
    if len(waiting_code_file_name) > 0:
        try:
            os.remove(waiting_code_file_name)
        except Exception:
            pass

        try:
            f = open(waiting_code_file_name, "x")
            f.write("1")
            f.close()
        except Exception:
            print(generate_answer(0, 'cannot create waiting_code_file_name: ' + str(waiting_code_file_name)))
            sys.exit()

if command_to_perfdorm == 'do_job' or command_to_perfdorm == 'send_code_request':
    try:
        if len(phone) == 0:
            exit_error = ERROR_NO_PHONE
            sys.exit()

        # Retrieve the list of keywords from command line
        data_arr = []
        keywords_arr = []
        keywords_and_arr = []
        found_keywords_arr = []
        stopwords_arr = []
        data_json = ''
        groups_to_monitor = []

        if len(passed_data) > 0:
            try:
                data_arr = json.loads(bytes.fromhex(passed_data).decode('utf-8'))
                if "keywords" in data_arr:
                    for i in range(len(data_arr['keywords'])):
                        try:
                            # if write_messages_on_screen:
                            #    print("keyword orig: ", data_arr['keywords'][i], "<br>")
                            #save_log(f"keyword: {data_arr['keywords'][i]}")
                            decoded_wrd = str(bytes.fromhex(data_arr['keywords'][i]).decode('utf-8'))
                            #save_log(f"decoded keyword: {decoded_wrd}")
                            
                            keywords_arr.append({"keyword": decoded_wrd, "orig": data_arr['keywords'][i]})

                            if write_messages_on_screen:
                               print("keyword: ", str(decoded_wrd), "<br>")
                        except Exception as err:
                            save_log(
                                f"eception in processing data keyword {err=}, {type(err)=} keyword: {data_arr['keywords'][i]} data: {passed_data}")
                            exit_error = WARNING_WRONG_KEYWORD
                            exit_message = data_arr['keywords'][i]
                            pass
                
                if "keywords_and" in data_arr:
                    for i in range(len(data_arr['keywords_and'])):
                        try:
                            decoded_wrd = str(bytes.fromhex(data_arr['keywords_and'][i]).decode('utf-8'))
                            save_log(f"decoded keyword and: {decoded_wrd}")
                            
                            keywords_and_arr.append({"keyword": decoded_wrd, "orig": data_arr['keywords_and'][i]})

                            if write_messages_on_screen:
                               print("keyword and: ", str(decoded_wrd), "<br>")
                        except Exception as err:
                            save_log(
                                f"eception in processing data keyword and {err=}, {type(err)=} keyword: {data_arr['keywords_and'][i]} data: {passed_data}")
                            exit_error = WARNING_WRONG_KEYWORD
                            exit_message = data_arr['keywords_and'][i]
                            pass

                if "stopwords" in data_arr:
                    for i in range(len(data_arr['stopwords'])):
                        try:
                            decoded_wrd = str(bytes.fromhex(data_arr['stopwords'][i]).decode('utf-8'))
                            stopwords_arr.append(decoded_wrd)
                            # if write_messages_on_screen:
                            #    print("stop word: ", str(decoded_wrd), "<br>")
                            # stopwords_arr.append(base64.b64decode(data_arr['stopwords'][i]).decode('utf-8'))
                        except Exception as err:
                            if write_messages_on_screen:
                                print("exception stop word: ", data_arr['stopwords'][i], "<br>")
                            # save_log(f"eception in processing data stopword {err=}, {type(err)=}")
                            exit_error = WARNING_WRONG_STOPWORD
                            exit_message = data_arr['stopwords'][i]
                            pass
                
                if "groups" in data_arr:
                    for i in range(len(data_arr['groups'])):
                        try:
                            groups_to_monitor.append(data_arr['groups'][i])
                        except Exception as err:
                            save_log(f"eception in processing data groups {err=}, {type(err)=}")
                            pass

                # print('groups_to_monitor: ', groups_to_monitor, '<br>')

            except Exception as err:
                save_log(f"eception in processing data {err=}, {type(err)=}")
                pass

        if len(keywords_arr) == 0 and len(debug_keyword) > 0:
            # keywords_arr.append({"keyword":debug_keyword, "orig":base64.b64encode(debug_keyword.encode('utf-8')).decode('utf-8')})
            keywords_arr.append({"keyword": debug_keyword, "orig": debug_keyword.encode('utf-8').hex()})

        if len(stopwords_arr) == 0 and len(debug_stopword) > 0:
            stopwords_arr.append(debug_stopword)

        # Connect to the Telegram
        #save_log(f"connecting: '{phone}', {api_id}, {api_hash}")
        client = TelegramClient(phone, api_id, api_hash)
        debug_step = "0.1"
        client.connect()
        debug_step = "0.2"
        #save_log(f"sign_in 2FA password: {password_2FA}")
        if not client.is_user_authorized():
            debug_step = "0.3"
            if command_to_perfdorm == 'do_job':
                exit_error = ERROR_NOT_AUTHORIZED
                # save_log(f"{phone=} not started")
                sys.exit()
            debug_step = "0.4"
            if len(code_file_name) == 0:
                exit_error = ERROR_NO_CODE_FILE_NAME
                sys.exit()
            debug_step = "0.5"
            #save_log(f"send_code_request")
            client.send_code_request(phone)
            save_log(f"read_code_from_file, password: {password_2FA}")
            tl_code = read_code_from_file(code_file_name)
            save_log(f"sign_in {tl_code}, password: {password_2FA}")
            try:
                client.sign_in(phone=phone, code=tl_code, password=password_2FA)
            except SessionPasswordNeededError:
                client.sign_in(password=password_2FA)

            #save_log(f"signed")
        client.start()

        if not command_to_perfdorm == 'do_job':
            save_log(f"{phone=} started")

        if command_to_perfdorm == 'do_job':

            # Read list of already sent messages
            messages_file_path = str(Path(__file__).parent.absolute()) + '/' + 'sent_messages_' + api_hash + '.json'
            sent_messages_txt = ''
            try:
                f = open(messages_file_path, "r")
                sent_messages_txt = f.read()
                f.close()
            except Exception:
                pass

            if sent_messages_txt and len(sent_messages_txt) > 0:
                found_messages_arr = json.loads(sent_messages_txt)
            
            if len(group_username) == 0:
                # Search for chats
                with client:
                    client.loop.run_until_complete(find_chats())

                # Add to the groups array chats, which are created by owner or which are megagroups
                for chat in chats:
                    try:
                        groups.append(chat)
                    except:
                        continue

                # sort groups alphabetically
                groups = sorted(groups, key=lambda a_group: a_group.title, reverse=False)
            else:
                grp = None

                with client:
                    client.loop.run_until_complete(find_group(group_username))

                groups.append(grp)
                groups_to_monitor.append({'group_id': str(grp.id), 'group_status': 'l'})

            # Make json record with list of groups
            groups_json = ''
            i = 0
            for g in groups:
                group_n = base64.b64encode(g.title.encode('utf-8')).decode('utf-8')
                item_json = f'"group_name" : "{group_n}", "group_id" : "{g.id}", "username" : "{"unknown" if not hasattr(g, "username") else g.username}"'
                groups_json = groups_json + (',' if len(groups_json) > 0 else '') + '{' + item_json + '}'
                if debug_mode:
                    if str(g.id) == str(debug_group_to_forward):
                        groups_to_monitor.append({'group_id': str(g.id), 'group_status': 'a'})
                    else:
                        groups_to_monitor.append({'group_id': str(g.id), 'group_status': 'l'})
                i += 1

            groups_json = '"groups":[' + groups_json + ']'
            data_json = data_json + (', ' if len(data_json) > 0 else '') + groups_json

            # sort groups in random order
            random.shuffle(groups)

            for group_to_monitor in groups_to_monitor:
                # if group does not have the "listen" flag then reject it
                if group_to_monitor['group_status'] != 'l':
                    continue

                # search for the group object by given id
                group_id = group_to_monitor['group_id']

                target_group_username = ''
                target_group_title = ''

                grop_found = False
                for g in groups:
                    if group_id == str(g.id):
                        target_group = g
                        grop_found = True
                        try:
                            target_group_username = target_group.username
                        except Exception as err:
                            pass
                        try:
                            target_group_title = target_group.title
                        except Exception as err:
                            pass
                        if write_messages_on_screen:
                            print(
                                f"Searching in group: @{target_group_username} >> '{target_group_title}' for last {parse_messages_for_last_hours} hours<br>")
                        break

                debug_step = "1"

                offset_id = 0

                while grop_found:

                    if (time.time() - script_started) > max_exec_time_in_secs:
                        break

                    # retrive the group messages
                    with client:
                        try:
                            client.loop.run_until_complete(find_messages(group=target_group))
                        except Exception as err:
                            pass

                    debug_step = "1.2"

                    if not history or not history.messages:
                        break
                    messages = history.messages
                    if write_messages_on_screen:
                        print(len(messages), ' messages found in: ', target_group_title, '<br>')
                    
                    save_log(str(len(messages)) + ' messages found in: @' + target_group_username + ' (' + target_group_title + ')')

                    debug_step = "2"

                    # discard messages which are created long time ago
                    if len(messages) > 0 and (time.time() + time.timezone) - time.mktime(
                            messages[0].date.timetuple()) > parse_messages_for_last_hours * 60 * 60:
                        save_log(f'All messages discarded because all messages are oldest than {parse_messages_for_last_hours} hours')
                        break

                    for message in messages:
                        try:
                            if (time.time() + time.timezone) - time.mktime(
                                    message.date.timetuple()) > parse_messages_for_last_hours * 60 * 60:
                                # if write_messages_on_screen:
                                #    print("message sent hours ago:", ((time.time() + time.timezone) - time.mktime(message.date.timetuple())) / 60 / 60, "<br>", message.message, "<br>")
                                break

                            msg_user_id = message.sender_id  # message.from_id.user_id

                            if not message.message or len(message.message) == 0:
                                continue
                            if str(message.id) in ignore_message_ids_arr:
                                save_log(f"Message {str(message.id)} already processed")
                                continue

                            #if write_messages_on_screen:
                            #    print(f"{message.date} {message.message}<br>")
                            
                            #save_log(f"{message.message}")

                            # look for any of stopword in message
                            stopword_found = False
                            for stopword in stopwords_arr:
                                if stopword.find("/") == 0:
                                    srch = stopword.removeprefix("/")
                                    x = re.search(srch, message.message, flags=re.I + re.M)
                                    if x:
                                        stopword_found = True
                                        #if write_messages_on_screen:
                                        #    print(f"Found stopword {stopword}<br>")
                                        break
                                else:
                                    if message.message.lower().find(stopword.lower()) >= 0:
                                        stopword_found = True
                                        # if write_messages_on_screen:
                                        #    print(f"Found stopword {stopword}<br>")
                                        break
                            if stopword_found:
                                continue

                            debug_step = "3"

                            # look for any of keyword in message
                            keyword_found = False
                            keyword_which_found = ''
                            keyword_which_found_orig = ""
                            
                            for keyword_dic in keywords_arr:
                                keyword = keyword_dic["keyword"]
                                #save_log(f"Searching for keyword: {keyword}")
                                
                                if write_messages_on_screen:
                                   print(f"Searching for keyword: {keyword}<br>")
                                   
                                if keyword.find("/") == 0:
                                    srch = keyword.removeprefix("/")
                                    
                                    x = re.search(srch, message.message, flags=re.I)
                                    if x:
                                        keyword_found = True
                                        keyword_which_found = keyword
                                        keyword_which_found_orig = keyword_dic["orig"]
                                        if write_messages_on_screen:
                                            print(f"Found keyword {keyword}<br>")
                                        break
                                else:
                                    if message.message.lower().find(keyword.lower()) >= 0:
                                        keyword_found = True
                                        keyword_which_found = keyword
                                        keyword_which_found_orig = keyword_dic["orig"]
                                        if write_messages_on_screen:
                                            print(f"Found keyword {keyword}<br>")
                                        break
                            
                            for keyword_dic in keywords_and_arr:
                                keyword = keyword_dic["keyword"]
                                save_log(f"Searching for keyword and: {keyword}")
                                if write_messages_on_screen:
                                   print(f"Searching for keyword: {keyword}<br>")
                                   
                                if keyword.find("/") == 0:
                                    srch = keyword.removeprefix("/")
                                    #save_log(f"Searching for keyword: {srch} in: {message.message}")
                                    x = re.search(srch, message.message, flags=re.I)
                                    if x:
                                        keyword_found = True
                                        keyword_which_found = keyword
                                        keyword_which_found_orig = keyword_dic["orig"]
                                        if write_messages_on_screen:
                                            print(f"Found keyword {keyword}<br>")
                                    else:
                                        keyword_found = False
                                        break
                                else:
                                    if message.message.lower().find(keyword.lower()) >= 0:
                                        keyword_found = True
                                        keyword_which_found = keyword
                                        keyword_which_found_orig = keyword_dic["orig"]
                                        if write_messages_on_screen:
                                            print(f"Found keyword {keyword}<br>")
                                    else:
                                        keyword_found = False
                                        break


                            debug_step = "3.1"
                            if keyword_found:
                                debug_step = "3.2"
                                # make sure that this message has not been processed before
                                message_already_processed = False
                                debug_step = "3.3"
                                for sent_message_id in found_messages_arr:
                                    try:
                                        debug_step = "3.4"
                                        if str(sent_message_id['message_id']) == str(message.id):
                                            if not debug_mode:
                                                message_already_processed = True
                                            # save_log(f"mesage {sent_message_id['message_id']} already processed")
                                            if write_messages_on_screen:
                                                print(f"mesage {sent_message_id['message_id']} already processed<br>")
                                            break
                                    except Exception as err:
                                        save_log(f"exception in finding processed message` {err=}, {type(err)=}")

                                debug_step = "4"
                                if not message_already_processed:

                                    debug_step = "4.7"
                                    cur_username = ""
                                    message_user_name = ""

                                    with client:
                                        client.loop.run_until_complete(find_user_name(msg_user_id))

                                    if message_user_name is None or len(message_user_name) <= 0:
                                        try:
                                            cur_username_re = re.findall('([^0-9a-zA-Z_-]@[0-9a-zA-Z_]+)',
                                                                         message.message, flags=re.I)
                                            found_addresses = len(cur_username_re)
                                            if found_addresses > 0:
                                                message_user_name = cur_username_re[0].strip().replace("@", "")
                                                if write_messages_on_screen:
                                                    print(
                                                        f"Found user_name: '{message_user_name}' in: {message.message}<br>")
                                                    # sys.exit()

                                        except Exception:
                                            pass

                                    if ignore_messages_with_no_username and (
                                            message_user_name is None or len(message_user_name) <= 0):
                                        if write_messages_on_screen:
                                            print(
                                                f"Discarded! Message has no user name: {message.date} {message.message}<br>")
                                        # save_log(f"Message has no user name")
                                        continue

                                    debug_step = "4.8"
                                    if not isinstance(cur_username, str):
                                        cur_username = ""

                                    found_keywords_arr.append(
                                        {"keyword": keyword_which_found, "orig": keyword_which_found_orig,
                                         "username": message_user_name, "message_id": str(message.id),
                                         "group_username": target_group_username, "message_text": str(message.message)})
                                    save_log('Found keyword: ' + str(keyword_which_found) + ', orig: ' + str(
                                        keyword_which_found_orig) + ', username: ' + str(message_user_name))

                                    if len(cur_username) <= 0:
                                        try:
                                            cur_username = target_group_username
                                        except Exception as err:
                                            pass

                                    try:

                                        message_text = '<b><a href="https://t.me/' + target_group_username + "/" + str(
                                            message.id) + '/">&#128161;</a></b>' + message.message + '\n&#128101; @' + target_group_username + '  \n' + '<a href="https://t.me/' + target_group_username + '/' + str(
                                            message.id) + '/">&#128172; message  &#128072;</a>\n'
                                        if not message_user_name is None and len(message_user_name) > 0:
                                            message_text = message_text + '&#128100; @' + message_user_name + '\n'
                                        message_text = message_text + '&#128273;' + keyword_which_found
                                        # message_text = message_text + '<b><a href="https://t.me/' + target_group_username + "/" + str(message.id) + '/">&#128273;' + keyword_which_found + '</a></b>\n'

                                        '''
                                        message_text = '&#128101; <a href="https://t.me/' + target_group_username + '/">' + target_group_username + ' </a>\n' + '<a href="https://t.me/' + target_group_username + '/' + str(message.id) + '/">&#128172; message  </a>\n'
                                        if not message_user_name is None and len(message_user_name) > 0:
                                            message_text = message_text + '&#128100; @' + message_user_name + '\n'
                                        message_text = message_text + '&#128273;' + keyword_which_found + '\n' + message.message
                                        '''
                                        # message_text = cur_username + "\n" + '<b><a href="https://t.me/' + target_group_username + "/" + str(message.id) + '/">&#128273;' + keyword_which_found + '</a></b>\n' + message.message

                                        # message_text = '<a href="https://t.me/' + target_group_username + "/" + str(message.id) + '/">' + cur_username + "</a>\n" + '&#128273;<b>' + keyword_which_found + '</b>\n' + message.message
                                        # save_log(message_text)
                                        if write_messages_on_screen:
                                            print(f"sending message: {message_text}")
                                    except Exception as err:
                                        save_log(f"exception to make message text ` {err=}, {type(err)=}")
                                        pass
                                    
                                    admin_group_found = False
                                    # forward this message to the admin groups
                                    for group_of_admins in groups_to_monitor:
                                        #save_log('group: ' + str(group_of_admins['group_id']) + ', status: ' + str(group_of_admins['group_status']))
                                        if group_of_admins['group_status'] == 'a':
                                            admin_group_found = True
                                            #save_log('admin group found: ' + str(group_of_admins['group_id']))
                                            for group_object in groups:
                                                #save_log('group: ' + str(group_object.id))
                                                if group_of_admins['group_id'] == str(group_object.id):
                                                    try:
                                                        debug_step = "5.1"
                                                        save_log('Sending message: ' + message_text)
                                                        with client:
                                                            client.loop.run_until_complete(send_mess(group_object, message_text))
                                                        save_log('Sent message id: ' + str(message.id) + ' to group: ' + group_object.title)
                                                        if write_messages_on_screen:
                                                            print('Sent message id: ' + str(message.id) + ' to group: ' + group_object.title)
                                                        break
                                                    except Exception as err:
                                                        save_log(f"eception in sending message {err=}, {type(err)=}")
                                            else:
                                                save_log(f"Error: admin group with id: {str(group_of_admins['group_id'])} not found")
                                    
                                    if not admin_group_found:
                                        save_log(f"Error: no admin groups found")

                                    debug_step = "5.2"
                                    found_messages_arr.append({'message_id': message.id,
                                                               'unix_time': str(round(time.time() + time.timezone))})
                                    m = message.message[0:256]
                                    # b = m.encode(encoding="ascii", errors="xmlcharrefreplace")
                                    # m = b.decode("utf-8")

                                    keyword_which_found_entity = keyword_which_found
                                    # try:
                                    #    b = keyword_which_found.encode(encoding="ascii", errors="xmlcharrefreplace")
                                    #    keyword_which_found_entity = b.decode("utf-8")
                                    # except Exception as err:
                                    #    pass

                                    m = '&#128273; ' + str(keyword_which_found_entity) + ' &#10140; ' + str(
                                        m) + ' &#8592; @' + str(target_group_username)
                                    all_messages.append(str(m))
                                    if write_messages_on_screen:
                                        print('Found message: ', message.date.strftime('%Y-%m-%d %H:%m'),
                                              message.message)
                                    debug_step = "5.3"
                                    save_log('Found new message ' + str(m))
                                    if (message_user_name is None or len(message_user_name) <= 0):
                                        save_log(f"Message has no user name")

                            debug_step = "6"
                            if ((maximum_messages != 0 and len(all_messages) >= maximum_messages)):
                                '''or (not message_user_name is None and len(message_user_name) > 0)'''
                                break
                        except Exception as err:
                            if write_messages_on_screen:
                                print('\033[91m' + f"Unexpected {err=}, {type(err)=}, {debug_step=}" + '\033[0m')
                                print('\033[91m' + f"mes: {message.message=}, {keyword=}" + '\033[0m')
                            save_log(f"eception in processing message {err=}, {type(err)=} debug_step: " + debug_step)
                    debug_step = "7"
                    offset_id = messages[len(messages) - 1].id
                    debug_step = "8"
                    if ((maximum_messages != 0 and len(all_messages) >= maximum_messages)):
                        break
                if ((maximum_messages != 0 and len(all_messages) >= maximum_messages)):
                    break
            if not debug_dont_save_found_messages:
                debug_step = "9"
                f = open(messages_file_path, "w")
                f.write(json.dumps(found_messages_arr))
                f.close()

        debug_step = "10"
        data_json = data_json + (', ' if len(data_json) > 0 else '') + '"found_messages":' + json.dumps(
            all_messages) + ', "found_keywords":' + json.dumps(found_keywords_arr)
        debug_step = "11"
        data_json = '{' + data_json + '}'
        print(generate_answer(1, exit_message, base64.b64encode(data_json.encode('utf-8')).decode("utf-8"), exit_error))
    except BaseException as e:
        print(generate_answer(0, 'exception in the Telegram connect: ' + str(e), '', exit_error))
        save_log('Exception in the Telegram connect: ' + str(e) + " debug_step: " + debug_step)

    debug_step = "12"
    if len(code_file_name) > 0:
        try:
            os.remove(code_file_name)
        except Exception:
            pass

    if len(waiting_code_file_name) > 0:
        try:
            os.remove(waiting_code_file_name)
        except Exception:
            pass
    save_log('exit')
    sys.exit()

elif command_to_perfdorm == 'save_code':
    if len(code_file_name) > 0:
        try:
            os.remove(code_file_name)
        except Exception:
            pass

        try:
            f = open(code_file_name, "x")
            f.write(sign_code)
            f.close()
        except Exception:
            print(generate_answer(0, 'cannot create code_file_name: ' + str(waiting_code_file_name)))
            sys.exit()
        print(generate_answer(1, 'code written in code_file_name'))
    else:
        print(generate_answer(0, 'file name is blank'))

elif command_to_perfdorm == 'is_send_code_request_waiting':
    try:
        if len(waiting_code_file_name) > 0:
            print(generate_answer(1, '', os.path.isfile(waiting_code_file_name)))
        else:
            print(generate_answer(1, '', False))
    except Exception:
        print(generate_answer(0, 'an error'))

elif command_to_perfdorm == 'send_message':
    save_log('send_message request: ' + str(send_message_recipient) + ', send_message_text: ' + str(send_message_text))
    if not send_message_recipient or len(send_message_recipient) == 0 or not send_message_text or len(
            send_message_text) == 0:
        print(generate_answer(0, 'Error: empty send_message_recipient or send_message_text'))
        sys.exit()

    try:
        # Connect to the Telegram
        client = TelegramClient(phone, api_id, api_hash)
        debug_step = "0.1"
        client.connect()
        debug_step = "0.2"
        if not client.is_user_authorized():
            debug_step = "0.3"
            if command_to_perfdorm == 'do_job':
                exit_error = ERROR_NOT_AUTHORIZED
                sys.exit()
            debug_step = "0.4"
            if len(code_file_name) == 0:
                exit_error = ERROR_NO_CODE_FILE_NAME
                sys.exit()
            debug_step = "0.5"
            client.send_code_request(phone)
            tl_code = read_code_from_file(code_file_name)
            client.sign_in(phone=phone, code=tl_code)

        client.start()

        send_message_text = bytes.fromhex(send_message_text).decode('utf-8')

        # with client:
        #    client.loop.run_until_complete(
        #        send_mess(send_message_recipient, send_message_text))

        print(generate_answer(1, 'message to @' + send_message_recipient + ' has been sent '))
        save_log('message to:' + send_message_recipient + ', ' + send_message_text)

    except BaseException as e:
        print(generate_answer(0, 'exception in send_message: ' + str(e), '', exit_error))
        save_log('Exception in send_message: ' + str(e) + " debug_step: " + debug_step)

elif command_to_perfdorm == 'get_group_info':
    
    exit_error = ERROR_NO_SUCH_GROUP

    if not group_username or len(group_username) == 0:
        print(generate_answer(0, 'Error: empty group_username', '', exit_error))
        sys.exit()

    try:
        # Connect to the Telegram
        client = TelegramClient(phone, api_id, api_hash)
        debug_step = "0.1"
        client.connect()

        debug_step = "0.2"
        if not client.is_user_authorized():
            debug_step = "0.3"
            if command_to_perfdorm == 'do_job':
                exit_error = ERROR_NOT_AUTHORIZED
                sys.exit()
            debug_step = "0.4"
            if len(code_file_name) == 0:
                exit_error = ERROR_NO_CODE_FILE_NAME
                sys.exit()
            debug_step = "0.5"
            client.send_code_request(phone)
            tl_code = read_code_from_file(code_file_name)
            client.sign_in(phone=phone, code=tl_code)

        client.start()

        grp = None

        with client:
            client.loop.run_until_complete(find_group(group_username))

        if grp != None:
            group_title = ''
            group_participants_count = 0
            group_about = ''

            group_title = grp.title

            group_info = None
            with client:
                client.loop.run_until_complete(get_group_info(grp))

            if group_info != None:

                group_participants_count = group_info.full_chat.participants_count

                group_about = group_info.full_chat.about

                with client:
                    try:
                        client.loop.run_until_complete(find_messages(group=grp))
                    except Exception as err:
                        pass

                debug_step = "1.2"

                messages = history.messages
                if write_messages_on_screen:
                    print(len(messages), ' messages found in: ', group_title, '<br>')

                debug_step = "2"
                all_messages_from_group = ''

                # if (time.time() + time.timezone) - time.mktime(message.date.timetuple()) > parse_messages_for_last_hours * 60 * 60:
                unixtime_of_nevest_message = 0
                unixtime_of_first_message = 0
                number_of_not_null_messages = 0
                time_interval_between_messages = 0

                for message in messages:
                    try:
                        debug_step = "2.1"
                        all_messages_from_group = all_messages_from_group + ' ' + message.message.lower()
                        if len(message.message) > 5:
                            if unixtime_of_nevest_message == 0:
                                unixtime_of_nevest_message = time.mktime(message.date.timetuple())
                            unixtime_of_first_message = time.mktime(message.date.timetuple())
                            number_of_not_null_messages = number_of_not_null_messages + 1
                    except:
                        pass

                language = ''
                try:
                    language = detect_language(all_messages_from_group)
                    #detect_language = classify(all_messages_from_group)
                    #language = detect_language[0]
                except:
                    pass
                
                debug_step = "2.2"

                if number_of_not_null_messages > 0:
                    time_interval_between_messages = (
                                                                 unixtime_of_nevest_message - unixtime_of_first_message) / number_of_not_null_messages / 60
                    if time_interval_between_messages > 0:
                        time_interval_between_messages = time_interval_between_messages.__round__(0)
                        if time_interval_between_messages < 1:
                            time_interval_between_messages = 1

                try:
                    debug_step = "2.3"
                    spec_chars = string.punctuation + '\n\xa0«»\t—…'
                    # all_messages_from_group = "".join([ch for ch in all_messages_from_group if ch not in spec_chars])

                    all_messages_from_group = re.sub('[' + spec_chars + ']', ' ', all_messages_from_group)
                    all_messages_from_group = re.sub('[^\x00-\x7Fа-яА-Я]', ' ', all_messages_from_group)
                    all_messages_from_group = re.sub('[0-9]+', ' ', all_messages_from_group)

                    # if write_messages_on_screen:
                    #    print('downloaded : ', len(all_messages_from_group), 'chars<br>')
                    group_tokens = word_tokenize(all_messages_from_group)

                    russian_stopwords = stopwords.words("russian")

                    stopwords_arr = []
                    stopwords_extend = ''
                    f = open(os.path.dirname(os.path.realpath(__file__)) + '/stop_words_ru.json', encoding="utf8")
                    stopwords_extend = f.read()
                    f.close()

                    if stopwords_extend and len(stopwords_extend) > 0:
                        stopwords_arr = stopwords_arr + json.loads(stopwords_extend)

                    stopwords_extend = ''
                    f = open(os.path.dirname(os.path.realpath(__file__)) + '/stop_words_en.json', encoding="utf8")
                    stopwords_extend = f.read()
                    f.close()
                    debug_step = "2.4"
                    if stopwords_extend and len(stopwords_extend) > 0:
                        stopwords_arr = stopwords_arr + json.loads(stopwords_extend)

                    english_stopwords = stopwords.words("english")

                    group_tokens = [token for token in group_tokens if
                                    token not in russian_stopwords and token not in punctuation and token not in english_stopwords and len(
                                        token) > 2]
                    stemmer = RussianStemmer()
                    group_tokens = [stemmer.stem(token) for token in group_tokens]

                    text = nltk.Text(group_tokens)
                    fdist = FreqDist(text)

                    group_symantic_core = ''
                    group_symantic_words = 0
                    if len(fdist.most_common(1)) > 0:
                        most_common_number = fdist.most_common(1)[0][1]
                        debug_step = "2.5"
                        for token, freq in fdist.most_common(100):
                            stopword_found = False
                            for stopword in stopwords_arr:
                                # if stopword in token:
                                if len(stopword) < 5:
                                    if token == stopword:
                                        stopword_found = True
                                        break
                                else:
                                    if token.find(stopword) == 0:
                                        stopword_found = True
                                        break
                            if not stopword_found:
                                group_symantic_core = group_symantic_core + token + ','
                                group_symantic_words = group_symantic_words + 1
                                if group_symantic_words > 100:
                                    break
                            if freq < most_common_number / 50:
                                break
                except:
                    print(
                        generate_answer(0, 'exception in get_group_info: ' + str(e) + " debug_step: " + debug_step, '',
                                        exit_error))
                    pass
        print(generate_answer(1, '', {"group_title": group_title, "group_about": group_about,
                                      "group_participants_count": group_participants_count,
                                      "minutes_interval_between_messages": time_interval_between_messages,
                                      "unixtime_of_nevest_message": unixtime_of_nevest_message,
                                      "group_symantic_core": group_symantic_core, "language":str(language)}))
        #save_log('group: ' + group_username + ' has been parsed ')

    except BaseException as e:
        print(generate_answer(0, 'exception in get_group_info: ' + str(e), '', exit_error))
        save_log('Exception in get_group_info: ' + str(e) + " debug_step: " + debug_step)

