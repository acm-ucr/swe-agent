import os
import json
from agents.coding_agent.coding_agent import CodingAgent
from agents.reasoning_agent.reasoning_agent import ReasoningAgent

def main():
    # Setup prompts and agents
    system_prompt = """

    You are an elite Next.js software engineer agent embedded in a CI/CD pipeline. Your role is to propose changes to a codebase based on feature requests. All your responses must be strictly formatted in **valid JSON**.

    Your Objective:
    Given a file tree and a user-defined task, you must analyze which files should be **modified**, **created**, or **deleted**, and provide clear instructions for each. You are expected to reason through the minimum set of necessary changes to fulfill the task without redundant modifications.

    JSON Response Format:
    Respond with a **single valid JSON object** containing up to three keys: `modify`, `create`, and `delete`.

    ```json
    {
    "modify": ["app/page.tsx"],
    "create": ["app/components/HelloWorld.tsx"],
    "delete": []
    }

      """  # Use your actual prompt
    correction_prompt = "Your previous response was not valid JSON. ... State and explain specifically why it is not valid JSON"
    coding_agent = CodingAgent("cogito:3b", "ollama", system_prompt, correction_prompt)
    reasoning_agent = ReasoningAgent("cogito:3b", "ollama", "You are a code reviewing agent.")

    # Example file tree and task
    file_tree = """
        app/
        page.tsx
        notrelevant.tsx
    """
    task = "add a 'react arrow function component within app/page.tsx that returns an html p tag with 'hello world' within it to the main page.tsx"

    # 1. CodingAgent analyzes the task
    file_actions = coding_agent.analyze_task(file_tree, task)
    files_to_modify = file_actions.get("modify", [])
    files_to_create = file_actions.get("create", [])

    # 2. For each file to modify, get the proposed code changes (stubbed here)
    # In a real system, you would generate or fetch the actual code changes
    proposed_changes = {
        fname: "// new code for " + fname for fname in files_to_modify
    }

    # 3. ReasoningAgent reviews each change
    review_results = []
    for fname in files_to_modify:
        prompt = f"""
You are an AI code reviewer.

Task: {task}
Proposed Code for {fname}:
{proposed_changes[fname]}

Does the code fulfill the task?
Reply:
- ✅ YES, the task is completed.
- ❌ NO, the task is not completed, and explain why.
"""
        response = reasoning_agent.instruct(prompt).strip()
        review_results.append({
            "file": fname,
            "review": response,
            "status": "✅" in response,
            "problem": None if "✅" in response else response
        })

    # 4. Aggregator logic: decide if all files are approved
    all_approved = all(r["status"] for r in review_results)
    
    # 5. Output results
    print("Files to modify:", files_to_modify)
    print("Files to create:", files_to_create)
    print("Review results:", json.dumps(review_results, indent=2))
    print("Should merge:", all_approved)

if __name__ == "__main__":
    main()