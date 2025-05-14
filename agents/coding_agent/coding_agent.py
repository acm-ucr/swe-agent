import ollama 
from agents.node import Node

from shared import clone_repo, ensure_repo_cloned, repo_to_textTree


class CodingAgent(Node):
    def __init__(self, model_name, backend, sys_msg):
        super().__init__(model_name, backend, sys_msg)
        
    def instruct(self, instruction):
        """
        youre an assitant. just talk with the user
        """
        response = super().instruct(instruction)
    
        return response
    

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv() 

    node = CodingAgent("qwen2.5:7b", "ollama", "You are a helpful assistant.")
    print(node.model_name)  
    print(node.backend)

