import os
import re
import subprocess
import requests


TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT = os.environ["TELEGRAM_CHAT_ID"]


def run(cmd):
    return subprocess.check_output(
        cmd,
        shell=True,
        text=True
    ).strip()


old = run("git rev-parse HEAD^")
new = run("git rev-parse HEAD")


files = run(
    f"git diff --name-only {old} {new}"
).splitlines()


changes = []


def get_version(text):

    # ищет числа типа 6803, 6804
    found = re.findall(
        r"\b\d{4}\b",
        text
    )

    return found[0] if found else "?"


for file in files:

    try:
        old_file = run(
            f"git show {old}:{file}"
        )

        new_file = run(
            f"git show {new}:{file}"
        )


        old_ver = get_version(old_file)
        new_ver = get_version(new_file)


        changes.append(
            f"{file}: {old_ver} => {new_ver}"
        )

    except:
        changes.append(
            f"{file}: changed"
        )


if not changes:
    exit()


versions = []

for c in changes:
    m = re.findall(
        r"(\d{4}) => (\d{4})",
        c
    )

    if m:
        versions.append(m[0])


if versions:
    main_old = versions[0][0]
    main_new = versions[0][1]
else:
    main_old = "?"
    main_new = "?"


msg = (
    f"Dota 2 {main_old} => {main_new}\n"
    f"Files changed: {len(files)}\n\n"
    + "\n".join(changes)
    +
    "\n\nЯ люблю тебя Блю"
)


requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    data={
        "chat_id": CHAT,
        "text": msg
    }
)
