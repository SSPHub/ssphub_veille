import subprocess


def clone_branch(repo_url, branch):
    """Clone a repo directly on the specified branch."""
    cmd = ["git", "clone", "--branch", branch, repo_url]
    subprocess.run(cmd, check=True)
