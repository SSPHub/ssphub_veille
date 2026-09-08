import subprocess


def clone_branch(repo_url, branch):
    """Clone a repo directly on the specified branch."""
    cmd = ["git", "clone", "--branch", branch, "--depth", "1", repo_url]
    subprocess.run(cmd, cwd="../", check=True)


def list_remote_branches(repo_url):
    """List branch names of a remote repo without cloning."""
    result = subprocess.run(
        ["git", "ls-remote", "--heads", repo_url],
        check=True,
        capture_output=True,
        text=True,
    )
    branches = []
    for line in result.stdout.splitlines():
        # Each line looks like: <commit-hash>\trefs/heads/<branch-name>
        ref = line.split("\t")[1]
        branches.append(ref.removeprefix("refs/heads/"))
    return branches


def extract_branch_infolettre(branch_list):
    return [branch for branch in branch_list if branch.startswith("infolettre")]


def max_infolettre(branch_list):
    """Return the highest NN among branch_list infolettre_NN."""
    max_num = 0
    max_branch = ""
    for branch in branch_list:
        num = int(branch[-2:])
        max_num = max(max_num, num)
        max_branch = branch
    return max_num, max_branch


def add_commit(file, repo, infolettre_branch):
    message = f"Add veille to {infolettre_branch}"
    subprocess.run(["git", "add", file], cwd=f"../{repo}", check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=f"../{repo}", check=True)
