import difflib
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone

from config import (
    OWNER,
    REPO,
    TRACK_FOLDER,
    HISTORY_FILES,
    BRANCH,
    TELEGRAM_CHAT_ID,
    TELEGRAM_TOKEN,
    STATE_FILE,
    GITHUB_TOKEN,
    MESSAGE_SUFFIX,
    BLOCKED_KEYWORDS,
)

from github_api import GitHub
from telegram_api import Telegram
from parser import parse_appid, parse_name, parse_emoji


github = GitHub(OWNER, REPO, GITHUB_TOKEN)
telegram = Telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)


# --------------------------------------------------------
# State
# --------------------------------------------------------

def load_state():

    try:

        with open(STATE_FILE, "r", encoding="utf8") as f:

            return json.load(f)

    except Exception:

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
# Новые строки в файлах истории (_HISTORY_by_date.txt)
# --------------------------------------------------------

def added_lines(old_text, new_text):

    old_lines = [line for line in old_text.splitlines() if line.strip()]
    new_lines = [line for line in new_text.splitlines() if line.strip()]

    # difflib находит именно ДОБАВЛЕННЫЕ строки, а не просто "всё после
    # старой длины" - так это работает даже если строка была вставлена не
    # строго в конец файла.
    matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines)

    result = []

    for tag, _i1, _i2, j1, j2 in matcher.get_opcodes():
        if tag in ("insert", "replace"):
            result.extend(new_lines[j1:j2])

    return result


def make_history_message(line):

    return f"{line}\n\n{MESSAGE_SUFFIX}"



# --------------------------------------------------------
# Стоп-слова: такие уведомления не отправляем вовсе
# --------------------------------------------------------

def is_blocked(text):

    lowered = text.lower()

    for keyword in BLOCKED_KEYWORDS:
        if keyword.lower() in lowered:
            return True

    return False


def make_message(file_name, old, new, date):

    appid = parse_appid(file_name)
    name = parse_name(appid)
    emoji = parse_emoji(appid)

    header = f"{emoji} {appid} - {name}" if emoji else f"{appid} - {name}"

    return (
        f"{header} | [v] {old} => {new} | {date} (UTC+3)\n"
        "\n"
        "💙 Я люблю тебя Блю"
    )


# --------------------------------------------------------
# Should we even look at this file?
# --------------------------------------------------------

def is_tracked(path):

    # Файл должен лежать непосредственно в TRACK_FOLDER (а не в папке с
    # похожим именем вроде "steam_apiary/...").
    if path != TRACK_FOLDER and not path.startswith(TRACK_FOLDER + "/"):
        return False

    # Интересуют только json-файлы конкретных приложений, служебные файлы
    # вроде _HISTORY_by_date.txt пропускаем - в них нет ключа версии, и без
    # этой проверки find_version() хватал бы случайное число из текста.
    if not path.endswith(".json"):
        return False

    return True


# --------------------------------------------------------
# Main
# --------------------------------------------------------

def main():

    state = load_state()

    latest = github.latest_commit(BRANCH)
    latest_sha = latest["sha"]

    if state.get("last_commit") == latest_sha:
        print("No updates.")
        return

    old_sha = state.get("last_commit") or ""

    if not old_sha:
        parents = latest.get("parents") or []
        old_sha = parents[0]["sha"] if parents else latest_sha

    compare = github.compare(old_sha, latest_sha)

    commits = compare.get("commits", [])

    print(f"Found commits: {len(commits)}")

    for commit in commits:

        sha = commit["sha"]

        commit_data = github.commit(sha)

        files = commit_data.get("files", [])

        parents = commit.get("parents") or []

        if not parents:
            print(f"Skipping {sha}: no parent commit")
            continue

        parent_sha = parents[0]["sha"]

        for file in files:

            path = file["filename"]

            if path in HISTORY_FILES:

                try:
                    # Файла могло не быть в родительском коммите (например,
                    # это самый первый коммит с ним) - тогда считаем, что
                    # "было" пусто.
                    old_text = github.raw(path, parent_sha)
                except Exception:
                    old_text = ""

                try:
                    new_text = github.raw(path, sha)
                except Exception as e:
                    print("RAW ERROR:", e)
                    continue

                for line in added_lines(old_text, new_text):

                    msg = make_history_message(line)

                    if is_blocked(msg):
                        print(f"Пропущено (стоп-слово): {line}")
                        continue

                    try:
                        telegram.send(msg)
                        print(msg)
                    except Exception as e:
                        print("TELEGRAM ERROR:", e)

                    # Небольшая пауза между сообщениями, чтобы не словить
                    # flood control от Telegram, если строк добавилось
                    # сразу несколько.
                    time.sleep(1)

                continue

            if not is_tracked(path):
                continue

            try:
                old_text = github.raw(path, parent_sha)
                new_text = github.raw(path, sha)

            except Exception as e:
                print("RAW ERROR:", e)
                continue

            old_version = find_version(old_text)
            new_version = find_version(new_text)

            if old_version is None or new_version is None:
                continue

            if old_version == new_version:
                continue

            msg = make_message(
                path,
                old_version,
                new_version,
                format_time(commit["commit"]["author"]["date"])
            )

            if is_blocked(msg):
                print(f"Пропущено (стоп-слово): {path}")
                continue

            try:
                telegram.send(msg)
                print(msg)
            except Exception as e:
                print("TELEGRAM ERROR:", e)

    state["last_commit"] = latest_sha
    save_state(state)

    print("Done.")


if __name__ == "__main__":

    try:
        main()
    except Exception as e:
        # Явно завершаем с ошибкой, чтобы GitHub Actions пометил запуск
        # как failed и это было видно во вкладке Actions, а не терялось
        # молча (раньше при любой ошибке state.json просто не обновлялся,
        # без внятного сообщения о причине).
        print(f"::error::Bot crashed: {e}", file=sys.stderr)
        sys.exit(1)
