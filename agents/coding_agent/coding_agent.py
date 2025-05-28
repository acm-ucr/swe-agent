import sys
import ollama 
import json
import logging
from agents.node import Node
from typing import Dict, List
from shared.shell_tools import open_subprocess, run_command, retrieve_subprocess_output

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

    def instruct(self, instruction):
        """
        Instructs the agent to perform a task.
        """
        # use this as the function to call, modify it if neccessary 
        response = super().instruct(instruction)

        return response
    
    def generate_command(self, script_path: str):
        """
        Determines the shell command to use to run the given script or project directory.

        Args:
            script_path (str): The path to the script file or project directory.

        Returns:
            str: The shell command to run the script or project.
        """
        # Search for package.json in the root
        workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
        package_json_path = os.path.join(workspace_root, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r", encoding="utf-8") as f:
                    package_data = json.load(f)
                scripts = package_data.get("scripts", {})
                if "dev" in scripts:
                    return "npm i && npm run dev"
                elif "start" in scripts:
                    return "npm i && npm start"
            except Exception:
                pass

        # Otherwise, use LLM to generate the command
        instruction = (
            f"You are a precise and obedient coding assistant. "
            f"Based on the file extension and context, determine the appropriate shell command to run the script: {script_path}. "
            f"Say ONLY the command. Your exact response will be used for the command. You will be punished for any additional words or explanations."
        )
        response = self.instruct(instruction)
        return response.strip()

    def check_status(self, script_path: str, id: str) -> tuple:
        """
        Checks if the given script runs successfully using a specified command.

        Args:
            script_path (str): The path to the script to run.

        Returns:
            dict: A JSON-like dictionary containing the result of the execution.
        """
        session_name = id
        try:
            # Open a tmux session
            open_subprocess(session_name)
            shell_command = self.generate_command(script_path)
            print(f"Generated command: {shell_command}")
            run_command(shell_command, session_name)
            output = retrieve_subprocess_output(session_name)
            return output, "success"
        except Exception as e:
            return str(e), "fail"

    def is_successful_output(self, output: str) -> dict:
        """
        Determines if the script output indicates a successful run.

        Args:
            output (str): The output from running the script.

        Returns:
            json: {"status": "success" or "fail", "output": output}
        """
        max_retries = 3
        for _ in range(max_retries):
            instruction = (
                f"You are a precise and obedient assistant. Given the following script output, determine if the script ran successfully. "
                f"Respond ONLY with 'success' if successful, or 'fail' if not. You will be severely punished for saying more than 1 word. Output: {output}"
            )
            response = self.instruct(instruction).strip().lower()
            if response in ("success", "fail"):
                status = "success" if response == "success" else "fail"
                return {"status": status, "output": output}
        # If no valid response after retries, default to fail
        return {"status": "fail", "output": output}
    

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    # check file status test
    agent = CodingAgent("cogito:3b", "ollama", "You are a helpful assistant.")

    dummy_script_path = "dummy_script.py"
    with open(dummy_script_path, "w") as f:
        f.write("print('Hello, World!')\n" \
        "print('This is a test script.')")
    id = "11111"
    result = agent.check_status(dummy_script_path, id)
    print("Check Status Result:")
    if result[1] == "fail":
        print({"status": "fail", "output": result[0]})
        quit()
    else:
        print(agent.is_successful_output(result))

        
    # write to file test
    
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
    
    file_tree = """
                    app/
                    page.tsx
                    notrelevant.tsx
                """
                        
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

    os.remove(dummy_script_path)
