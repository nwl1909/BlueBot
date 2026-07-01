import requests


class GitHub:

    def __init__(self, owner, repo):

        self.owner = owner
        self.repo = repo

    def request(self, url):

        return requests.get(
            url,
            headers={
                "Accept": "application/vnd.github+json"
            },
            timeout=30
        ).json()

    def latest_commit(self, branch):

        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/commits/{branch}"

        return self.request(url)

    def commit(self, sha):

        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/commits/{sha}"

        return self.request(url)

    def raw(self, path, ref):

        url = f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/{ref}/{path}"

        return requests.get(url, timeout=30).text
