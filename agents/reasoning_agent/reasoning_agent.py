import ollama
import json
import os
from dotenv import load_dotenv

# === Class Definition ===
from agents.node import Node
from shared.github_tools import merge_github_branch, solve_merge_conflicts

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

    if task_data["status"]:
        owner = "acm-ucr"
        repo = "swe-agent"
        head = task_data.get("feature_branch_name")
        base = "main"

        print(f"✅ Task complete. Merging branch '{head}' into '{base}' on {owner}/{repo}...")

        # === Try GitHub API merge ===
        merge_result = merge_github_branch(owner, repo, head, base)

        if merge_result is None:
            print("⚠️ Remote merge failed — attempting to resolve merge conflicts locally with LLM...")

            # === Call your local conflict solver ===
            local_repo_path = os.getenv("LOCAL_REPO_PATH")
            if not local_repo_path:
                raise ValueError("Please set LOCAL_REPO_PATH environment variable.")

            conflict_resolved = solve_merge_conflicts(
                repo_path=local_repo_path,
                base_branch=base,
                original_task=task_data["original_task"],
                agent=agent,
                feature_branch=head
            )

            if conflict_resolved:
                print("✅ Conflicts resolved & merged successfully via local solver.")
            else:
                print("❌ Local conflict resolution failed. Please resolve manually.")
        else:
            print("✅ Remote merge succeeded.")

    else:
        print("Task not complete. See problem above.")
