import zmq
import json
import time
import os
from agents.assignment_agent.assignment_agent import AssignmentAgent
from orchestrator.publisher import publish_text

class Orchestrator:
    def __init__(self, model_name, backend, sys_msg, devices):
        self.assignment_agent = AssignmentAgent(model_name, backend, sys_msg)
        self.devices = devices
        self.context = zmq.Context()
        self.total_attempts = 10


    def add_device(self, device):
        self.devices.append(device)

    def remove_device(self, device):
        if device in self.devices:
            self.devices.remove(device)

    def get_open_device(self, model_type):
        """
            Based on the model_type see if any are avaliable 
            If so return the device info 
            else return None
        """
        for device in self.devices[model_type]:
            if device['status'] == 'open':
                return device 
        return None

    
    def stream_tasks(self, task_list):
        print("=== Assigning Tasks ===")
        result = self.assignment_agent.classify_task_list(task_list)

        all_tasks = []
        for task_list, model_type in [
            (result["regular_model"], "regular"),
            (result["thinking_model"], "thinking")
        ]:
            for task in task_list:
                task["model_type"] = model_type
                all_tasks.append(task)

        print("=== Streaming Tasks ===")
        while(self.total_attempts > 0):
            for task in all_tasks:
                print(task)
                task_string = str(task['id']) + ": " + task['description']
                device = self.get_open_device(task['model_type'])

                if device is None:
                    continue

                ip = device['ip']
                port = device['port']
                topics = "test"

                # publish_text(task_string, ip, port, topics, task_string)
                print(f"Sent task {task['id']} to device {device['id']} at {ip}:{port}")
                all_tasks.remove(task)
            self.total_attempts -= 1

        # assuming devices is a hashmap of device name to sets where each set contains the ip 
        # {
        #     regular: 
        #       device id : {ip, device type, port, status}
        #     thinking: 
        #       device id : {ip, device type, port, status}
        # }

        # assign tasks in queue system 
        # every device has a list of tasks to complete

        # until there's no tasks left in the queue 
            # for device in self.devices:
                # if device['status'] == "open":
                    # assign tasks to device 
                    # remove task from queue 
                    # update device status to closed 
                    # update device status to open after task is completed

def main():
    topics = ["Device1", "Device2", "Device3"]
    with open("ip.json") as f:
        config = json.load(f)
    
    receiver = config["devices"]["receiver"]
    context = zmq.Context()

    print("Attempting handshake...")
    socket = context.socket(zmq.PUB)
    socket.bind(f"tcp://*:5555")
    
    try:
        start_time = time.time()
        duration = 10
        while time.time() - start_time < duration:
            for i , topic in enumerate(topics):
                json_str = json.dumps(config)
                print(json_str)
                socket.send_string(f"{topic} {json_str}")
                time.sleep(2)
    except zmq.Again:
        print("Handshake timed out. Exiting.")
    
    socket.close()
    context.term()

if __name__ == "__main__":
    # main()
    model = "cogito:3b"
    backend = "ollama"
    sys_msg = """
                You are a task classifier. You can only reply with one word.
            """
    devices = {
        "regular": [
            {
                "id": 1,
                "ip": 1234,
                "port": 5555,
                "status": "open"  # open, closed
            }
        ],
        "thinking": [
            {
                "id": 2,
                "ip": 1234,
                "port": 5555,
                "status": "open"  # open, closed
            },
        ]
    }
    agent = Orchestrator(model, backend, sys_msg, devices)

    # Load tasks from JSON
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    task_list_path = os.path.join(project_dir, "tests/task_list_5.json")

    with open(task_list_path, "r") as f:
        task_list = json.load(f)

    agent.stream_tasks(task_list)