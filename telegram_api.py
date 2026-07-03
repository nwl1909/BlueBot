import requests


class Telegram:

    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

    def send(self, text):

        if not self.token or not self.chat_id:
            raise RuntimeError(
                "TELEGRAM_TOKEN / TELEGRAM_CHAT_ID не заданы "
                "(проверьте секреты репозитория в Settings -> Secrets -> Actions)"
            )

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"

        r = requests.post(
            url,
            json={
                "chat_id": self.chat_id,
                "text": text,
                "disable_web_page_preview": True
            },
            timeout=30
        )

        if not r.ok or not r.json().get("ok", False):
            raise RuntimeError(f"Telegram API error: {r.status_code} {r.text}")
