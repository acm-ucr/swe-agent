import sys
import ollama 
import json
import logging
import os
import shutil
from datetime import datetime
sys.path.append("/Users/henry/Documents/GitHub/swe-agent")
from agents.node import Node
from typing import Dict, List
from shared.file_tools import fetch_files_from_codebase, edit_files_from_codebase, create_file

class CodingAgent(Node):
    def __init__(self, model_name, backend, sys_msg, correction_prompt):
        super().__init__(model_name, backend, sys_msg)

        # intialize attributes for intermediate steps such as models
        self.correction_prompt = correction_prompt

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

        messages = [
            ('system', self.sys_msg),
            ('user', f"File Tree:\n{file_tree}\n\nTask: {task}")
        ]

        retry_count = 0
        while retry_count < max_retries:
            response = ollama.chat(
                model=self.model_name,
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
                    messages.append(('user', self.correction_prompt))
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

        messages = [
            ('system', self.sys_msg),
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
                    messages.append(('user', self.correction_prompt))
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
        system_prompt = """You are specialized in analyzing tasks and determining which files need to be modified or created.
Your outputs should follow this structure:
1. Begin with a <thinking> section.
2. Inside the thinking section:
   a. Analyze the task requirements
   b. Consider existing files that need modification
   c. Consider if new files need to be created
3. Include a <reflexion> section where you:
   a. Review your decisions
   b. Verify if the file selections make sense
   c. Confirm or adjust your decisions if necessary
4. Close the thinking section with </thinking>
5. Provide your final answer in a valid JSON array format containing only the relevant file paths.

Example output format:
<thinking>
1. Task requires modifying test.py...
2. No new files needed...
3. Only test.py needs to be modified...

<reflexion>
- test.py exists in the file tree
- The task specifically mentions test.py
- No other files need modification
</reflexion>
</thinking>
["src/test.py"]
"""

        correction_prompt = """Your previous response was not valid JSON. Please provide your answer in a valid JSON array format.
For example: ["src/test.py"]
Do not include any other text or formatting, just the JSON array."""

        messages = [
            ('system', system_prompt),
            ('user', f"File Tree:\n{file_tree}\n\nTask: {task}")
        ]

        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            try:
                response = ollama.chat(
                    model=self.model_name,
                    messages=[{'role': role, 'content': content} for role, content in messages]
                )

                content = response['message']['content']
                
                # Extract JSON part
                if '<thinking>' in content:
                    json_part = content.split('</thinking>')[-1].strip()
                else:
                    json_part = content.strip()

                # Parse and validate the JSON
                result = json.loads(json_part)
                if not isinstance(result, list):
                    raise json.JSONDecodeError("Invalid structure", json_part, 0)

                # Separate paths into modify and create based on existence in file tree
                modify_paths = []
                create_paths = []
                
                for path in result:
                    if path in file_tree or any(path in line for line in file_tree.split('\n')):
                        modify_paths.append(path)
                    else:
                        logging.info(f"Path {path} not found in file tree, will be created")
                        create_paths.append(path)

                return {
                    "modify": modify_paths,
                    "create": create_paths
                }

            except json.JSONDecodeError as e:
                retry_count += 1
                if retry_count < max_retries:
                    logging.warning(f"Attempt {retry_count}: Invalid JSON response. Error: {str(e)}")
                    messages.append(('assistant', content))
                    messages.append(('user', correction_prompt))
                else:
                    logging.error("Maximum retries reached. Could not get valid JSON response.")
                    return {"modify": [], "create": []}
            except Exception as e:
                logging.error(f"Unexpected error in analyze_task: {str(e)}")
                return {"modify": [], "create": []}

        return {"modify": [], "create": []}

    def read_files(self, file_paths: List[str]) -> Dict[str, str]:
        """
        Reads the contents of specified files.
        
        Args:
            file_paths: List of file paths to read
            
        Returns:
            Dict mapping file paths to their contents
        """
        return fetch_files_from_codebase(file_paths)

    def modify_files(self, file_updates: Dict[str, str]) -> Dict[str, str]:
        """
        Modifies existing files with new content.
        
        Args:
            file_updates: Dict mapping file paths to their new contents
            
        Returns:
            Dict with results of each file modification
        """
        return edit_files_from_codebase(file_updates)

    def create_new_files(self, files_to_create: List[str], base_path: str = "") -> None:
        """
        Creates new files in the codebase.
        
        Args:
            files_to_create: List of file paths to create
            base_path: Optional base path for the new files
        """
        for file_path in files_to_create:
            # Extract filename and extension
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            # Create empty file
            create_file(name, ext[1:], os.path.dirname(file_path))

    def resolve_path(self, base_path: str, file_path: str) -> str:
        """
        Resolves a file path relative to the base path.
        
        Args:
            base_path: The base directory path
            file_path: The file path to resolve
            
        Returns:
            str: The resolved absolute path
            
        Raises:
            ValueError: If the resolved path is outside the base directory
        """
        # Convert to absolute paths
        abs_base = os.path.abspath(base_path)
        abs_path = os.path.abspath(os.path.join(base_path, file_path))
        
        # Check if the resolved path is within the base directory
        if not abs_path.startswith(abs_base):
            raise ValueError(f"Path {file_path} resolves outside base directory {base_path}")
            
        return abs_path

    def backup_file(self, file_path: str) -> str:
        """
        Creates a backup of a file before modification.
        
        Args:
            file_path: Path of the file to backup
            
        Returns:
            str: Path of the backup file
        """
        if not os.path.exists(file_path):
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.{timestamp}.bak"
        shutil.copy2(file_path, backup_path)
        return backup_path

    def generate_file_content(self, task: str, file_path: str, existing_content: str = "") -> str:
        """
        Generates new content for a file based on the task and existing content.
        
        Args:
            task: The task description
            file_path: Path of the file to modify
            existing_content: Current content of the file
            
        Returns:
            str: New content for the file
        """
        prompt = f"""You are a code generator. Your task is to {task}.

File: {file_path}
Current content:
{existing_content}

IMPORTANT INSTRUCTIONS:
1. Output ONLY the code/content that should be in the file
2. DO NOT include any explanations, markdown, or text like "Here's the code:"
3. If modifying an existing file, maintain its current structure and imports
4. If creating a new file, include all necessary imports and structure
5. Follow the project's existing patterns and style

Output the complete file content, ready to be written to the file."""

        response = ollama.chat(
            model=self.model_name,
            messages=[{'role': 'user', 'content': prompt}]
        )
        
        return response['message']['content'].strip()

    def safe_modify_file(self, file_path: str, new_content: str) -> bool:
        """
        Safely modifies a file with error handling and backup.
        
        Args:
            file_path: Path of the file to modify
            new_content: New content to write
            
        Returns:
            bool: True if modification was successful
        """
        try:
            # Create backup
            backup_path = self.backup_file(file_path)
            
            # Write new content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            return True
        except Exception as e:
            logging.error(f"Error modifying file {file_path}: {str(e)}")
            # Restore from backup if it exists
            if backup_path and os.path.exists(backup_path):
                shutil.copy2(backup_path, file_path)
            return False

    def execute_task(self, file_tree: str, task: str, base_path: str = "") -> Dict[str, List[str]]:
        """
        Executes a task by analyzing, reading, and modifying files as needed.
        
        Args:
            file_tree: ASCII representation of the file tree
            task: Description of the task to be performed
            base_path: Base path for file operations
            
        Returns:
            Dict containing results of the operation
        """
        # Analyze which files need to be modified or created
        analysis = self.analyze_task(file_tree, task)
        
        # Handle file modifications
        if analysis["modify"]:
            # Read existing files
            file_contents = self.read_files(analysis["modify"])
            logging.info(f"Read {len(file_contents)} files for modification")
            
            # Generate and apply modifications
            for file_path in analysis["modify"]:
                try:
                    # Resolve the full path
                    full_path = self.resolve_path(base_path, file_path)
                    
                    # Get existing content
                    existing_content = file_contents.get(file_path, "")
                    
                    # Generate new content
                    new_content = self.generate_file_content(task, file_path, existing_content)
                    
                    # Safely modify the file
                    if self.safe_modify_file(full_path, new_content):
                        logging.info(f"Successfully modified {file_path}")
                    else:
                        logging.error(f"Failed to modify {file_path}")
                except Exception as e:
                    logging.error(f"Error processing {file_path}: {str(e)}")
        
        # Handle file creation
        if analysis["create"]:
            for file_path in analysis["create"]:
                try:
                    # Resolve the full path
                    full_path = self.resolve_path(base_path, file_path)
                    
                    # Generate content for new file
                    new_content = self.generate_file_content(task, file_path)
                    
                    # Create directory if needed
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    
                    # Write the file
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    logging.info(f"Created new file {file_path}")
                except Exception as e:
                    logging.error(f"Error creating {file_path}: {str(e)}")
        
        return analysis

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

    # Setup prompts 
    system_prompt = """
                        You're a pro at Next.js and determining which files to modify / create given a task from your boss. He'll kill you and your family if you modify the wrong files or create files we don't need.

                        You are specialized in analyzing tasks and determining which new files need to be created.
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

    correction_prompt = """
                            Your previous response was not valid JSON. Please provide your answer in a valid JSON array format.
                            For example: ["file1.tsx", "file2.tsx"]
                            Do not include any other text or formatting, just the JSON array.
                        """ 

    # Example usage
    model_name = "cogito:3b"
    backend = "ollama"
    agent = CodingAgent(model_name, backend, system_prompt, correction_prompt)

    
    # Example task: Add a function to test.py that creates a new branch
    file_tree = """
        SWE-Agent-test/
        ├─ config/
        │  └─ test.yaml
        ├─ ollama-tools/
        │  ├─ .gitignore
        │  ├─ example_allmodels.py
        │  ├─ example_think_act.py
        │  ├─ example_with_tool_support.py
        │  ├─ LICENSE
        │  ├─ ollama_tools.py
        │  ├─ README.md
        │  ├─ requirements.txt
        │  └─ sample_functions.py
        ├─ src/
        │  ├─ agent.py
        │  ├─ github.py
        │  ├─ huggingface.py
        │  ├─ ollama_tool.py
        │  ├─ test.py
        │  └─ utils.py
        ├─ .gitignore
        ├─ .gitmodules
        ├─ dummy.txt
        └─ README.md
                """
    
    # Example 1: Simple modification
    # task1 = "add a \"hello world\" to the main page.tsx"
    # print("\nTask 1 - Simple Modification:")
    # result1 = agent.analyze_task(file_tree, task1)
    # print("\nFinal Result 1:")
    # print(json.dumps(result1, indent=2))
    
    # # Example 2: Creating new component
    # task2 = "create a new button component with a primary style"
    # print("\nTask 2 - Creating New Component:")
    # result2 = agent.analyze_task(file_tree, task2)
    # print("\nFinal Result 2:")
    # print(json.dumps(result2, indent=2))

    task = "Add a function to test.py that creates a new branch"
    base_path = "/Users/henry/Documents/GitHub/SWE-Agent-test"
    
    print("\nExecuting task:", task)
    result = agent.execute_task(file_tree, task, base_path)
    print("\nTask execution result:")
    print(json.dumps(result, indent=2))

