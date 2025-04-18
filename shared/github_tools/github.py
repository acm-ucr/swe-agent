import os
import requests
from git import Repo, exc

# GitHub API URL
GITHUB_API_URL = "https://api.github.com"

# Retrieve your GitHub token from the environment variable
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("Please set your GITHUB_TOKEN environment variable.")

HEADERS = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
        }

def stage_and_commit_files(repo_path: str, file_paths: list, commit_message: str) -> bool:
    """
    Stages and commits specified files to the local Git repository.

    Args:
        repo_path: The path to the local Git repository.
        file_paths: A list of file paths to stage for commit.
        commit_message: The commit message to use.

    Returns:
        bool: True if the commit was successful, False otherwise.
    """
    try:

        # Initialize the repo object for the current directory
        repo = Repo(repo_path)

        # Stage the specified files
        for file_path in file_paths:
            repo.git.add(file_path)

        # Create the commit with the provided message
        repo.git.commit("-m", commit_message)

        print(f"Successfully committed {len(file_paths)} files with message: '{commit_message}'")
        return True
    except exc.GitCommandError as e:
        print(f"Git command error: {str(e)}")
        return False
    except Exception as e:
        print(f"Error committing files: {str(e)}")
        return False

def get_issue_count(owner: str, repo: str) -> int:
    """
    Retrieves the number of issues in a GitHub repository.
    owner: The owner of the GitHub repository.
    repo: The name of the GitHub repository.
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    all_items = response.json()

    # Filter out pull requests
    issues_only = [item for item in all_items if "pull_request" not in item]
    return len(issues_only)

def get_github_issue(owner: str, repo: str, issue_number: int) -> dict:
    """
    Retrieves a GitHub issue's details.
    owner: The owner of the GitHub repository.
    repo: The name of the GitHub repository.
    """

    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def create_github_issue(owner: str, repo: str, title: str, body: str) -> dict:
    """
    Creates a GitHub issue the specified repository with the given title and body.
    owner: The owner of the GitHub repository.
    repo: The name of the GitHub repository.
    title: The title of the issue.
    body: The body of the issue.
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues"
    # Create the issue.
    response = requests.post(url, headers=HEADERS, json={"title": title, "body": body})

    if response.status_code != 201:
        print("Error creating issue:", response.content)
        return None
    issue = response.json()
    print("Created issue:", issue.get("html_url", ""))

    return issue

def close_github_issue(owner: str, repo: str, issue_number: int) -> dict:
    """
    Closes a GitHub issue in the specified repository.
    owner: The owner of the GitHub repository.
    repo: The name of the GitHub repository.
    issue_number: The number of the issue to close.
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}"
    response = requests.patch(url, headers=HEADERS, json={"state": "closed"})
    if response.status_code != 200:
        print("Error closing issue:", response.content)
        return None
    issue = response.json()
    print("Closed issue:", issue.get("html_url", ""))
    return issue

def merge_github_branch(owner: str, repo: str, head: str, base: str = "main") -> dict:
    """
    Merges a GitHub branch into another branch in the specified repository.
    owner: The owner of the GitHub repository.
    repo: The name of the GitHub repository.
    head: The name of the branch to merge from.
    base: The name of the branch to merge into (defaults to main).
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/merges"
    payload = {
            "base": base,
            "head": head,
            "commit_message": f"Merge {head} into {base}"
            }
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code != 201:
        print("Error merging branches:", response.content)
        return None
    merge_result = response.json()
    print(f"Successfully merged {head} into {base}")
    return merge_result

def close_github_pull_request(owner: str, repo: str, pull_number: int) -> dict:
    """
    Closes a GitHub pull request in the specified repository.
    owner: The owner of the GitHub repository.
    repo: The name of the GitHub repository.
    pull_number: The number of the pull request to close.
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pull_number}"
    response = requests.patch(url, headers=HEADERS, json={"state": "closed"})
    if response.status_code != 200:
        print("Error closing pull request:", response.content)
        return None
    pr = response.json()
    print("Closed pull request:", pr.get("html_url", ""))
    return pr

def get_pr_count(owner: str, repo: str) -> dict:
    """
    Retrieves the number of pull requests in a GitHub repository.
    owner: The owner of the GitHub repository.
    repo: The name of the GitHub repository.
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    all_items = response.json()

    # Filter out pull requests
    issues_only = [item for item in all_items if "pull_request" in item]
    return len(issues_only)

def get_github_pr(owner: str, repo: str) -> dict:
    """
    Retrieves a GitHub pull request's details.
    owner: The owner of the GitHub repository.
    repo: The name of the GitHub repository.
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def create_pull_request(owner, repo, issue_number, branch_name, base="main"):
    """
    Creates a GitHub pull request based on the Owner's repo and issue number under a branch.
    owner: The owner of the GitHub repository.
    repo: The name of the GitHub repository.
    issue_number: The issue number to link to the pull request.
    """

    # Use HEADERS so that our token and proper Accept header are included.
    headers = HEADERS

    # Retrieve the issue details from GitHub
    issue_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}"
    issue_response = requests.get(issue_url, headers=headers)
    if issue_response.status_code != 200:
        print("Error retrieving issue details:", issue_response.content)
        return None
    issue_details = issue_response.json()

    # Check if the issue already has a linked pull request.
    if "pull_request" in issue_details:
        print(f"Issue #{issue_number} already has a linked pull request. Skipping creation.")
        return None

    # Construct the PR title and body.
    issue_title = issue_details.get("title", "").strip()
    issue_body = issue_details.get("body", "")
    pr_title = f"[#{issue_number}] {issue_title}"
    pr_body = f"Closes #{issue_number}\n\n{issue_body}"

    # Prepare the payload to create the pull request.
    pr_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls"
    payload = {
            "title": pr_title,
            "body": pr_body,
            "head": branch_name,  # This should be the branch you're on, i.e., "test"
            "base": base         # The branch to merge into, i.e., "main"
            }
    print("Payload for PR creation:", payload)

    # Create the pull request.
    pr_response = requests.post(pr_url, headers=headers, json=payload)
    if pr_response.status_code != 201:
        print("Error creating pull request:", pr_response.content)
        return None
    pr = pr_response.json()
    print("Created PR:", pr.get("html_url", ""))
    return pr

def total_prs(owner, repo, head, base):
    """
    Get's the total number of pull requests from a branch to another.
    owner: The owner of the GitHub repository.
    repo: The name of the GitHub repository.
    head: The branch to merge from.
    base: The branch to merge into.
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls"
    # The head parameter must be in the format "owner:branch"
    params = {"head": f"{owner}:{head}", "base": base, "state": "all"}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return len(response.json())


def create_new_branch(owner, repo, new_branch, base = "main"):
    """
    Creates a new branch in the specified GitHub repository.
    owner: The owner of the GitHub repository.
    repo: The name of the GitHub repository.
    new_branch: The name of the new branch to create.
    base: The name of the base branch to branch from (default is "main").
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/refs/heads/{base}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print("Error retrieving sha", response.content)
        return None
    sha = response.json()["object"]["sha"]
    post_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/refs"
    payload = {
            "ref": f"refs/heads/{new_branch}",
            "sha": sha
            }
    post_response = requests.post(post_url, headers = HEADERS, json= payload)
    if post_response.status_code == 201:
        print("Branch created.")

def main():
    owner = "Jeli04"
    repo = "SWE-Agent-test"
    issue_number = 4

    # Print number of issues
    issue_count = get_issue_count(owner, repo)
    print("Number of issues:", issue_count)

    # Retrieve the issue details
    issue_details = get_github_issue(owner, repo, issue_number)
    issue_title = issue_details.get("title", "").strip()
    print("Issue Title:", issue_title)
    print("Issue Details:", issue_details.get('body', 'No details provided'))

    # Since you are on your "test" branch, set branch_name accordingly.
    branch_name = "test"  # This is your current branch
    head = branch_name
    base = "main"  # Assuming you want to merge into the main branch

    # Print the number of PRs from "test" to "main"
    num_prs = get_pr_count(owner, repo)
    print("Number of PRs:", num_prs)

    # Create the pull request from the test branch (if one doesn't already exist)
    try:
        pr_response = create_pull_request(owner, repo, issue_number, branch_name, base=base)
    except requests.exceptions.HTTPError as e:
        print(f"Error creating PR: {e.response.json()}")

def fetch_files_from_codebase(file_paths: list) -> dict:
    """
    Fetches files from a local repository's codebase.

    Args:
        file_paths: A list of specific file paths to fetch.

    Returns:
        A dictionary where keys are file paths and values are file contents as strings.
        If a file cannot be opened (e.g., it doesn't exist), the path will not be included in the result.
    """
    file_contents = {}
    for path in file_paths:
        try:
            with open(path, 'r', encoding='utf-8') as file:
                file_contents[path] = file.read()
        except FileNotFoundError:
            pass
    return file_contents

def edit_files_from_codebase(file_updates: dict) -> dict:
    """
    Overwrites multiple files in the local codebase with new content.
    Args:
        file_updates (dict): A dictionary where:
            - Keys are file paths (relative or absolute).
            - Values are the new content (as strings) to write into each file.
    Returns:
        dict: A dictionary summarizing the result for each file:
            - If successful: { "file_path": "success" }
            - If failed: { "file_path": "error: <error message>" }
    """
    results = {}
    for file_path, new_content in file_updates.items():
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
            results[file_path] = "success"
        except Exception as e:
            results[file_path] = f"error: {str(e)}"
    return results

if __name__ == "__main__":
    main()
