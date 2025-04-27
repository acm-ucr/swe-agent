import git
import ollama
import os
from tests.github_tools_test import test_merge_github_branch, test_close_github_pull_request, test_fetch_files_from_codebase, test_edit_files_from_codebase

def run_test():
    print("Running github API tests.....\n\n")
    test_edit_files_from_codebase()
    test_close_github_pull_request()
    test_fetch_files_from_codebase()
    test_merge_github_branch()
    print("\n\nAll tests successful....")

def main():
    print("\n\nWhich LLM Agent would you like to run?")
    print("--------------------------------------")
    print("\t1) Assignment Agent")
    print("\t2) Coding  Agent")
    print("\t3) Reasoning Agent")
    print("\t4) Review Agent")
    print("\t5) Quit")
    print("--------------------------------------\n\n")
    user_choice = int(input("Enter Choice: "))

    if (user_choice == 1):
        print("nice")
    elif (user_choice == 2):
        print("nice")
    elif (user_choice == 3):
        print("nice")
    elif (user_choice == 4):
        print("nice")
    elif (user_choice == 5):
        exit(0)
    else:
        raise ValueError


if __name__ == "__main__":
    run_test()
    main()
    