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