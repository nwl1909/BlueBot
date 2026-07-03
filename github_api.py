import requests

API = "https://api.github.com"


class GitHub:

    def __init__(self, owner, repo, token=None):

        self.owner = owner
        self.repo = repo

        self.headers = {
            "Accept": "application/vnd.github+json"
        }

        # Без токена GitHub API даёт всего 60 запросов/час на IP - этого
        # не хватает даже на пару запусков workflow, и бот начинает падать
        # с HTTP 403 (rate limit), из-за чего уведомления перестают
        # приходить. С токеном лимит поднимается до 5000/час.
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    # -------------------------------------

    def get(self, url):

        r = requests.get(
            url,
            headers=self.headers,
            timeout=30
        )

        r.raise_for_status()

        return r.json()

    # -------------------------------------

    def latest_commit(self, branch):

        url = (
            f"{API}/repos/"
            f"{self.owner}/"
            f"{self.repo}/"
            f"commits/{branch}"
        )

        return self.get(url)

    # -------------------------------------

    def commit(self, sha):

        url = (
            f"{API}/repos/"
            f"{self.owner}/"
            f"{self.repo}/"
            f"commits/{sha}"
        )

        return self.get(url)

    # -------------------------------------

    def compare(self, old_sha, new_sha):

        url = (
            f"{API}/repos/"
            f"{self.owner}/"
            f"{self.repo}/"
            f"compare/"
            f"{old_sha}...{new_sha}"
        )

        return self.get(url)

    # -------------------------------------

    def raw(self, path, ref):

        url = (
            "https://raw.githubusercontent.com/"
            f"{self.owner}/"
            f"{self.repo}/"
            f"{ref}/"
            f"{path}"
        )

        r = requests.get(
            url,
            headers=self.headers,
            timeout=30
        )

        r.raise_for_status()

        return r.text

    # -------------------------------------

    def commits_between(self, old_sha, new_sha):

        data = self.compare(
            old_sha,
            new_sha
        )

        commits = data.get(
            "commits",
            []
        )

        result = []

        for commit in commits:

            result.append(
                commit["sha"]
            )

        return result
