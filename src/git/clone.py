import re
import subprocess


def clone_branch(repo_url, branch):
    """Clone a repo directly on the specified branch."""
    cmd = ["git", "clone", "--branch", branch, repo_url]
    subprocess.run(cmd, check=True)


def list_branches(repo_dir="."):
    """Return a list of local branch names."""
    result = subprocess.run(
        ["git", "branch", "--format=%(refname:short)", "--remotes"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.split()


def max_infolettre(branch_list):
    """Return the highest N among subfolders named infolettre_N."""
    max_num = 0
    for branch in branch_list:
        match = re.fullmatch(r"infolettre_(\d+)", branch)
        if match:
            num = int(match.group(1))
            max_num = max(max_num, num)
    return max_num
