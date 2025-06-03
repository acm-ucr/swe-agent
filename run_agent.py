import pyfiglet
import json
import os
import zmq 
import threading
import argparse
from colorama import init, Fore, Style
from agents.interface_agent.interface_agent import InterfaceAgent 
from agents.review_agent.review_agent import ReviewAgent
from agents.coding_agent.coding_agent import CodingAgent
from shared.setup_tools import read_initial_instructions, setup_logs
from shared.log_tools import log_interaction, print_action
from shared.file_tools import extract_json
from orchestrator.orchestrator import Orchestrator
from orchestrator.client import start_handshake_server, text_listener   

def parse_args():
    parser = argparse.ArugementParser(description="SWE Agent Settings")
    parser.add_argument("--instruction_path", type=str, default="./instructions/")
    parser.add_argument("--device_config", type=str, default="")
    parser.add_argument("--distributed_config", type=str, default="")
    parser.add_argument("--log_type", type=str, default="test")
    parser.add_argument("--main_device", type=bool, description="On distributed setting the task divider, no distributed the main agent", default=True)


def run_code_agent(args):
    # Render ASCII art banner
    banner = pyfiglet.figlet_format("SWE Agent", font="slant")

    # Print in light blue
    print(Fore.LIGHTBLUE_EX + banner + Style.RESET_ALL)

    # intialize variables 
    path = args.instruction_path # "/Users/jerryli/Desktop/python/SWE-Agent/instructions/code_only/test3.json" 
    instructions = read_initial_instructions(path)
    log_path = setup_logs(type=args.log_type)
    if args.device_config != "":
        with open(args.device_config) as f:   # "instructions/code_only/device.json"
            device_config = json.load(f)
        distributed = False
    else:   
        distributed = True

    # intialize agent
    code_agent = CodingAgent("cogito:3b", 
                             "ollama", 
                             sys_prompt=instructions['code_prompt']['system_prompt'], 
                             correction_prompt=instructions['code_prompt']['correction_prompt'])

    # listen for all assigned tasks 
    receiver_ip = device_config["receiver"]["ip"]
    sender_ip = device_config["sender"]["ip"]
    port =  device_config["sender"]["port"]
    context = zmq.Context()

    # threading.Thread(
    #     target=start_handshake_server,
    #     args=(context, device_config["receiver"]["handshake_port"]),
    #     daemon=True
    # ).start()

    # tasks = text_listener(context, sender_ip, port=port, topic=receiver_ip)
    tasks = ["add a \"hello world\" to page.tsx"]

    # complete all assigned tasks 
    file_tree = """
                    app/
                    page.tsx
                    notrelevant.tsx
                """
    for i, task in enumerate(tasks):
        output = code_agent.analyze_task(file_tree, task, max_tries=10)   # files to modify

        # result = code_agent.check_status(dummy_script_path, id)

        print(output)


    # send to aggregator
 

def run_main_agent(args):
    # Render ASCII art banner
    banner = pyfiglet.figlet_format("SWE Agent", font="slant")

    # Print in light blue
    print(Fore.LIGHTBLUE_EX + banner + Style.RESET_ALL)

    # intialize variables 
    path = args.instruction_path # "/Users/jerryli/Desktop/python/SWE-Agent/instructions/code_only/test3.json" 
    instructions = read_initial_instructions(path)
    log_path = setup_logs(type=args.log_type)
    if args.device_config != "":
        with open(args.device_config) as f:   # "instructions/code_only/device.json"
            device_config = json.load(f)
        with open(args.distributed_config) as f:
            distributed_config = json.load(f)
        distributed = False
    else:   
        distributed = True

    # intialize agents
    interface_agent = InterfaceAgent("gemma3:12b", "ollama", sys_msg=instructions['interaction_prompt'], temperature=0.5)
    orchestrator_agent = Orchestrator("cogito:3b", "ollama", sys_msg=instructions['orchestrator_prompt'], devices=distributed_config)
    code_agent = CodingAgent("cogito:3b", 
                             "ollama", 
                             sys_prompt=instructions['code_prompt']['system_prompt'], 
                             correction_prompt=instructions['code_prompt']['correction_prompt']) if not distributed else None
    # interaction 
    while True:
        user_prompt = input(">>> ")
        if user_prompt == "quit": break 
        print_action("Interacting with the user...", color="yellow")
        output = interface_agent.instruct(user_prompt)
        print(output)

        log_interaction(log_path, 
                        {
                            "agent": "interaction",
                            "sys_prompt": instructions['interaction_prompt'],
                            "user_prompt": user_prompt,
                            "tools_used": None, # change later?
                            "output": output
                        })
        
        tasks = extract_json(output)
        if tasks is not None:
            break

    # orchestrator 
    if distributed:
        print(tasks)
        log_interaction(log_path, 
                        {
                            "agent": "interaction",
                            "tasks": tasks,
                        })
        orchestrator_agent.stream_tasks(tasks, log_path=log_path)

    # code agent
    if not distributed:
        file_tree = ""
        for i, task in enumerate(tasks):
            output = code_agent.analyze_task(file_tree, task, max_tries=10)   # files to modify
            # result = code_agent.check_status(dummy_script_path, id)

def main():
    args = parse_args()

    if not args.main_device:
        run_code_agent(args)
    else:
        run_main_agent(args)

if __name__ == "__main__":
    main()


# test
'''
Help create a website that visualizes the solution for the two sum leetcode question as a react project.
It should show the array elements, target sum and the indicies being chcked. I envision a simple animation thats a predefined GIF. I dont have any wireframes right now. This is all the information you need
No this is all you need to gererate the tasks


'''