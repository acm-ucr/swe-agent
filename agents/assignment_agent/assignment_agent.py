import json
import sys
sys.path.append("/Users/risaonishi/Downloads/CS/swe-agent/agents")
from agents.node import Node


# === Classification agent class ===
class AssignmentAgent(Node):
    def __init__(self, model_name, backend, sys_msg=""):
        super().__init__(model_name, backend, sys_msg)

    def classify_task(self, task_id, description):
        """
        Classify a single task as either 'regular_model' or 'thinking_model'
        """
        prompt = f"""
                You are a task classifier. You can only reply with one word.

                Classify the task as:
                - "regular_model" for simple tasks (e.g. UI layout, static styling, project setup)
                - "thinking_model" for complex tasks (e.g. backend logic, authentication, APIs, or DB work)

                Return **only** the category string — either "regular_model" or "thinking_model".
                Do **not** include explanations or reasoning. You will be punished for including additional reasoning in your answer.

                Task:
                {task_id}: {description}
                """

        category = self.instruct(prompt).strip().replace('"', '')

        if category not in {"regular_model", "thinking_model"}:
            raise ValueError(f"Invalid category '{category}' returned for task {task_id}")
        
        return category

    def classify_task_list(self, task_list):
        result = {"regular_model": [], "thinking_model": []}

        for task in task_list:
            task_id = task.get("id")
            desc = task.get("description")
            if not task_id or not desc:
                print(f"Skipping invalid task: {task}")
                continue

            try:
                category = self.classify_task(task_id, desc)
                result[category].append(task)
                print(f"✓ Task {task_id} → {category}")
            except Exception as e:
                print(f"✗ Failed to classify task {task_id}: {e}")

        return result


# === Script entry point ===
if __name__ == "__main__":
    import os
    MODEL = "cogito:3b"
    BACKEND = "ollama"
    PROMPT = """
                You are a task classifier. You can only reply with one word.

                Classify the task as:
                - "regular_model" for simple tasks (e.g. UI layout, static styling, project setup)
                - "thinking_model" for complex tasks (e.g. backend logic, authentication, APIs, or DB work)

                Return **only** the category string — either "regular_model" or "thinking_model".
                Do **not** include explanations or reasoning. You will be punished for including additional reasoning in your answer.
                """

    # Load tasks from JSON
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    task_list_path = os.path.join(project_dir, "tests/task_list_30.json")

    with open(task_list_path, "r") as f:
        task_list = json.load(f)

    agent = AssignmentAgent(MODEL, BACKEND, PROMPT)

    print("=== Assigning Tasks ===")
    result = agent.classify_task_list(task_list)

    # Save to file
    output_path = os.path.join(project_dir, "tests/model_assignment.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n🎉 Classification complete. Saved to {output_path}")
