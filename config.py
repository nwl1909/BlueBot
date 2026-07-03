import os

OWNER = "muk-as"

REPO = "DOTA2_WEB"

BRANCH = "master"

# В репозитории muk-as/DOTA2_WEB папка steam_api лежит в КОРНЕ репозитория,
# а не внутри dota2_web/. Из-за неверного пути ни один файл никогда не
# проходил проверку path.startswith(TRACK_FOLDER), и бот не отправлял
# ни одного уведомления.
TRACK_FOLDER = "steam_api"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Токен GitHub Actions (secrets.GITHUB_TOKEN), нужен чтобы поднять лимит
# запросов к GitHub API с 60/час до 5000/час и избежать падений бота
# из-за 403 rate limit при частых запусках.
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

STATE_FILE = "state.json"

STATE_BRANCH = "bot-state"

STATE_NAME = "state.json"

MESSAGE_SUFFIX = "💙 Я люблю тебя Блю"
