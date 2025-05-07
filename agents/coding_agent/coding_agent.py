import ollama 
from agents.node import Node

class CodingAgent(Node):
    # override any neccessary attributes or functions from Node
    
    def __init__(self, model_name, backend, sys_msg):
        super().__init__(model_name, backend, sys_msg)

        # intialize attributes for intermediate steps such as models

    # add additionally helper functions here

    def instruct(self, instruction):
        """
        Instructs the agent to perform a task.
        """
        # use this as the function to call, modify it if neccessary 
        response = super().instruct(instruction)

        return response
    

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv() 

    node = CodingAgent("qwen2.5:7b", "ollama", "You are a helpful assistant.")
    print(node.model_name)
    print(node.backend)

