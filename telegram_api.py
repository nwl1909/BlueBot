import requests


class Telegram:

    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

    def send(self, text):

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"

        requests.post(
            url,
            json={
                "chat_id": self.chat_id,
                "text": text,
                "disable_web_page_preview": True
            },
            timeout=30
        )
