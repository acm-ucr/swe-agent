import ollama
from agents.node import Node

class CodingAgent(Node):
    def __init__(self, model_name, backend, sys_msg):
        super().__init__(model_name, backend, sys_msg)

    def instruct(self, instruction):
        """
        Instructs the agent to perform a task.
        """
        response = super().instruct(instruction)

        return response


if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()

    node = CodingAgent("deepseek-r1", "ollama", "You are a helpful assistant.")
    print(node.model_name)
    print(node.backend)

    print(node.instruct("Write a function to calculate the factorial of a number."))

