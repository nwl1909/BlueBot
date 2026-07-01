import json
import re
from pathlib import Path


# ----------------------------------------
# Версия
# ----------------------------------------

VERSION_KEYS = (
    "version",
    "build",
    "buildid",
    "client_version",
    "patch",
    "revision",
    "value"
)


def _find_in_object(obj):

    if isinstance(obj, dict):

        for key, value in obj.items():

            if key.lower() in VERSION_KEYS:

                if isinstance(value, int):
                    return value

                if isinstance(value, str):

                    if value.isdigit():
                        return int(value)

            result = _find_in_object(value)

            if result is not None:
                return result

    elif isinstance(obj, list):

        for value in obj:

            result = _find_in_object(value)

            if result is not None:
                return result

    return None


def parse_version(text):

    try:

        obj = json.loads(text)

        version = _find_in_object(obj)

        if version is not None:
            return version

    except:

        pass

    numbers = re.findall(r"\d+", text)

    if numbers:

        return int(numbers[-1])

    return None


# ----------------------------------------
# ID
# ----------------------------------------

def parse_appid(path):

    name = Path(path).stem

    digits = re.findall(r"\d+", name)

    if digits:

        return digits[0]

    return name


# ----------------------------------------
# Название
# ----------------------------------------

def parse_name(path):

    name = Path(path).stem

    return name.replace("_", " ").title()


# ----------------------------------------
# Telegram
# ----------------------------------------

def make_message(appid,
                 title,
                 old_version,
                 new_version,
                 time_string,
                 suffix):

    return (
        f"{appid} - {title} | "
        f"[v] {old_version} => {new_version} | "
        f"{time_string} (UTC+3)\n\n"
        f"{suffix}"
    )
