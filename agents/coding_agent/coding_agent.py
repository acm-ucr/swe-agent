import ollama 
from agents.node import Node
from shared.shell_tools import open_subprocess, run_command, retrieve_subprocess_output

class CodingAgent(Node):
    def __init__(self, model_name, backend, sys_msg):
        super().__init__(model_name, backend, sys_msg)

    def instruct(self, instruction):
        """
        Instructs the agent to perform a task.
        """
        response = super().instruct(instruction)

        return response
    
    def generate_command(self, script_path: str) -> str:
        """
        Determines the shell command to use to run the given script.

        Args:
            script_path (str): The path to the script to classify.

        Returns:
            str: The shell command to run the script.
        """
        instruction = (
            f"You are a helpful coding assistant. Based on the file extension and context, determine the appropriate shell command to run the script: {script_path}. "
            "Say ONLY the command. Your exact response will be used for the command. You will be punished for any additional words or explanations."
        )
        response = self.instruct(instruction)
        return response.strip()

    def check_status(self, script_path: str, id: str) -> str:
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
            return output
        except Exception as e:
            return str(e)

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
            f"You are a helpful assistant. Given the following script output, determine if the script ran successfully. "
            f"Respond ONLY with 'success' if successful, or 'fail' if not. You will be severely punished for saying more than 1 word. Output: {output}"
        )
        response = self.instruct(instruction).strip().lower()
        status = "success" if response == "success" else "fail"
        return {"status": status, "output": output}
    

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()

    agent = CodingAgent("cogito:3b", "ollama", "You are a helpful assistant.")

    dummy_script_path = "dummy_script.py"
    with open(dummy_script_path, "w") as f:
        f.write("print('Hello, World!')\n" \
        "print('This is a test script.')")
    id = "12345"
    result = agent.check_status(dummy_script_path, id)
    print("Check Status Result:")
    print(agent.is_successful_output(result))

    os.remove(dummy_script_path)
