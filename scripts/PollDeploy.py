"""Pull only successful main pushes; public PR jobs never execute on the VM."""

import fcntl
import json
import os
from pathlib import Path
import subprocess
import urllib.request


REPOSITORY = "calWoolgar/ubuntu-apps-health-api"


def is_successful_main_run(run, revision):
    return (
        run.get("head_sha") == revision
        and run.get("head_branch") == "main"
        and run.get("event") == "push"
        and run.get("path", "").split("@", 1)[0] == ".github/workflows/ci.yaml"
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
        and (run.get("head_repository") or {}).get("full_name") == REPOSITORY
    )


def deploy_latest(root):
    source = root / "source"
    if not (source / ".git").exists():
        subprocess.run([
            "git", "clone", "--quiet", "--depth", "1", "--single-branch",
            "--branch", "main", "--no-checkout",
            f"https://github.com/{REPOSITORY}.git", str(source),
        ], check=True, timeout=120)
    subprocess.run([
        "git", "-C", str(source), "fetch", "--quiet", "--depth", "1", "origin",
        "+refs/heads/main:refs/remotes/origin/main",
    ], check=True, timeout=120)
    revision = subprocess.check_output([
        "git", "-C", str(source), "rev-parse", "refs/remotes/origin/main",
    ], text=True).strip()
    current = root / "current" / ".deploy-revision"
    if current.exists() and current.read_text().strip() == revision:
        print(f"Already deployed: {revision}", flush=True)
        return

    url = (
        f"https://api.github.com/repos/{REPOSITORY}/actions/workflows/ci.yaml/runs"
        f"?event=push&branch=main&head_sha={revision}&per_page=1"
    )
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "ubuntu-apps-health-api-deployer",
    })
    with urllib.request.urlopen(request, timeout=20) as response:
        runs = json.load(response).get("workflow_runs", [])
    if not runs or not is_successful_main_run(runs[0], revision):
        print(f"Waiting for successful main push CI: {revision}", flush=True)
        return

    subprocess.run([
        "git", "-C", str(source), "checkout", "--quiet", "--detach", revision,
    ], check=True, timeout=30)
    subprocess.run([
        "bash", str(source / "scripts" / "Deploy.sh"), revision,
    ], cwd=source, env={**os.environ, "DEPLOY_ROOT": str(root)}, check=True)


def main():
    root = Path(os.environ.get("DEPLOY_ROOT", Path.home() / "apps/ubuntu-apps-health-api")).resolve()
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".deployment.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Another deployment check is already running.", flush=True)
            return
        deploy_latest(root)


if __name__ == "__main__":
    main()
