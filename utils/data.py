import json
from utils.config import DATA_FILE, SENT_CODES_FILE, GUILD_SETTINGS_FILE, UID_DATA_FILE, SENT_VIDEOS_FILE

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"fortune_dates": {}, "gacha_pity": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_sent_codes():
    try:
        with open(SENT_CODES_FILE, "r") as f:
            data = json.load(f)
            return {k: set(v) for k, v in data.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_sent_codes(codes_dict):
    data = {k: list(v) for k, v in codes_dict.items()}
    with open(SENT_CODES_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_guild_settings():
    try:
        with open(GUILD_SETTINGS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_guild_settings(settings):
    with open(GUILD_SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

def load_uid_data():
    try:
        with open(UID_DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_uid_data(data):
    with open(UID_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_sent_videos():
    try:
        with open(SENT_VIDEOS_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_sent_videos(sent_videos):
    with open(SENT_VIDEOS_FILE, "w") as f:
        json.dump(list(sent_videos), f)

def get_channels_for_type(guild_settings, notify_type):
    channels = []
    for guild_id, settings in guild_settings.items():
        if notify_type in settings:
            channels.append(settings[notify_type])
    return channels
