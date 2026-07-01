import json
import re
from datetime import datetime, timedelta, timezone

from telegram_api import Telegram
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

Telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID).send("✅ Тест ЖОПЫ ГОЛУБИНА")

from config import (
    OWNER,
    REPO,
    TRACK_FOLDER,
    BRANCH,
    TELEGRAM_CHAT_ID,
    TELEGRAM_TOKEN,
    STATE_FILE,
)

from github_api import GitHub
from telegram_api import Telegram


github = GitHub(OWNER, REPO)
telegram = Telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)


# --------------------------------------------------------
# State
# --------------------------------------------------------

def load_state():

    try:

        with open(STATE_FILE, "r", encoding="utf8") as f:

            return json.load(f)

    except:

        return {
            "last_commit": ""
        }


def save_state(state):

    with open(STATE_FILE, "w", encoding="utf8") as f:

        json.dump(
            state,
            f,
            indent=4
        )


# --------------------------------------------------------
# Version Parser
# --------------------------------------------------------

VERSION_PATTERNS = [

    r'"version"\s*:\s*([0-9]+)',

    r'"build"\s*:\s*([0-9]+)',

    r'"client_version"\s*:\s*([0-9]+)',

    r'"patch"\s*:\s*([0-9]+)',

    r'"revision"\s*:\s*([0-9]+)',

    r'"value"\s*:\s*([0-9]+)'
]


def find_version(text):

    for pattern in VERSION_PATTERNS:

        m = re.search(pattern, text)

        if m:

            return int(m.group(1))

    numbers = re.findall(r"\d+", text)

    if len(numbers):

        return int(numbers[-1])

    return None


# --------------------------------------------------------
# UTC+3
# --------------------------------------------------------

def format_time(timestr):

    utc = datetime.strptime(
        timestr,
        "%Y-%m-%dT%H:%M:%SZ"
    )

    utc = utc.replace(
        tzinfo=timezone.utc
    )

    moscow = utc.astimezone(
        timezone(
            timedelta(hours=3)
        )
    )

    return moscow.strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# --------------------------------------------------------
# Message
# --------------------------------------------------------

def make_message(file_name, old, new, date):

    stem = file_name.split("/")[-1]

    stem = stem.replace(".json", "")

    return (
        f"{stem} - Dota 2 Server | [v] {old} => {new} | {date} (UTC+3)\n"
        "\n"
        "💙 Я люблю тебя Блю"
    )


# --------------------------------------------------------
# Main
# --------------------------------------------------------

state = load_state()

latest = github.latest_commit(BRANCH)

latest_sha = latest["sha"]


if state["last_commit"] == latest_sha:

    print("No updates.")

    quit()


commit = github.commit(latest_sha)

files = commit["files"]


for file in files:

    path = file["filename"]

    if not path.startswith(TRACK_FOLDER):

        continue

    previous_sha = commit["parents"][0]["sha"]

    try:

        old_text = github.raw(
            path,
            previous_sha
        )

        new_text = github.raw(
            path,
            latest_sha
        )

    except Exception as e:

        print(e)

        continue

    old_version = find_version(old_text)

    new_version = find_version(new_text)

    if old_version is None:

        continue

    if new_version is None:

        continue

    if old_version == new_version:

        continue

    msg = make_message(

        path,

        old_version,

        new_version,

        format_time(
            commit["commit"]["author"]["date"]
        )

    )

    telegram.send(msg)

    print(msg)

state["last_commit"] = latest_sha

save_state(state)

print("Done.")
