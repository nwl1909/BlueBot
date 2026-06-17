#!/usr/bin/env python3
"""
Monitor a remote git repository and send Telegram notifications when files change.
Sends the newly added lines from changed files.

Usage:
  - Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID as repository secrets and expose them to the workflow.
  - The script stores state in ./repos_state.json and clones repositories under ./repos/.

This file is intended to be run inside a GitHub Actions job (or locally). When used in Actions the workflow will commit repos_state.json back to the repo so the state persists.
"""
import os
import sys
import json
import re
import subprocess
import requests
from pathlib import Path

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT = os.environ.get("TELEGRAM_CHAT_ID")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
    print("Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID environment variables", file=sys.stderr)
    sys.exit(2)

STATE_FILE = Path("repos_state.json")
REPOS_DIR = Path("repos")
REPOS_DIR.mkdir(exist_ok=True)


def run(cmd, cwd=None, check=True):
    return subprocess.check_output(cmd, shell=True, text=True, cwd=cwd).strip()


def get_default_remote_branch(repo_dir):
    try:
        ref = run("git symbolic-ref refs/remotes/origin/HEAD", cwd=repo_dir)
        return ref.rsplit("/", 1)[-1]
    except Exception:
        for b in ("main", "master"):
            try:
                run(f"git rev-parse --verify origin/{b}", cwd=repo_dir)
                return b
            except Exception:
                continue
    return "HEAD"


def get_repo_name(url):
    name = url.rstrip("/").split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
    owner = url.rstrip("/").split("/")[-2]
    return owner, name


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def send_telegram(msg):
    """Send a single message to Telegram"""
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={
                "chat_id": TELEGRAM_CHAT,
                "text": msg,
                "parse_mode": "HTML"
            },
            timeout=10
        )
    except Exception as e:
        print("Failed to send Telegram message:", e, file=sys.stderr)


def ensure_repo_cloned(url, local_dir):
    # accept either Path or str
    local = Path(local_dir)
    if not local.exists():
        run(f"git clone {url} {local}")
    else:
        run("git fetch --all --prune", cwd=str(local))


def get_added_lines(old_commit, new_commit, file_path, cwd):
    """Extract newly added lines from git diff"""
    try:
        diff_output = run(f"git diff {old_commit} {new_commit} -- {file_path}", cwd=cwd)
        added_lines = []
        for line in diff_output.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                # Remove the leading '+' to get the actual line
                added_lines.append(line[1:].strip())
        return added_lines
    except Exception:
        return []


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/monitor_dota_repo.py <git_repo_url>", file=sys.stderr)
        sys.exit(2)

    repo_url = sys.argv[1]
    owner, repo = get_repo_name(repo_url)
    local_dir = REPOS_DIR / f"{owner}_{repo}"
    ensure_repo_cloned(repo_url, local_dir)

    branch = get_default_remote_branch(str(local_dir))
    remote_ref = f"origin/{branch}" if branch != "HEAD" else "origin/HEAD"

    new = run(f"git rev-parse {remote_ref}", cwd=str(local_dir))

    state = load_state()
    key = f"{owner}/{repo}"
    old = state.get(key)

    if not old:
        try:
            old = run(f"git rev-parse {new}^", cwd=str(local_dir))
        except Exception:
            old = new

    if old == new:
        print(f"No changes for {key}")
        return

    files_out = run(f"git diff --name-only {old} {new}", cwd=str(local_dir))
    files = files_out.splitlines() if files_out else []

    if not files:
        print(f"No file changes detected for {key}")
        return

    # Get newly added lines from all changed files
    all_added_lines = []
    for file_path in files:
        added_lines = get_added_lines(old, new, file_path, str(local_dir))
        all_added_lines.extend(added_lines)

    # Get the first newly added non-empty line
    first_new_line = ""
    for line in all_added_lines:
        if line and not line.startswith('@@'):
            first_new_line = line
            break

    # Build the message
    msg_lines = [
        first_new_line if first_new_line else f"Обновлено {len(files)} файлов",
        "━━━━━━━━━━━━━━━━",
        "💙 <i>Я люблю тебя Блю</i>"
    ]
    
    msg = "\n".join(msg_lines)
    
    send_telegram(msg)
    print("Sent message:")
    print(msg)

    state[key] = new
    save_state(state)


if __name__ == "__main__":
    main()
