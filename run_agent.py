import pyfiglet
from colorama import init, Fore, Style
from agents.reasoning_agent.reasoning_agent import InteractionAgent 
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
    interaction_agent = InteractionAgent("qwen2.5:7b", "ollama", instructions['sys_prompt'])
    orchestrator_agent = ReviewAgent()
    code_agent = CodingAgent("qwen2.5:7b", "ollama", instructions['sys_prompt'], instructions['correction_prompt'])

    # interaction 
    interaction_complete = False
    user_prompt = instructions['user_prompt']
    while not interaction_complete:
        print_action("Interacting with the user...", color="yellow")
        output = interaction_agent.instruct(user_prompt)
        print(output)
        # interaction_complete = output['status']

        # log
        log_interaction(log_path, 
                        {
                            "agent": "interaction",
                            "sys_prompt": instructions['sys_prompt'],
                            "user_prompt": user_prompt,
                            "tools_used": None, # change later?
                            "output": output
                        })
    
        if not interaction_complete:
            user_prompt = input()
            if user_prompt == "quit": exit()    # debug

    # orchestrator 

    # code agent


if __name__ == "__main__":
    run_agent()