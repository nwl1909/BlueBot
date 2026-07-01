import json
import re
from pathlib import Path


# ----------------------------------------
# Загрузка базы приложений
# ----------------------------------------

try:
    with open("apps.json", "r", encoding="utf-8") as f:
        APPS = json.load(f)
except Exception:
    APPS = {}


# ----------------------------------------
# Возможные ключи версии
# ----------------------------------------

VERSION_KEYS = {
    "version",
    "build",
    "buildid",
    "client_version",
    "patch",
    "revision",
    "value"
}


# ----------------------------------------
# Рекурсивный поиск версии
# ----------------------------------------

def _find_version(obj):

    if isinstance(obj, dict):

        for key, value in obj.items():

            if key.lower() in VERSION_KEYS:

                if isinstance(value, int):
                    return value

                if isinstance(value, str):

                    if value.isdigit():
                        return int(value)

            result = _find_version(value)

            if result is not None:
                return result

    elif isinstance(obj, list):

        for item in obj:

            result = _find_version(item)

            if result is not None:
                return result

    return None


# ----------------------------------------
# Получить версию файла
# ----------------------------------------

def parse_version(text):

    # Попытка распарсить JSON

    try:

        data = json.loads(text)

        version = _find_version(data)

        if version is not None:
            return version

    except Exception:
        pass

    # Поиск по шаблонам

    patterns = [

        r'"version"\s*:\s*([0-9]+)',
        r'"build"\s*:\s*([0-9]+)',
        r'"buildid"\s*:\s*([0-9]+)',
        r'"client_version"\s*:\s*([0-9]+)',
        r'"patch"\s*:\s*([0-9]+)',
        r'"revision"\s*:\s*([0-9]+)',
        r'"value"\s*:\s*([0-9]+)'

    ]

    for pattern in patterns:

        m = re.search(pattern, text, re.IGNORECASE)

        if m:
            return int(m.group(1))

    # Последнее число в файле

    numbers = re.findall(r"\d+", text)

    if numbers:
        return int(numbers[-1])

    return None


# ----------------------------------------
# Получить AppID
# ----------------------------------------

def parse_appid(path):

    filename = Path(path).stem

    match = re.search(r"\d+", filename)

    if match:
        return match.group(0)

    return filename


# ----------------------------------------
# Название приложения
# ----------------------------------------

def parse_name(appid):

    info = APPS.get(str(appid))

    if info is None:
        return "Unknown App"

    if isinstance(info, dict):
        return info.get("name", "Unknown App")

    return str(info)


# ----------------------------------------
# Эмодзи приложения
# ----------------------------------------

def parse_emoji(appid):

    info = APPS.get(str(appid))

    if isinstance(info, dict):
        return info.get("emoji", "")

    return ""


# ----------------------------------------
# Тип приложения
# ----------------------------------------

def parse_type(appid):

    info = APPS.get(str(appid))

    if isinstance(info, dict):
        return info.get("type", "unknown")

    return "unknown"


# ----------------------------------------
# Формирование сообщения
# ----------------------------------------

def make_message(
    appid,
    old_version,
    new_version,
    date_string,
    suffix
):

    emoji = parse_emoji(appid)

    name = parse_name(appid)

    if emoji:
        header = f"{emoji} {appid} - {name}"
    else:
        header = f"{appid} - {name}"

    return (
        f"{header} | "
        f"[v] {old_version} => {new_version} | "
        f"{date_string} (UTC+3)\n\n"
        f"{suffix}"
    )
