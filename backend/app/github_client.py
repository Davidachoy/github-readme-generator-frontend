import os
import httpx

GITHUB_API = "https://api.github.com"

def _headers():
    token = os.getenv("GITHUB_TOKEN")
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

async def fetch_profile_data(username: str) -> dict:
    async with httpx.AsyncClient(headers=_headers(), timeout=20) as client:
        user = (await client.get(f"{GITHUB_API}/users/{username}")).json()
        repos = (await client.get(f"{GITHUB_API}/users/{username}/repos?per_page=100&sort=updated")).json()

        lang_totals = {}
        for r in repos[:30]:  # límite para no explotar rate limit
            langs = (await client.get(r["languages_url"])).json()
            for k, v in langs.items():
                lang_totals[k] = lang_totals.get(k, 0) + v

        return {
            "username": username,
            "name": user.get("name"),
            "bio": user.get("bio"),
            "followers": user.get("followers"),
            "public_repos": user.get("public_repos"),
            "top_languages": sorted(lang_totals.items(), key=lambda x: x[1], reverse=True)[:10],
            "repos": [
                {
                    "name": r["name"],
                    "url": r["html_url"],
                    "description": r.get("description"),
                    "stars": r.get("stargazers_count"),
                    "forks": r.get("forks_count"),
                    "language": r.get("language"),
                }
                for r in repos[:12]
            ],
        }
