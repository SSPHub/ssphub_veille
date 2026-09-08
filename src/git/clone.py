import os
import re
import subprocess


def clone_branch(repo_url, branch):
    """Clone a repo directly on the specified branch."""
    cmd = ["git", "clone", "--branch", branch, repo_url]
    subprocess.run(cmd, check=True)


def max_infolettre(folder="infolettre"):
    """Return the highest N among subfolders named infolettre_N."""
    max_num = 0
    for name in os.listdir(folder):
        match = re.fullmatch(r"infolettre_(\d+)", name)
        if match:
            num = int(match.group(1))
            max_num = max(max_num, num)
    return max_num
