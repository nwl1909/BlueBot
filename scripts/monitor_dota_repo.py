#!/usr/bin/env python3
"""
Monitor a remote git repository and send Telegram notifications when files change.
Sends a beautiful combined message with all file updates.

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


def get_version(text):
    found = re.findall(r"\b\d{4}\b", text)
    return found[0] if found else "?"


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


def get_file_emoji(filename):
    """Return appropriate emoji based on file type"""
    if filename.endswith('.json'):
        return '📄'
    elif filename.endswith('.txt'):
        return '📝'
    elif filename.endswith('.py'):
        return '🐍'
    elif filename.endswith('.yml') or filename.endswith('.yaml'):
        return '⚙️'
    elif 'HISTORY' in filename.upper():
        return '📜'
    else:
        return '📦'


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

    # Collect all changes
    changes = []
    for fpath in files:
        try:
            old_file = run(f"git show {old}:{fpath}", cwd=str(local_dir))
            new_file = run(f"git show {new}:{fpath}", cwd=str(local_dir))
            old_ver = get_version(old_file)
            new_ver = get_version(new_file)
            changes.append({
                'path': fpath,
                'old_ver': old_ver,
                'new_ver': new_ver,
                'status': 'updated'
            })
        except Exception:
            changes.append({
                'path': fpath,
                'old_ver': '?',
                'new_ver': '?',
                'status': 'changed'
            })

    # Find the main version (from first file with version pair)
    main_old = "?"
    main_new = "?"
    title_name = "Dota 2"

    for idx, change in enumerate(changes):
        if change['old_ver'] != '?' and change['new_ver'] != '?':
            main_old, main_new = change['old_ver'], change['new_ver']
            title_name = Path(files[idx]).stem
            break

    # Build the single beautiful message
    msg_lines = [
        f"🎮 <b>{title_name}</b>",
        f"<b>Версия: {main_old} → {main_new}</b>",
        f"<b>Файлов изменено: {len(files)}</b>",
        "━━━━━━━━━━━━━━━━",
        f"💙 <i>Я люблю тебя Блю</i>"
    ]
    
    msg = "\n".join(msg_lines)
    
    send_telegram(msg)
    print("Sent message:")
    print(msg)

    state[key] = new
    save_state(state)


if __name__ == "__main__":
    main()
