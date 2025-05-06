import ollama
import json
import logging
import sys
import argparse

def analyze_file_tree(file_tree: str, task: str, max_retries: int = 3) -> str:
    """
    Analyzes a file tree and task to determine relevant files that need modification.
    
    Args:
        file_tree (str): ASCII representation of the file tree
        task (str): Description of the task to be performed
        max_retries (int): Maximum number of retries for JSON validation
        
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

    correction_prompt = """Your previous response was not valid JSON. Please provide your answer in a valid JSON array format.
For example: ["file1.tsx", "file2.tsx"]
Do not include any other text or formatting, just the JSON array."""

    messages = [
        ('system', system_prompt),
        ('user', f"File Tree:\n{file_tree}\n\nTask: {task}")
    ]

    retry_count = 0
    while retry_count < max_retries:
        response = ollama.chat(
            model='cogito:3b',
            messages=[{'role': role, 'content': content} for role, content in messages]
        )

        # Extract the JSON array from the response
        content = response['message']['content']
        if '<thinking>' in content:
            # Extract everything after the last </thinking> tag
            json_part = content.split('</thinking>')[-1].strip()
        else:
            json_part = content.strip()

        try:
            # Parse and validate the JSON
            result = json.loads(json_part)
            return json.dumps(result)
        except json.JSONDecodeError:
            retry_count += 1
            if retry_count < max_retries:
                logging.warning(f"Attempt {retry_count}: Invalid JSON response. Retrying...")
                messages.append(('assistant', content))
                messages.append(('user', correction_prompt))
            else:
                logging.error("Maximum retries reached. Could not get valid JSON response.")
                return json.dumps({
                    "error": "Could not get valid JSON response",
                    "raw_response": content
                })

    return json.dumps({
        "error": "Maximum retries reached",
        "raw_response": content
    })

def main():
    parser = argparse.ArgumentParser(description='File Tree Analyzer')
    parser.add_argument('--logging', type=str, default='INFO', help='Logging level')
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=args.logging, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))

    # Example usage
    file_tree = """app/
page.tsx
notrelevant.tsx"""
    
    task = "add a \"hello world\" to the main page"
    
    result = analyze_file_tree(file_tree, task)
    print("\nFinal Result:")
    print(result)

if __name__ == "__main__":
    main() 