import os
from github import Github
from typing import Dict, Any

def commit_regression_test(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Commits the synthesized regression test to the remote PR branch via PyGithub.
    Updates the PR body to reflect that the test was added.
    """
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("Warning: GITHUB_TOKEN not found. Skipping commit.")
        return state
        
    repo_full_name = state.get("repo_full_name")
    pr_branch = state.get("pr_branch") # Passed by PR agent or orchestrator
    pr_number = state.get("pr_number")
    test_code = state.get("regression_test_code")
    failing_file = state.get("failing_file", "unknown")
    
    if not all([repo_full_name, pr_branch, test_code]):
        print("Missing required state keys for committing the test.")
        return state
        
    try:
        g = Github(github_token)
        repo = g.get_repo(repo_full_name)
        
        # We need a file path for the test. 
        # Usually tests are stored in a tests/ directory.
        failing_file_stem = failing_file.split('/')[-1].replace(".py", "")
        test_file_path = f"tests/test_{failing_file_stem}_regression.py"
        
        # Commit the file to the branch
        commit_message = f"test(regression): auto-generated test for {failing_file_stem}"
        
        try:
            # Check if file exists to update, else create
            contents = repo.get_contents(test_file_path, ref=pr_branch)
            repo.update_file(contents.path, commit_message, test_code, contents.sha, branch=pr_branch)
            print(f"Updated existing test file: {test_file_path}")
        except:
            # File does not exist, create it
            repo.create_file(test_file_path, commit_message, test_code, branch=pr_branch)
            print(f"Created new test file: {test_file_path}")
            
        # Update PR body if PR number is known
        if pr_number:
            pr = repo.get_pull(int(pr_number))
            new_body = pr.body + "\n\n✅ **Regression Test Added**: A new test was synthesized to prevent this root cause from returning."
            pr.edit(body=new_body)
            print(f"Updated PR #{pr_number} description.")
            
        state["regression_test_committed"] = True
        
    except Exception as e:
        print(f"Failed to commit regression test: {e}")
        state["regression_test_committed"] = False
        
    return state
