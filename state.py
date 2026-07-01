import json
from github_api import GitHub

STATE_FILE = "state.json"
STATE_BRANCH = "bot-state"


def load_state_local():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"last_commit": ""}


def save_state_local(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)


# -----------------------------
# GitHub storage (ВАЖНО)
# -----------------------------

def load_state_remote(github: GitHub):
    try:
        raw = github.raw("state.json", STATE_BRANCH)
        return json.loads(raw)
    except:
        return {"last_commit": ""}


def save_state_remote(github: GitHub, state: dict):
    """
    Требует GitHub push (через workflow)
    Здесь только подготовка файла.
    """
    save_state_local(state)
    return state
