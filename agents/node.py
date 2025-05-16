import ollama 
from shared.ollama_tools.ollama_tools import generate_function_description
from shared.github_tools import create_github_issue, get_issue_count
from smolagents import HfApiModel, CodeAgent

"""
    This module defines a Node class that represents our base for an Agent
    Handles the model backend between huggingface and ollama
"""
class Node():
    def __init__(self, model_name, backend, sys_msg, max_new_tokens=1000):
        self.model_name = model_name
        self.backend = backend
        assert self.backend in ["huggingface", "ollama"], f"Unsupported backend: {self.backend}"
        
        if self.backend == "ollama":
            self.model = ollama.create(model='example', from_=self.model_name, system=sys_msg)
        elif self.backend == "huggingface":
            # temp usage of api for huggingface
            model = HfApiModel(model_id=self.model_name, max_new_tokens=max_new_tokens)
            self.model = CodeAgent(tools=[], model=model, add_base_tools=True)
        self.tools = []
    
    def add_tool(self, tool):
        """
        Adds a tool to the node.
        """
        if self.backend == "ollama":
            self.tools.append(generate_function_description(tool))
        elif self.backend == "huggingface":
            self.tools.append(tool)
            self.model.tools[tool.name] = tool

    def instruct(self, instruction):
        """
        Instructs the agent to perform a task.
        """
        if self.backend == "ollama":
            response = ollama.chat(model=self.model_name, messages=[
                        {'role': 'user', 'content': instruction}, 
                    ], tools = self.tools)
            response = response['message']['content']
        elif self.backend == "huggingface":
            response = self.model.run(instruction)

        return response 
    

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv() 

    node = Node("qwen2.5:7b", "ollama", "You are a helpful assistant.")
    print(node.model_name)
    print(node.backend)

    node.add_tool(create_github_issue)
    node.add_tool(get_issue_count)
    print(node.tools)

