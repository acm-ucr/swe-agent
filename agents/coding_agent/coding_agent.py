import ollama 
from agents.node import Node
from shared.shell_tools import open_subprocess, run_command, retrieve_subprocess_output

class CodingAgent(Node):
    def __init__(self, model_name, backend, sys_msg):
        super().__init__(model_name, backend, sys_msg)
        self.add_tool(open_subprocess)
        self.add_tool(run_command)
        self.add_tool(retrieve_subprocess_output)

    def instruct(self, instruction):
        """
        Instructs the agent to perform a task.
        """
        response = super().instruct(instruction)

        return response
    
    def generate_command(self, script_path):
        """
        Determines the shell command to use to run the given script.

        Args:
            script_path (str): The path to the script to classify.

        Returns:
            str: The shell command to run the script.
        """
        instruction = (
            f"You are a helpful assistant. Based on the file extension and context, determine the appropriate shell command to run the script: {script_path}. "
            "Say ONLY the command. Your exact response will be used for the command. You will be punished for any additional words or explanations."
        )
        response = self.instruct(instruction)
        return response.strip()

    def check_status(self, script_path):
        """
        Checks if the given script runs successfully using a specified command template.

        Args:
            script_path (str): The path to the script to run.
            command_template (str): A template for the command to execute the script. Defaults to "{script_path}".

        Returns:
            dict: A JSON-like dictionary containing the result of the execution.
        """
        session_name = "check_status_session"
        try:
            # Open a tmux session
            open_subprocess(session_name)
            command = self.generate_command(script_path)
            run_command(command, session_name)
            output = retrieve_subprocess_output(session_name)

            if "Traceback" in output or "Error" in output:
                return {"status": "failure", "error": output}
            else:
                return {"status": "success", "output": output}

        except Exception as e:
            return {"status": "error", "message": str(e)}
    

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()

    agent = CodingAgent("cogito:3b", "ollama", "You are a helpful assistant.")

    dummy_script_path = "dummy_script.py"
    with open(dummy_script_path, "w") as f:
        f.write("print('Hello, World!')")

    command = agent.generate_command(dummy_script_path)
    print(f"Determined command: {command}")

    # Check the status of running the script
    result = agent.check_status(dummy_script_path)
    print("Check Status Result:")
    print(result)

    # Clean up the dummy script
    os.remove(dummy_script_path)
