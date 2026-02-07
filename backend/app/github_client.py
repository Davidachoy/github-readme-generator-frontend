import asyncio
import os
from typing import Dict, List, Optional

import httpx
from fastapi import HTTPException

GITHUB_API = "https://api.github.com"
REQUEST_TIMEOUT = httpx.Timeout(20.0, connect=10.0)
MAX_REPOS = int(os.getenv("GITHUB_MAX_REPOS", "100"))
LANGUAGE_REPO_LIMIT = int(os.getenv("GITHUB_LANGUAGE_REPO_LIMIT", "30"))
REPO_RESULT_LIMIT = int(os.getenv("GITHUB_REPO_RESULT_LIMIT", "12"))


def _headers() -> Dict[str, str]:
    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "readme-generator",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def _get_json(
    client: httpx.AsyncClient,
    url: str,
    params: Optional[Dict[str, object]] = None,
):
    try:
        response = await client.get(url, params=params)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"GitHub API request failed: {exc}",
        ) from exc

    if response.status_code >= 400:
        detail = None
        try:
            detail = response.json().get("message")
        except ValueError:
            detail = response.text

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="GitHub user not found")
        raise HTTPException(status_code=response.status_code, detail=detail or "GitHub API error")

    return response.json()


async def _fetch_repos(client: httpx.AsyncClient, username: str) -> List[dict]:
    repos: List[dict] = []
    page = 1

    while len(repos) < MAX_REPOS:
        per_page = min(100, MAX_REPOS - len(repos))
        params = {
            "per_page": per_page,
            "page": page,
            "sort": "updated",
            "direction": "desc",
            "type": "owner",
        }
        batch = await _get_json(client, f"{GITHUB_API}/users/{username}/repos", params=params)
        if not isinstance(batch, list) or not batch:
            break
        repos.extend(batch)
        if len(batch) < per_page:
            break
        page += 1

    return repos


async def _fetch_languages(client: httpx.AsyncClient, repos: List[dict]) -> Dict[str, int]:
    lang_totals: Dict[str, int] = {}
    if not repos:
        return lang_totals

    semaphore = asyncio.Semaphore(5)

    async def fetch_repo_langs(repo: dict) -> Dict[str, int]:
        url = repo.get("languages_url")
        if not url:
            return {}
        async with semaphore:
            try:
                response = await client.get(url)
            except httpx.HTTPError:
                return {}
        if response.status_code >= 400:
            return {}
        try:
            data = response.json()
        except ValueError:
            return {}
        return data if isinstance(data, dict) else {}

    tasks = [fetch_repo_langs(repo) for repo in repos]
    for lang_map in await asyncio.gather(*tasks):
        for language, amount in lang_map.items():
            if isinstance(amount, int):
                lang_totals[language] = lang_totals.get(language, 0) + amount

    return lang_totals


def _build_language_list(lang_totals: Dict[str, int]) -> List[dict]:
    total_bytes = sum(lang_totals.values())
    languages: List[dict] = []
    for name, bytes_count in lang_totals.items():
        percentage = 0.0
        if total_bytes > 0:
            percentage = round((bytes_count / total_bytes) * 100, 2)
        languages.append({"name": name, "bytes": bytes_count, "percentage": percentage})
    languages.sort(key=lambda item: item["bytes"], reverse=True)
    return languages


def _format_repo(repo: dict) -> dict:
    return {
        "name": repo.get("name"),
        "url": repo.get("html_url"),
        "description": repo.get("description"),
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "language": repo.get("language"),
        "updated_at": repo.get("pushed_at") or repo.get("updated_at"),
        "is_fork": repo.get("fork", False),
    }


async def fetch_profile_data(username: str) -> dict:
    async with httpx.AsyncClient(headers=_headers(), timeout=REQUEST_TIMEOUT) as client:
        user = await _get_json(client, f"{GITHUB_API}/users/{username}")
        repos = await _fetch_repos(client, username)

        owned_repos = [repo for repo in repos if not repo.get("fork")]
        if not owned_repos:
            owned_repos = repos

        repos_for_languages = owned_repos[:LANGUAGE_REPO_LIMIT]
        lang_totals = await _fetch_languages(client, repos_for_languages)
        languages = _build_language_list(lang_totals)

        repos_payload = [_format_repo(repo) for repo in owned_repos[:REPO_RESULT_LIMIT]]
        top_languages = languages[:10]

        stats = {
            "followers": user.get("followers"),
            "following": user.get("following"),
            "public_repos": user.get("public_repos"),
            "public_gists": user.get("public_gists"),
            "total_stars": sum(repo.get("stargazers_count", 0) for repo in owned_repos),
            "total_forks": sum(repo.get("forks_count", 0) for repo in owned_repos),
            "total_open_issues": sum(repo.get("open_issues_count", 0) for repo in owned_repos),
        }

        return {
            "username": user.get("login", username),
            "name": user.get("name"),
            "bio": user.get("bio"),
            "avatar_url": user.get("avatar_url"),
            "profile_url": user.get("html_url"),
            "stats": stats,
            "languages": languages,
            "top_languages": top_languages,
            "repos": repos_payload,
        }
