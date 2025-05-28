import pyfiglet
from colorama import init, Fore, Style
from agents.interface_agent.interface_agent import InterfaceAgent 
from agents.review_agent.review_agent import ReviewAgent
from agents.coding_agent.coding_agent import CodingAgent
from shared.setup_tools import read_initial_instructions, setup_logs
from shared.log_tools import log_interaction, print_action

def run_agent():
    # Render ASCII art banner
    banner = pyfiglet.figlet_format("SWE Agent", font="slant")

    # Print in light blue
    print(Fore.LIGHTBLUE_EX + banner + Style.RESET_ALL)

    # intialize variables 
    path = "/Users/jerryli/Desktop/python/SWE-Agent/instructions/test1.json" # change later
    instructions = read_initial_instructions(path)
    log_path = setup_logs(type='tests')

    # intialize agents
    interface_agent = InterfaceAgent("gemma3:4b", "ollama", sys_msg=instructions['interaction_prompt'], temperature=0.5)
    orchestrator_agent = ReviewAgent()
    code_agent = CodingAgent("qwen2.5:7b", "ollama", instructions['sys_prompt'], instructions['correction_prompt'])

    # interaction 
    while True:
        user_prompt = input(">>> ")
        print_action("Interacting with the user...", color="yellow")
        output = interface_agent.instruct(user_prompt)
        print(output)

        log_interaction(log_path, 
                        {
                            "agent": "interaction",
                            "sys_prompt": instructions['sys_prompt'],
                            "user_prompt": user_prompt,
                            "tools_used": None, # change later?
                            "output": output
                        })
        
        if user_prompt == "quit": break 

    # orchestrator 
    

    # code agent


if __name__ == "__main__":
    run_agent()