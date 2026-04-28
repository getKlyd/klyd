import json
from pathlib import Path

def get_config_path():
    return Path('.keel') / 'config.json'

def init_config():
    keel_dir = Path('.keel')
    keel_dir.mkdir(exist_ok=True)
    
    config_path = get_config_path()
    if not config_path.exists():
        with open(config_path, 'w') as f:
            json.dump({}, f, indent=2)

def set_config(key, value):
    init_config()
    config_path = get_config_path()
    with open(config_path, 'r') as f:
        data = json.load(f)
    data[key] = value
    with open(config_path, 'w') as f:
        json.dump(data, f, indent=2)

def get_config(key, default=None):
    config_path = get_config_path()
    if not config_path.exists():
        return default
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
        return data.get(key, default)
    except:
        return default

def get_all_config():
    config_path = get_config_path()
    if not config_path.exists():
        return {}
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except:
        return {}
