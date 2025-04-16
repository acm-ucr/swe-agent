import os
import requests

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

def get_issue_count(owner: str, repo: str) -> dict:
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

if __name__ == "__main__":
    main()