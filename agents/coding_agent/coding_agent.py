import sys
import ollama 
import json
import logging
import re
sys.path.append("C:\\Users\\inegi_pqetia\\Documents\\ACM DAS\\swe-agent")
from agents.node import Node
from typing import Dict, List
import subprocess
import os

from shared.ollama_tools.ollama_tools import generate_function_description, use_tools
from shared.github_tools import ensure_repo_cloned,clone_repo, repo_to_fileTree 



tools = [
    generate_function_description(ensure_repo_cloned),
    generate_function_description(clone_repo),
    generate_function_description(repo_to_fileTree),
    ...
]


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
    
    def handle_clone_task(self, owner: str, repo: str, target_dir: str, max_retries: int = 1):
        """
        Tries to clone the repo until it's confirmed to be cloned or max_retries is hit.
        """
        attempt = 0
        while attempt < max_retries:
            attempt += 1
            logging.info(f"Attempt {attempt} to clone {owner}")
            try:
                # Attempt to clone or ensure it's cloned
                success = ensure_repo_cloned(owner, repo, target_dir)

                # Check if the repo was actually cloned (i.e., directory exists and has a .git)
                if success:
                    logging.info(f"Successfully cloned repository to {target_dir}")
                    return True

            except Exception as e:
                logging.warning(f"Attempt {attempt} failed: {e}")

            logging.info("Retrying...")

        return False

    def parse_github_url(self, url: str):
        """
        Parses a GitHub repository URL and returns the owner and repository name.
        
        Args:
            url (str): The GitHub repository URL (e.g., "https://github.com/owner/repo")
        
        Returns:
            Tuple[str, str]: A tuple containing the owner and repository name
        
        Raises:
            ValueError: If the URL is not a valid GitHub repository URL
        """
        import re
        
        pattern = r'https?://github\.com/([^/]+)/([^/]+)(?:\.git)?/?$'
        match = re.match(pattern, url)
        
        if match:
            owner = match.group(1)
            repo = match.group(2)
            return owner, repo
        else:
            raise ValueError(f"Invalid GitHub URL: {url}")

    def instruct(self, instruction, task1):
        # 1. Get response from model
        response = ollama.chat(
            model=self.model_name,
            messages=[
                {'role': 'system', 'content': self.sys_msg},
                {'role': 'user', 'content': instruction}
            ]
        )

        # 2. Handle tool calls if present
        if 'tool_calls' in response['message']:
            tools_calls = response['message']['tool_calls']
            logging.debug("Tool calls received: %s", tools_calls)
            result = use_tools(tools_calls, tools)  # use your tool list
            if result:
                return result

       # 3. Fallback: parse instruction manually
        if "clone" in instruction and "https://github.com" in instruction:
            match = re.search(r'https://github\.com/([^/\s]+/[^/\s]+)', instruction)
            if match:
                repo_url = "https://github.com/" + match.group(1)
                owner, repo = self.parse_github_url(repo_url)
                target_dir = f"./{repo}"

                success = self.handle_clone_task(owner, repo, target_dir)
                if success:
                    print(f"Successfully cloned repository {repo_url} into {target_dir}.")
                
        #4. Call Henry's function
        file_tree = repo_to_fileTree(target_dir)
        print(file_tree)
        print("\nTask 1 - Simple Modification:")
        result1 = agent.analyze_task(file_tree, task1)
        print("\nFinal Result 1:")
        print(json.dumps(result1, indent=2))


        return result1


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv() 

    # Setup prompts 
    system_prompt = system_prompt = """
            You're a pro at Next.js and determining which files to modify or create given a task from your boss. He'll kill you and your family if you modify the wrong files or create files we don't need.

            You are specialized in analyzing tasks and determining which new files need to be created.
            Your outputs should follow this structure:

            1. Clone https://github.com/jeli04/acm-hydra into this directory using ensure_repo_cloned.
            2. Create an ASCII representation of the repo using repo_to_fileTree.
            3. Begin with a <thinking> section.
            4. Inside the thinking section:
            a. Analyze the task requirements  
            b. Consider if new files need to be created  
            c. Determine appropriate file locations and names  
            5. Include a <reflexion> section where you:
            a. Review your decisions  
            b. Verify if the file locations make sense  
            c. Confirm or adjust your decisions if necessary  
            6. Close the thinking section with </thinking>
            7. Provide your final answer in a JSON array format containing only the new file paths.

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


    #testing 
    system_prompt2 = """
                       You are an assistant that helps with software engineering tasks. Run handle_clone_task to clone the github repository into this directory.
 """
    
    correction_prompt2 = """
make sure the repo is actually cloned, and tell me the path to the repo.

"""
    # Example usage
    model_name = "qwen2.5:7b"
    backend = "ollama"
    agent = CodingAgent(model_name, backend, system_prompt, correction_prompt)
    
    # Example 1: Simple modification
    task1 = "add a \"hello world\" to the main page.tsx"
    # result1 = agent.analyze_task(file_tree, task1)
    # print("\nFinal Result 1:")
    # print(json.dumps(result1, indent=2))
    
    # # Example 2: Creating new component
    # task2 = "create a new button component with a primary style"
    # print("\nTask 2 - Creating New Component:")
    # result2 = agent.analyze_task(file_tree, task2)
    # print("\nFinal Result 2:")
    # print(json.dumps(result2, indent=2))
    # node = CodingAgent("qwen2.5:7b", "ollama", "You are a helpful assistant.")
    # print(node.model_name)  
    # print(node.backend)


    task0 = "Clone https://github.com/jeli04/acm-hydra into this directory using ensure_repo_cloned."
    print("\nTask 0 - Cloning Repo:")
    response = agent.instruct(task0,task1)
    print("Response:\n", response)
 