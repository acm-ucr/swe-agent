import sys
import ollama 
import json
import logging
sys.path.append("/Users/henry/Documents/GitHub/swe-agent")
from agents.node import Node
from typing import Dict, List

class CodingAgent(Node):
    # override any neccessary attributes or functions from Node
    
    def __init__(self, model_name, backend, sys_msg):
        super().__init__(model_name, backend, sys_msg)

        # intialize attributes for intermediate steps such as models

    # add additionally helper functions here

    def analyze_file_tree(self, file_tree: str, task: str, max_retries: int = 3) -> str:
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
            except json.JSONDecodeError as e:
                retry_count += 1
                if retry_count < max_retries:
                    logging.warning(f"Attempt {retry_count}: Invalid JSON response. Error: {str(e)}")
                    messages.append(('assistant', content))
                    messages.append(('user', correction_prompt))
                else:
                    logging.error("Maximum retries reached. Could not get valid JSON response.")
                    return json.dumps([])

        return json.dumps([])

    def determine_files_to_create(self, file_tree: str, task: str, max_retries: int = 3) -> List[str]:
        """
        Determines which new files need to be created for the task.
        
        Args:
            file_tree (str): ASCII representation of the file tree
            task (str): Description of the task to be performed
            max_retries (int): Maximum number of retries for JSON validation
            
        Returns:
            List[str]: List of new files that need to be created
        """
        system_prompt = """You are specialized in analyzing tasks and determining which new files need to be created.
Your outputs should follow this structure:
1. Begin with a <thinking> section.
2. Inside the thinking section:
   a. Analyze the task requirements
   b. Consider if new files need to be created
   c. Determine appropriate file locations and names
3. Include a <reflexion> section where you:
   a. Review your decisions
   b. Verify if the file locations make sense
   c. Confirm or adjust your decisions if necessary
4. Close the thinking section with </thinking>
5. Provide your final answer in a JSON array format containing only the new file paths.

Example output format:
<thinking>
1. Task requires a new button component...
2. No existing button component found...
3. Should create new file in components directory...

<reflexion>
- Need to create new file for button component
- Should follow project structure conventions
- Component should be in components directory
</reflexion>
</thinking>
["components/Button.tsx"]
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
                model=self.model_name,
                messages=[{'role': role, 'content': content} for role, content in messages]
            )

            content = response['message']['content']
            if '<thinking>' in content:
                json_part = content.split('</thinking>')[-1].strip()
            else:
                json_part = content.strip()

            try:
                result = json.loads(json_part)
                if not isinstance(result, list):
                    raise json.JSONDecodeError("Invalid structure", json_part, 0)
                return result
            except (json.JSONDecodeError, TypeError) as e:
                retry_count += 1
                if retry_count < max_retries:
                    logging.warning(f"Attempt {retry_count}: Invalid JSON response. Error: {str(e)}")
                    messages.append(('assistant', content))
                    messages.append(('user', correction_prompt))
                else:
                    logging.error("Maximum retries reached. Could not get valid JSON response.")
                    return []

        return []

    def analyze_task(self, file_tree: str, task: str) -> Dict[str, List[str]]:
        """
        Main function that analyzes a task and determines all necessary file actions.
        
        Args:
            file_tree (str): ASCII representation of the file tree
            task (str): Description of the task to be performed
            
        Returns:
            Dict[str, List[str]]: Dictionary containing all file actions needed
        """
        # Get files to modify
        modify_result_str = self.analyze_file_tree(file_tree, task)
        try:
            modify_result = json.loads(modify_result_str)
            if not isinstance(modify_result, list):
                modify_result = []
        except json.JSONDecodeError:
            modify_result = []
        
        # Get files to create
        create_result = self.determine_files_to_create(file_tree, task)
        
        # Log the results
        if modify_result:
            logging.info(f"Files to modify: {modify_result}")
        if create_result:
            logging.info(f"Files to create: {create_result}")
        
        return {
            "modify": modify_result,
            "create": create_result
        }

    def instruct(self, instruction):
        """
        Instructs the agent to perform a task.
        """
        # use this as the function to call, modify it if neccessary 
        response = super().instruct(instruction)

        return response
    

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv() 

    # Example usage
    agent = CodingAgent("cogito:3b", "ollama", "You are a helpful assistant.")
    
    file_tree = """app/
page.tsx
notrelevant.tsx"""
    
    # Example 1: Simple modification
    task1 = "add a \"hello world\" to the main page.tsx"
    print("\nTask 1 - Simple Modification:")
    result1 = agent.analyze_task(file_tree, task1)
    print("\nFinal Result 1:")
    print(json.dumps(result1, indent=2))
    
    # Example 2: Creating new component
    task2 = "create a new button component with a primary style"
    print("\nTask 2 - Creating New Component:")
    result2 = agent.analyze_task(file_tree, task2)
    print("\nFinal Result 2:")
    print(json.dumps(result2, indent=2))

