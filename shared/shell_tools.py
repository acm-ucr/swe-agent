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


#windows commands

def run_shell_command(command: str, proc: subprocess.Popen, max_lines=30) -> str:
    if proc.poll() is not None:
        raise RuntimeError("PowerShell process has exited.")
    
    proc.stdin.write(command.strip() + "\n")
    proc.stdin.write("echo __END__\n")
    proc.stdin.flush()

    output_lines = []
    for _ in range(max_lines):
        line = proc.stdout.readline()
        print(f"DEBUG: {line.strip()}")
        output_lines.append(line)
        if "__END__" in line:
            break
    return "".join(output_lines)

process = subprocess.Popen(
    ["powershell", "-NoExit"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)


if __name__ == "__main__":
    session = "my_session"
    # Start the persistent tmux session.
    # open_subprocess(session)


    # Run a command in that tmux session.
    # stdout = run_command("ls -l", session)
    # stdout = run_command("cd /Users/jerryli/Desktop/python/SWE-Agent-test/test_project", session)
    # stdout = run_command("npm run dev", session)
    # stdout = run_command("C-c", session)
    # stdout = retrieve_subprocess_output(session)

    try:
        print(run_shell_command('cd "C:/Users/inegi_pqetia/Documents/ACM DAS/swe-agent/acm-hydra"; git checkout -b test; git branch --show-current', process))

    finally:
        process.stdin.write("exit\n")
        process.stdin.flush()
        process.wait()