import json
import datetime
import os
import random
import streamlit as st
def load_json(file):
    with open(file, "r") as f:
        return json.load(f)

def load_data():
    return {
        "pages": ["Home", "Bravais", "Inverse Bravais", "Sheet TPMS", "Skeletal TPMS", "Strut-based"],
        "descriptions": load_json("desc_dict.json"),
        "crystal_images": load_json("crystal_images.json"),
        "subtypes_info": load_json("subtype_info.json"),
        "params_dict": {int(k): v for k, v in load_json("param_Dict.json").items()},
        "dict_key_map": {int(k): v for k, v in load_json("dict_key_map.json").items()},
        "system_prompt": open("instruction.txt").read()
    }
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def get_drive():
    gauth = GoogleAuth()
    gauth.ServiceAuth()  # <-- IMPORTANT
    return GoogleDrive(gauth)

drive = get_drive()

def append_to_jsonl(file_id, entry: dict):
   
     # 1. Download current file
    logs = drive.CreateFile({'id': file_id})
    print(f"Downloaded file: {file_id}")
    content = logs.GetContentString()

    # 2. Append new JSON line
    content += json.dumps(entry) + "\n"
    print(f"File {file_id} appended with entry: {entry}")
    # 3. Upload updated file
    logs.SetContentString(content)
    logs.Upload()
    print(f"File {file_id} updated")

def user_name():
    username = ''
    for i in range(8):
        username += str(random.randint(1, 9))
    return username

if 'username' not in st.session_state:
    st.session_state['username'] = user_name()
    username = st.session_state['username']
else:
    username = st.session_state['username']
ALL_LOGS_drive = "1eTJ0qRUJNLrlHkS9uZkc5UbTr5Ax5vxQ"
ALL_LOGS, CHAT_HISTORY = '.logs/all_logs.jsonl', '.logs/chat_history.jsonl'
def log_message(role, content):
    """Append a chat message to a JSONL log file with timestamp."""
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),"username": st.session_state['username'],
        "role": role,
        "content": content
    }
    with open(CHAT_HISTORY, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
    with open(ALL_LOGS, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

def log_to_drive(log_file, drive_file):
   
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            append_to_jsonl(drive_file, json.loads(line))
            print(f"{drive_file} updated with: {line}")

def clear_drive_files(drive_file):
    file = drive.CreateFile({'id': drive_file})
    file.SetContentString("")    # overwrite with empty string
    file.Upload()

def json_check(file):
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                return True
        return False
BUTTON_HISTORY = '.logs/button_history.jsonl'
def log_event(button_name,mode):
    
    if 'username' not in st.session_state:
        st.session_state['username'] = user_name()
        log_entry = {
        "timestamp": datetime.datetime.now().isoformat(), "username": st.session_state['username'],
        "button name": button_name,
        "mode": mode
        }
        with open(ALL_LOGS, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(), "username": st.session_state['username'],
        "button name": button_name,
        "mode": mode
    }

    if button_name != 'App opened':
        with open(BUTTON_HISTORY, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        with open(ALL_LOGS, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

LOG_SLIDER_CHANGES_TEMPORARY =  '.logs/log_slider_changes_temporary.jsonl'
LOG_SLIDER_CHANGES_PERMANENT = '.logs/log_slider_changes_permanent.jsonl'
def log_slider_changes(param_dict,mode):
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(), "username": username,
        "param_dict": param_dict,
        "mode": mode
    }

    # Read existing entries
    existing_entries = []
    with open(LOG_SLIDER_CHANGES_TEMPORARY, "r", encoding="utf-8") as f:
        for line in f:
            try:
                existing_entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    # Check if the same param_dict already exists
    existing_param_dicts = [entry["param_dict"] for entry in existing_entries]

    if existing_param_dicts != [] and param_dict != existing_param_dicts[-1]:
        # Append to log files
        with open(LOG_SLIDER_CHANGES_TEMPORARY, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        with open(ALL_LOGS, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        with open(LOG_SLIDER_CHANGES_PERMANENT, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        return True
    elif existing_entries == []:
        with open(LOG_SLIDER_CHANGES_TEMPORARY, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        with open(LOG_SLIDER_CHANGES_PERMANENT, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        return True

LOG_SUBMISSION = '.logs/log_submission.jsonl'
def log_submission(struc_info, design_ques,mode):
    log_entry = {"timestamp": datetime.datetime.now().isoformat(),
        "username": username,
        "Design Question": design_ques,
        "Parameter dict": struc_info,
        "Mode": mode
    }
    with open(LOG_SUBMISSION, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
    with open(ALL_LOGS, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

LOG_SUBMISSION_FINAL = '.logs/log_submission_final.jsonl'

def process_log_submission():
    design_ques_dict = []
    len_file = 0
    with open(LOG_SUBMISSION, "r", encoding="utf-8") as file:
        for line in file:
            len_file += 1
        for i in range(len_file-1, -1, -1):
            if file[i]["Design Question"] not in list(design_ques_dict.keys()):
                design_ques_dict.append(file[i]['Design Question'])
                with open(LOG_SUBMISSION_FINAL, "a", encoding="utf-8") as file2:
                    file2.write(json.dumps(file[i]) + "\n")


def log_close_app():

    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "username": st.session_state['username'],
        "event": "close app",
    }
    existing_entries = []
    with open(ALL_LOGS, "r", encoding="utf-8") as f:
        for line in f:
                existing_entries.append(json.loads(line))
    
    count = 0
    for entry in existing_entries:
        if "username" in entry.keys():
            pass
        else:
            count += 1
    
    if count == len(existing_entries):
        
        with open(ALL_LOGS, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
