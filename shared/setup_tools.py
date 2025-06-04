
import os
import json 
from datetime import datetime

def read_initial_instructions(path):
    try:
        with open(path, 'r') as f:
            instructions = json.load(f)
    except FileNotFoundError:
        print("Error: File not found.")
        instructions = None
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON.")
        instructions = None
        
    return instructions

def setup_logs(type="runs", os_type="mac"):
    # create new log file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = f'{timestamp}.json'
    absolute_path = os.path.abspath("logs")
    if os_type=="mac" or os_type=="linux": log_path = absolute_path + "/" + type + "/" + file_name 
    else: log_path = absolute_path + "\\" + type + "\\" + file_name

    # write to folder based on type
    with open(log_path, 'w') as f:
        json.dump({}, f)

    print("Log Created: ", file_name)

    return log_path
