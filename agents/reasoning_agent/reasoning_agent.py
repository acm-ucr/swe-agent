import ollama
import json
import os
from dotenv import load_dotenv

# === Class Definition ===
from agents.node import Node

class ReasoningAgent(Node):
    def __init__(self, model_name, backend, sys_msg):
        super().__init__(model_name, backend, sys_msg)

    def instruct(self, instruction):
        return super().instruct(instruction)

if __name__ == "__main__":
    load_dotenv()

    with open("agents/reasoning_agent/test.json") as f:
        task_data = json.load(f)

    agent = ReasoningAgent("cogito:3b", "ollama", "You are a code reviewing agent.")

    prompt = f"""
You are an AI code reviewer.

Task: {task_data['original_task']}
Proposed Code:
{task_data['changes_to_file']}

Does the code fulfill the task?
Reply:
- ✅ YES, the task is completed.
- ❌ NO, the task is not completed, and explain why.
"""

    response = agent.instruct(prompt).strip()

    # Add status + problem fields
    task_data["status"] = "✅" in response
    task_data["problem"] = None if task_data["status"] else response

    print(json.dumps(task_data, indent=2))
