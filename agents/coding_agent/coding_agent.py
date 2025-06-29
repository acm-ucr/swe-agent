import sys
import ollama 
import json
import logging
import re
import subprocess
import os
from agents.node import Node
from typing import Dict, List
from datetime import datetime
from shared.ollama_tools.ollama_tools import generate_function_description, use_tools
from shared.github_tools import ensure_repo_cloned,clone_repo, repo_to_fileTree 
from shared.file_tools import fetch_files_from_codebase, edit_files_from_codebase, create_file
from shared.shell_tools import open_subprocess, run_command, retrieve_subprocess_output

tools = [
    generate_function_description(ensure_repo_cloned),
    generate_function_description(clone_repo),
    generate_function_description(repo_to_fileTree),
]

class CodingAgent(Node):
    def __init__(self, model_name, backend, sys_msg, correction_prompt, 
                 task_analysis_prompt, line_identification_prompt, action_selection_prompt,
                 replace_content_prompt, add_content_prompt, new_file_prompt):
        super().__init__(model_name, backend, sys_msg)

        # intialize attributes for intermediate steps such as models
        self.correction_prompt = correction_prompt
        self.task_analysis_prompt = task_analysis_prompt
        self.line_identification_prompt = line_identification_prompt
        self.action_selection_prompt = action_selection_prompt
        self.replace_content_prompt = replace_content_prompt
        self.add_content_prompt = add_content_prompt
        self.new_file_prompt = new_file_prompt

    def analyze_task(self, file_tree: str, task: str, max_tries: int = 5) -> Dict[str, List[str]]:
        """
        Main function that analyzes a task and determines all necessary file actions.
        
        Args:
            file_tree (str): ASCII representation of the file tree
            task (str): Description of the task to be performed
            
        Returns:
            Dict[str, List[str]]: Dictionary containing all file actions needed
        """
        messages = [
            ('system', self.task_analysis_prompt),
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
                
                # Extract JSON using markers
                result = self._extract_json_from_response(content)
                
                if result is None:
                    raise json.JSONDecodeError("Could not extract valid JSON", content, 0)

                # Separate paths into modify and create based on existence in file tree
                modify_paths = []
                create_paths = []
                
                for path in result:
                    # Check if file exists in file tree with various path formats
                    path_found = False
                    
                    # Try exact match
                    if path in file_tree:
                        path_found = True
                    
                    # Try checking each line
                    if not path_found:
                        for line in file_tree.split('\n'):
                            if path in line or path.split('/')[-1] in line:
                                path_found = True
                                break
                    
                    if path_found:
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
                    messages.append(('user', self.correction_prompt))
                else:
                    logging.error("Maximum retries reached. Could not get valid JSON response.")
                    return {"modify": [], "create": []}
            except Exception as e:
                logging.error(f"Unexpected error in analyze_task: {str(e)}")
                return {"modify": [], "create": []}

        return {"modify": [], "create": []}
    
    def _extract_json_from_response(self, response: str) -> List[str]:
        """
        Extracts JSON array from structured model response.
        
        Args:
            response: Raw response from the model
            
        Returns:
            List[str]: Extracted file paths, or None if parsing fails
        """
        # Look for START_FILES and END_FILES markers
        start_marker = "START_FILES"
        end_marker = "END_FILES"
        
        # Find the markers
        start_idx = response.find(start_marker)
        end_idx = response.find(end_marker)
        
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            # Extract content between markers
            json_start = start_idx + len(start_marker)
            json_content = response[json_start:end_idx].strip()
            
            try:
                result = json.loads(json_content)
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass
        
        # Fallback: look for any JSON array in the response
        return self._fallback_json_parse(response)
    
    def _fallback_json_parse(self, response: str) -> List[str]:
        """
        Fallback JSON parsing when structured markers aren't found.
        
        Args:
            response: Raw model response
            
        Returns:
            List[str]: Best attempt at extracting file paths, or None if nothing found
        """
        # Look for JSON array patterns
        import re
        
        # Find patterns like ["file1.py", "file2.py"]
        json_pattern = r'\[[\s\S]*?\]'
        matches = re.findall(json_pattern, response)
        
        for match in matches:
            try:
                result = json.loads(match)
                if isinstance(result, list) and all(isinstance(item, str) for item in result):
                    return result
            except json.JSONDecodeError:
                continue
        
        # Final fallback: return None to trigger retry
        return None

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
        # For new files, generate complete content
        if not existing_content.strip():
            prompt = self.new_file_prompt.format(task=task, file_path=file_path)
        else:
            # For existing files, use bounded modification approach
            return self._modify_existing_file(task, file_path, existing_content)

        response = ollama.chat(
            model=self.model_name,
            messages=[{'role': 'user', 'content': prompt}]
        )
        
        # Parse the structured response
        raw_content = response['message']['content']
        return self._extract_code_from_response(raw_content)
    
    def _modify_existing_file(self, task: str, file_path: str, existing_content: str) -> str:
        """
        Modifies existing file content using a simple multi-step approach.
        
        Args:
            task: The task description
            file_path: Path of the file to modify
            existing_content: Current content of the file
            
        Returns:
            str: Modified file content
        """
        # Step 1: Identify WHERE to modify (just line numbers)
        target_line = self._identify_target_line(task, file_path, existing_content)
        
        # Step 2: Determine WHAT ACTION to take (simplified choices)
        action = self._determine_action(task, target_line, existing_content)
        
        # Step 3: Generate CONTENT (focused generation)
        content = self._generate_modification_content(task, file_path, action)
        
        # Step 4: Apply the modification
        return self._apply_simple_modification(existing_content, target_line, action, content)
    
    def _identify_target_line(self, task: str, file_path: str, existing_content: str) -> int:
        """
        Step 1: Just identify which line number to target.
        
        Args:
            task: The task description
            file_path: Path of the file to modify
            existing_content: Current content of the file
            
        Returns:
            int: Target line number
        """
        lines = existing_content.split('\n')
        total_lines = len(lines)
        
        # Show numbered content for line identification
        numbered_content = '\n'.join(f"{i+1:3}: {line}" for i, line in enumerate(lines))
        
        line_prompt = self.line_identification_prompt.format(
            task=task, 
            file_path=file_path, 
            numbered_content=numbered_content,
            total_lines=total_lines,
            middle_line=total_lines // 2
        )

        response = ollama.chat(
            model=self.model_name,
            messages=[{'role': 'user', 'content': line_prompt}]
        )
        
        # Extract line number with fallback
        try:
            line_text = response['message']['content'].strip()
            # Extract first number found
            import re
            numbers = re.findall(r'\d+', line_text)
            if numbers:
                line_num = int(numbers[0])
                # Validate and clamp to reasonable bounds
                return max(1, min(line_num, total_lines + 1))
        except:
            pass
        
        # Fallback based on task keywords
        task_lower = task.lower()
        if 'middle' in task_lower:
            return max(1, total_lines // 2)
        elif 'beginning' in task_lower or 'start' in task_lower:
            return 1
        elif 'end' in task_lower:
            return total_lines
        else:
            return max(1, total_lines // 2)  # Default to middle
    
    def _determine_action(self, task: str, target_line: int, existing_content: str) -> str:
        """
        Step 2: Determine what type of action to take (simplified choices).
        
        Args:
            task: The task description
            target_line: The target line number
            existing_content: Current content of the file
            
        Returns:
            str: Action type ('add_after', 'add_before', 'replace')
        """
        action_prompt = self.action_selection_prompt.format(task=task, target_line=target_line)

        response = ollama.chat(
            model=self.model_name,
            messages=[{'role': 'user', 'content': action_prompt}]
        )
        
        # Parse response with fallback
        choice = response['message']['content'].strip().upper()
        
        if 'A' in choice or 'AFTER' in choice.upper():
            return 'add_after'
        elif 'B' in choice or 'BEFORE' in choice.upper():
            return 'add_before'
        elif 'C' in choice or 'REPLACE' in choice.upper():
            return 'replace'
        else:
            # Fallback based on task keywords
            task_lower = task.lower()
            if 'replace' in task_lower or 'change' in task_lower:
                return 'replace'
            elif 'add' in task_lower or 'insert' in task_lower or 'comment' in task_lower:
                return 'add_after'
            else:
                return 'add_after'  # Safe default
    
    def _generate_modification_content(self, task: str, file_path: str, action: str) -> str:
        """
        Step 3: Generate the specific content to add/replace.
        
        Args:
            task: The task description
            file_path: Path of the file to modify
            action: The action type
            
        Returns:
            str: Generated content
        """
        if action == 'replace':
            content_prompt = self.replace_content_prompt.format(task=task, file_path=file_path)
        else:  # add_after or add_before
            content_prompt = self.add_content_prompt.format(task=task, file_path=file_path)

        response = ollama.chat(
            model=self.model_name,
            messages=[{'role': 'user', 'content': content_prompt}]
        )
        
        content = response['message']['content'].strip()
        
        # Clean up common artifacts
        content = self._clean_generated_content(content)
        
        return content
    
    def _clean_generated_content(self, content: str) -> str:
        """
        Cleans up generated content to remove common artifacts.
        
        Args:
            content: Raw generated content
            
        Returns:
            str: Cleaned content
        """
        # Remove markdown code blocks
        if content.startswith('```') and content.endswith('```'):
            lines = content.split('\n')
            if len(lines) > 2:
                content = '\n'.join(lines[1:-1])
        
        # Remove single backticks
        content = content.strip('`')
        
        # Remove common prefixes
        prefixes_to_remove = ['Content:', 'Output:', 'Result:', 'Answer:']
        for prefix in prefixes_to_remove:
            if content.startswith(prefix):
                content = content[len(prefix):].strip()
        
        # If content is suspiciously short or empty, provide fallback
        if len(content.strip()) < 3:
            return "# Generated content"
        
        return content.strip()
    
    def _apply_simple_modification(self, existing_content: str, target_line: int, action: str, content: str) -> str:
        """
        Step 4: Apply the modification to the content.
        
        Args:
            existing_content: Current file content
            target_line: Line number to target
            action: Action type ('add_after', 'add_before', 'replace')
            content: Content to add/replace
            
        Returns:
            str: Modified content
        """
        lines = existing_content.split('\n')
        
        if action == 'add_after':
            # Insert after target line
            if target_line <= len(lines):
                lines.insert(target_line, content)
            else:
                lines.append(content)
        
        elif action == 'add_before':
            # Insert before target line
            insert_pos = max(0, target_line - 1)
            lines.insert(insert_pos, content)
        
        elif action == 'replace':
            # Replace target line
            if 1 <= target_line <= len(lines):
                lines[target_line - 1] = content
            else:
                # If target line doesn't exist, append instead
                lines.append(content)
        
        return '\n'.join(lines)

    def _extract_code_from_response(self, response: str) -> str:
        """
        Extracts code content from structured model response.
        
        Args:
            response: Raw response from the model
            
        Returns:
            str: Extracted code content, or fallback if parsing fails
        """
        # Look for START_CODE and END_CODE markers
        start_marker = "START_CODE"
        end_marker = "END_CODE"
        
        # Find the markers
        start_idx = response.find(start_marker)
        end_idx = response.find(end_marker)
        
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            # Extract content between markers
            code_start = start_idx + len(start_marker)
            extracted = response[code_start:end_idx].strip()
            
            # Basic sanity check - ensure we have some content
            if len(extracted) > 0:
                return extracted
        
        # Fallback: try to clean the raw response
        return self._fallback_parse(response)
    
    def _fallback_parse(self, response: str) -> str:
        """
        Fallback parsing when structured markers aren't found.
        
        Args:
            response: Raw model response
            
        Returns:
            str: Best attempt at extracting useful content
        """
        # Remove common markdown artifacts
        cleaned = response.strip()
        
        # Remove code block markers if present
        if cleaned.startswith('```'):
            lines = cleaned.split('\n')
            if len(lines) > 1:
                # Remove first line (```python, ```javascript, etc.)
                lines = lines[1:]
                # Remove last line if it's just ```
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                cleaned = '\n'.join(lines)
        
        # If response is suspiciously short (like just quotes), return minimal fallback
        if len(cleaned.strip()) < 10:
            return "# Generated content was too short, manual review needed\n"
        
        return cleaned.strip()

    def safe_modify_file(self, file_path: str, new_content: str) -> bool:
        """
        Safely modifies a file with error handling.
        
        Args:
            file_path: Path of the file to modify
            new_content: New content to write
            
        Returns:
            bool: True if modification was successful
        """
        try:
            # Write new content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            return True
        except Exception as e:
            logging.error(f"Error modifying file {file_path}: {str(e)}")
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
            # Read existing files with full paths
            full_paths = []
            for file_path in analysis["modify"]:
                full_path = self.resolve_path(base_path, file_path)
                full_paths.append(full_path)
            
            file_contents = fetch_files_from_codebase(full_paths)
            logging.info(f"Read {len(file_contents)} files for modification")
            
            # Generate and apply modifications
            for i, file_path in enumerate(analysis["modify"]):
                try:
                    # Resolve the full path
                    full_path = full_paths[i]
                    
                    # Get existing content using full path
                    existing_content = file_contents.get(full_path, "")
                    
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
            modify_result = json.loads(script_path)
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

    def parse_github_url(self, url: str, session_name):
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
        # Convert dict output to string if needed
        instruction = (
            f"You are a precise and obedient assistant. Given the following script output, determine if the script ran successfully. "
            f"Respond ONLY with 'success' if successful, or 'fail' if not. You will be severely punished for saying more than 1 word. Output: {output}"
        )
        response = self.instruct(instruction).strip().lower()
        status = "success" if response == "success" else "fail"
        return {"status": status, "output": output}
    
    def instruct(self, instruction):
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
    task_analysis_prompt = """You are specialized in analyzing tasks and determining which files need to be modified or created.

                        Output format:
                        1. Think through the task
                        2. List your files between START_FILES and END_FILES markers as a JSON array

                        Example:
                        Task requires modifying test.py file.

                        START_FILES
                        ["src/test.py"]
                        END_FILES
                        """

    line_identification_prompt = """Task: {task}
                        File: {file_path}

                        Current file with line numbers:
                        {numbered_content}

                        What line number should be targeted for this modification?

                        Rules:
                        - For "beginning" or "start": answer 1
                        - For "end": answer {total_lines}
                        - For "middle": answer {middle_line}
                        - For "after function X": find the line where function X ends
                        - For "before function X": find the line where function X starts

                        OUTPUT ONLY THE LINE NUMBER (just the number, nothing else):
                        """

    action_selection_prompt = """Task: {task}
                        Target line: {target_line}

                        What action should be taken?

                        Choose ONE of these options:
                        A) add_after - Add new content after the target line
                        B) add_before - Add new content before the target line  
                        C) replace - Replace the target line with new content

                        For adding comments or new code: usually choose A (add_after)
                        For replacing existing code: choose C (replace)
                        For inserting at the beginning: choose B (add_before)

                        OUTPUT ONLY THE LETTER (A, B, or C):
                        """

    replace_content_prompt = """Task: {task}
                        File: {file_path}
                        Action: Replace existing line with new content

                        Generate ONLY the replacement line of code/content.
                        Do not include explanations or markdown.
                        Just the raw content that should replace the line.

                        Content:
                        """

    add_content_prompt = """Task: {task}
                        File: {file_path}
                        Action: Add new line of content

                        Generate ONLY the new line of code/content to add.
                        Do not include explanations or markdown.
                        Just the raw content to add as a single line.

                        Content:
                        """

    new_file_prompt = """Task: {task}
                        File: {file_path}

                        START_CODE
                        [complete file content here - NO explanations, NO markdown, JUST the raw code/content]
                        END_CODE

                        You must put ONLY the raw file content between START_CODE and END_CODE. Do not include any explanations, descriptions, or markdown formatting.
                        """


    # Example usage
    model_name = "qwen2.5:7b"
    backend = "ollama"
    agent = CodingAgent(
        model_name, 
        backend, 
        system_prompt, 
        correction_prompt,
        task_analysis_prompt,
        line_identification_prompt, 
        action_selection_prompt,
        replace_content_prompt, 
        add_content_prompt, 
        new_file_prompt
    )

    
    # Example 1: Simple modification
    task1 = "add a \"hello world\" to the main page.tsx"
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

    # node = CodingAgent("qwen2.5:7b", "ollama", "You are a helpful assistant.")
    # print(node.model_name)  
    # print(node.backend)


    task0 = "Clone https://github.com/jeli04/acm-hydra into this directory using ensure_repo_cloned."
    print("\nTask 0 - Cloning Repo:")
    response = agent.instruct(task0,task1)
    print("Response:\n", response)
 


    task = "Add a 'hello world' comment in the end of test.py. dont make ANY other changes"
    base_path = "/Users/henry/Documents/GitHub/SWE-Agent-test"
    
    print("\nExecuting task:", task)
    result = agent.execute_task(file_tree, task, base_path)
    print("\nTask execution result:")
    print(json.dumps(result, indent=2))

    os.remove(dummy_script_path)
