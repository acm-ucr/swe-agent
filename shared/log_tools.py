import json
from datetime import datetime

def log_interaction(path, data):
    with open(path, 'r') as f:
        full_data = json.load(f)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    full_data[timestamp] = data

    with open(path, 'w') as f:
        json.dump(full_data, f, indent=2)
        

def log_orchestrator():
    pass

def log_coding():
    pass

def print_action(text, color="green"):
    color_map = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m"
    }
    reset_color = "\033[0m"
    
    print(f"{color_map[color]}{text}{reset_color}")