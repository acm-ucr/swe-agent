import json
from agents.node import Node


class AssignmentAgent(Node):
    def __init__(self, model_name, backend, sys_msg):
        super().__init__(model_name, backend, sys_msg)

    def classify_tasks(self, prompt):
        """
        Classify tasks based on their complexity using the LLM.

        Args:
            prompt (str): A prompt containing tasks to classify.

        Returns:
            dict: A dictionary with classified tasks.
        """
        response = self.instruct(prompt)

        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            raise ValueError("The response is not in valid JSON format.")

        # Check for required keys
        required_keys = {"regular_model", "thinking_model"}
        if not required_keys.issubset(result.keys()):
            raise ValueError(
                f"Response JSON must contain keys: {required_keys}. Got: {list(result.keys())}"
            )

        return result


if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()

    MODEL = "qwen3:4b"
    PROMPT = """You are a software task classifier.

                    Classify each task based on its complexity using the description. Use the following rules:
                    - "regular": project setup, simple UI layout, static styling
                    - "complex": logic-heavy backend work, database or auth integration, API calls

                    Return your response as a JSON object with two keys:
                    - "regular_model": [list of tasks]
                    - "thinking_model": [list of tasks]
                    Each task must contain: id, description.
                    Only return valid JSON. No extra explanation."""

    agent = AssignmentAgent(MODEL, "ollama", PROMPT)

    with open("task_list.json", "r") as f:
        task_list = json.load(f)

    instruction = PROMPT + "\n\nTasks:\n" + json.dumps(task_list, indent=2)

    # Classify tasks
    print("=== Assigning Tasks ===")
    try:
        result = agent.classify_tasks(instruction)
        with open("model_assignment.json", "w") as f:
            json.dump(result, f, indent=2)
        print("Classification complete. Saved to model_assignment.json")
    except ValueError as e:
        print("Failed to parse model output (invalid JSON):", e)
