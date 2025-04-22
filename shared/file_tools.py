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

def create_file(name: str, type: str, path: str = "", content: str = "") -> None:
    """
    Creates new file of the file type based on the arguements name and type
    name: The name of the file
    type: The file type to be created
    path: Optional path for the new file, if not specified assume in current directory
    content: Optional content of the new file, if not specified assume no content
    """
    with open(path + name + "." + type, 'w') as f: 
        f.write(content)