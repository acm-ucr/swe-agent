import subprocess
import time 

def open_subprocess(session_name: str) -> subprocess.Popen:
    """
    Opens a persistent subprocess.
    session_name: Session name of the tmux session.
    """
    # Create a new detached tmux session running an interactive bash shell.
    subprocess.run(["tmux", "new-session", "-d", "-s", session_name, "bash"])
    print(f"Tmux session '{session_name}' started.")

def retrieve_subprocess_output(session_name: str, num_lines: int = 50) -> str:
    """
    Gets the number of lines from the tmux session based on the num_lines parameter.
    session_name: Session name of the tmux session.
    num_lines: Number of lines to retrieve from the tmux session.
    """ 

    result = subprocess.run(
        ["tmux", "capture-pane", "-t", session_name, "-p", "-S", f"-{num_lines}"],
        stdout=subprocess.PIPE,
        text=True
    )
    return result.stdout

def run_command(command: str, session_name: str) -> tuple:
    """
    Excutes a shell command in the named tmux session and returns the output of that execution.
    command: The command to execute in the shell.
    session_name: The name of the tmux session.
    """
    # Send the command to the tmux session. "C-m" simulates the Enter key.
    subprocess.run(["tmux", "send-keys", "-t", session_name, command, "C-m"])
    
    # Wait briefly to let the command execute and produce output.
    time.sleep(0.5)
    
    # Capture the content of the tmux pane (last 100 lines for example).
    result = subprocess.run(
        ["tmux", "capture-pane", "-t", session_name, "-p", "-S", "-100"],
        stdout=subprocess.PIPE,
        text=True
    )
    captured_output = result.stdout

    return captured_output



if __name__ == "__main__":
    session = "my_session"
    # Start the persistent tmux session.
    # open_subprocess(session)
    
    # Run a command in that tmux session.
    # stdout = run_command("ls -l", session)
    # stdout = run_command("cd /Users/jerryli/Desktop/python/SWE-Agent-test/test_project", session)
    # stdout = run_command("npm run dev", session)
    # stdout = run_command("C-c", session)
    stdout = retrieve_subprocess_output(session)
    print("Captured Output:")
    print(stdout)