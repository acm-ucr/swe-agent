from unittest.mock import patch
import os
from github_tools import merge_github_branch, close_github_pull_request, fetch_files_from_codebase, edit_files_from_codebase, fetch_files_from_codebase, edit_files_from_codebase
import tempfile

def test_merge_github_branch():
    print("\nTesting: merge_github_branch")
    with patch('requests.post') as mocked_post:
        mocked_post.return_value.status_code = 201
        mocked_post.return_value.json.return_value = {"merged": True}

        result = merge_github_branch("owner", "repo", "feature-branch", "main")
        assert result == {"merged": True}, f"Expected success, got {result}"
    print("Passed: merge_github_branch")

def test_close_github_pull_request():
    print("\nTesting: close_github_pull_request")
    with patch('requests.patch') as mocked_patch:
        mocked_patch.return_value.status_code = 200
        mocked_patch.return_value.json.return_value = {"html_url": "http://example.com/pull/1"}

        result = close_github_pull_request("owner", "repo", 1)
        assert result["html_url"] == "http://example.com/pull/1", f"Expected HTML URL, got {result}"
        

def test_fetch_files_from_codebase():
    print("\nTesting: fetch_files_from_codebase")
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
        tmp.write("sample content")
        tmp_path = tmp.name

    result = fetch_files_from_codebase([tmp_path, "nonexistent.txt"])
    assert tmp_path in result and result[tmp_path] == "sample content", "Failed to fetch existing file"
    assert "nonexistent.txt" not in result, "Nonexistent file should not be in result"

    os.unlink(tmp_path)  # Cleanup
    print("Passed: fetch_files_from_codebase")

def test_edit_files_from_codebase():
    print("\nTesting: edit_files_from_codebase")
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
        tmp_path = tmp.name

    updates = {tmp_path: "new content"}
    result = edit_files_from_codebase(updates)
    assert result[tmp_path] == "success", f"Expected success on editing, got {result[tmp_path]}"

    with open(tmp_path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert content == "new content", f"Content not updated properly, got {content}"

    os.unlink(tmp_path)  # Cleanup
    print("Passed: edit_files_from_codebase")

def main():
    print("\nRunning all tests...\n")
    test_merge_github_branch()
    test_close_github_pull_request()
    test_fetch_files_from_codebase()
    test_edit_files_from_codebase()
    print("\nAll tests completed successfully!")

if __name__ == '__main__':
    main()
    

    

