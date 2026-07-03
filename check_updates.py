#!/usr/bin/env python3
"""
Отслеживает файл steam_api/_HISTORY_by_date.txt в репозитории muk-as/DOTA2_WEB
и шлёт новые строки (обновления версий) в Telegram-канал.

Состояние (сколько строк уже обработано) хранится в state.json рядом со скриптом.
Файл коммитится обратно в репозиторий шагом workflow после запуска скрипта.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

RAW_URL = "https://raw.githubusercontent.com/muk-as/DOTA2_WEB/master/steam_api/_HISTORY_by_date.txt"
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")
SIGNATURE = "💙 Я люблю тебя Блю"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def fetch_history_text() -> str:
    # cache-busting параметр, чтобы не словить закэшированную GitHub-версию файла
    url = f"{RAW_URL}?_={int(time.time())}"
    req = urllib.request.Request(url, headers={"Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8")


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_line_count": 0}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def send_telegram_message(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("::error::TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не заданы", file=sys.stderr)
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            if not body.get("ok"):
                print(f"::error::Telegram API вернул ошибку: {body}", file=sys.stderr)
                return False
            return True
    except urllib.error.HTTPError as e:
        print(f"::error::HTTP ошибка Telegram API: {e.code} {e.read().decode('utf-8', 'ignore')}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"::error::Не удалось отправить сообщение: {e}", file=sys.stderr)
        return False


def main() -> int:
    try:
        text = fetch_history_text()
    except Exception as e:
        print(f"::error::Не удалось скачать файл истории: {e}", file=sys.stderr)
        return 1

    lines = [line for line in text.splitlines() if line.strip()]
    state = load_state()
    last_count = state.get("last_line_count", 0)

    # Первый запуск: просто фиксируем текущее состояние, ничего не шлём,
    # чтобы не спамить всей историей версий разом.
    if last_count == 0 and not os.path.exists(STATE_FILE):
        state["last_line_count"] = len(lines)
        save_state(state)
        print(f"Первый запуск. Зафиксировано {len(lines)} строк, уведомления начнутся со следующих изменений.")
        return 0

    if len(lines) <= last_count:
        print("Новых обновлений нет.")
        return 0

    new_lines = lines[last_count:]
    print(f"Найдено новых строк: {len(new_lines)}")

    all_ok = True
    for line in new_lines:
        message = f"{line}\n{SIGNATURE}"
        ok = send_telegram_message(message)
        all_ok = all_ok and ok
        if ok:
            print(f"Отправлено: {line}")
        time.sleep(1)  # небольшая пауза между сообщениями

    # Сохраняем прогресс даже при частичном сбое отправки, чтобы не застрять в цикле повторов
    state["last_line_count"] = len(lines)
    save_state(state)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
