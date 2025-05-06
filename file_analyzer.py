import ollama
import json
import logging
import sys
import argparse

def analyze_file_tree(file_tree: str, task: str) -> str:
    """
    Analyzes a file tree and task to determine relevant files that need modification.
    
    Args:
        file_tree (str): ASCII representation of the file tree
        task (str): Description of the task to be performed
        
    Returns:
        str: JSON string containing relevant files that need modification
    """
    system_prompt = """You are specialized in analyzing file trees and determining which files need to be modified for a given task.
Your outputs should follow this structure:
1. Begin with a <thinking> section.
2. Inside the thinking section:
   a. Analyze the file tree structure
   b. Consider the task requirements
   c. Identify relevant files based on naming conventions and task context
3. Include a <reflexion> section where you:
   a. Review your file selection
   b. Verify if the selected files make sense for the task
   c. Confirm or adjust your selection if necessary
4. Close the thinking section with </thinking>
5. Provide your final answer in a JSON array format containing only the relevant file paths.

Example output format:
<thinking>
1. Analyzing file tree structure...
2. Task requires modification of main page...
3. Based on naming conventions, page.tsx is likely the main page...

<reflexion>
- page.tsx is the standard name for main pages in Next.js
- The task specifically mentions "main page"
- No other files seem relevant to this task
</reflexion>
</thinking>
["app/page.tsx"]
"""

    messages = [
        ('system', system_prompt),
        ('user', f"File Tree:\n{file_tree}\n\nTask: {task}")
    ]

    response = ollama.chat(
        model='phi4',
        messages=[{'role': role, 'content': content} for role, content in messages]
    )

    # Extract the JSON array from the response
    content = response['message']['content']
    if '<thinking>' in content:
        # Extract everything after the last </thinking> tag
        json_part = content.split('</thinking>')[-1].strip()
        try:
            # Parse and validate the JSON
            result = json.loads(json_part)
            return json.dumps(result)
        except json.JSONDecodeError:
            return json.dumps([])
    return json.dumps([])

def main():

    # Example usage
    file_tree = """app/
page.tsx
notrelevant.tsx"""
    
    task = "add a \"hello world\" to the main page"
    
    result = analyze_file_tree(file_tree, task)
    print(result)

if __name__ == "__main__":
    main() 