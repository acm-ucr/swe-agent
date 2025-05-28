import pyfiglet
import json
import os
from colorama import init, Fore, Style
from agents.interface_agent.interface_agent import InterfaceAgent 
from agents.review_agent.review_agent import ReviewAgent
from agents.coding_agent.coding_agent import CodingAgent
from shared.setup_tools import read_initial_instructions, setup_logs
from shared.log_tools import log_interaction, print_action
from shared.file_tools import extract_json
from orchestrator.orchestrator import Orchestrator

def run_agent():
    # Render ASCII art banner
    banner = pyfiglet.figlet_format("SWE Agent", font="slant")

    # Print in light blue
    print(Fore.LIGHTBLUE_EX + banner + Style.RESET_ALL)

    # intialize variables 
    path = r"C:\Users\10660\Projects\swe-agent\instructions\test2.json" # change later
    instructions = read_initial_instructions(path)
    log_path = setup_logs(type='tests')
    devices = {
        "regular": [
            {
                "id": 1,
                "ip": 1234,
                "port": 5555,
                "status": "open"  # open, closed
            },
            {
                "id": 2,
                "ip": 1235,
                "port": 5555,
                "status": "open"  # open, closed
            },
            {
                "id": 3,
                "ip": 1236,
                "port": 5555,
                "status": "open"  # open, closed
            },
        ],
        "thinking": [
            {
                "id": 4,
                "ip": 1237,
                "port": 5555,
                "status": "open"  # open, closed
            },
        ]
    }

    # intialize agents
    interface_agent = InterfaceAgent("gemma3:12b", "ollama", sys_msg=instructions['interaction_prompt'], temperature=0.5)
    orchestrator_agent = Orchestrator("cogito:3b", "ollama", sys_msg=instructions['orchestrator_prompt'], devices=devices)
    code_agent = CodingAgent("qwen2.5:7b", "ollama", instructions['code_prompt'], instructions['code_prompt'])

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
    print(tasks)
    log_interaction(log_path, 
                    {
                        "agent": "interaction",
                        "tasks": tasks,
                    })
    orchestrator_agent.stream_tasks(tasks, log_path=log_path)

    # code agent


if __name__ == "__main__":
    run_agent()


# test
'''
Help create a website that visualizes the solution for the two sum leetcode question as a react project.
It should show the array elements, target sum and the indicies being chcked. I envision a simple animation thats a predefined GIF. I dont have any wireframes right now. This is all the information you need
No this is all you need to gererate the tasks


'''