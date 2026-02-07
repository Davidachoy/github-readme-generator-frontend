from __future__ import annotations

from typing import Iterable, Mapping
from urllib.parse import quote_plus, urlencode

DEFAULT_BADGES: tuple[str, ...] = ("profile", "followers", "repos", "top_language")
DEFAULT_STYLE = "flat"


def _normalize_list(value: object, default: Iterable[str]) -> list[str]:
    if value is None:
        return list(default)
    if isinstance(value, str):
        items = [item.strip() for item in value.split(",")]
        return [item for item in items if item]
    if isinstance(value, dict):
        return [key for key, enabled in value.items() if enabled]
    if isinstance(value, (list, tuple, set)):
        return [item for item in value if item]
    return list(default)


def _shield_url(label: str, message: str, color: str, style: str, logo: str | None = None) -> str:
    base = f"https://img.shields.io/badge/{quote_plus(label)}-{quote_plus(message)}-{color}"
    params: dict[str, str] = {"style": style}
    if logo:
        params["logo"] = logo
    return f"{base}?{urlencode(params)}"


def _markdown_badge(alt: str, url: str, link: str | None = None) -> str:
    if link:
        return f"[![{alt}]({url})]({link})"
    return f"![{alt}]({url})"


def _extract_languages(profile_data: Mapping[str, object]) -> list[tuple[str, float]]:
    languages = profile_data.get("top_languages") or []
    results: list[tuple[str, float]] = []
    for item in languages:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            name, value = item
        elif isinstance(item, dict):
            name = item.get("name") or item.get("language")
            value = item.get("bytes") or item.get("count") or item.get("value")
        else:
            continue
        if name is None:
            continue
        try:
            count = float(value)
        except (TypeError, ValueError):
            count = 0.0
        results.append((str(name), count))
    return results


def _language_badge_list(profile_data: Mapping[str, object], config: Mapping[str, object]) -> list[str]:
    languages = _extract_languages(profile_data)
    if not languages:
        return []
    try:
        max_languages = int(config.get("max_languages", 5) or 0)
    except (TypeError, ValueError):
        max_languages = 0
    if max_languages <= 0:
        return []
    try:
        min_percent = float(config.get("min_percent", 0) or 0)
    except (TypeError, ValueError):
        min_percent = 0.0
    total = sum(count for _, count in languages)
    if total <= 0:
        return []
    color = str(config.get("color") or config.get("language_color") or "blue")
    style = str(config.get("style") or DEFAULT_STYLE)
    badges: list[str] = []
    for name, count in languages[:max_languages]:
        percent = round((count / total) * 100)
        if percent < min_percent:
            continue
        url = _shield_url(str(name), f"{percent}%", color, style)
        badges.append(_markdown_badge(str(name), url))
    return badges


def build_language_badges(profile_data: Mapping[str, object], config: Mapping[str, object] | None = None) -> str:
    cfg = config or {}
    joiner = str(cfg.get("joiner") or " ")
    return joiner.join(_language_badge_list(profile_data, cfg))


def build_badges(profile_data: Mapping[str, object], config: Mapping[str, object] | None = None) -> str:
    cfg = config or {}
    style = str(cfg.get("style") or DEFAULT_STYLE)
    joiner = str(cfg.get("joiner") or " ")
    enabled = _normalize_list(cfg.get("badges"), DEFAULT_BADGES)
    colors = cfg.get("colors") if isinstance(cfg.get("colors"), dict) else {}
    username = profile_data.get("username")

    badges: list[str] = []
    for badge in enabled:
        if badge == "profile":
            if username:
                color = str(colors.get("profile") or "181717")
                url = _shield_url("GitHub", str(username), color, style, logo="github")
                link = f"https://github.com/{username}"
                badges.append(_markdown_badge("GitHub profile", url, link=link))
        elif badge == "followers":
            followers = profile_data.get("followers")
            if followers is not None:
                color = str(colors.get("followers") or "blue")
                url = _shield_url("Followers", str(followers), color, style)
                badges.append(_markdown_badge("Followers", url))
        elif badge == "repos":
            repos = profile_data.get("public_repos")
            if repos is not None:
                color = str(colors.get("repos") or "informational")
                url = _shield_url("Repos", str(repos), color, style)
                badges.append(_markdown_badge("Public repos", url))
        elif badge == "top_language":
            languages = _extract_languages(profile_data)
            if languages:
                total = sum(count for _, count in languages)
                name, count = languages[0]
                if total > 0:
                    percent = round((count / total) * 100)
                    message = f"{name} {percent}%"
                else:
                    message = str(name)
                color = str(colors.get("top_language") or "orange")
                url = _shield_url("Top language", message, color, style)
                badges.append(_markdown_badge("Top language", url))
        elif badge == "languages":
            language_cfg = (
                dict(cfg.get("language_badges", {}))
                if isinstance(cfg.get("language_badges"), dict)
                else {}
            )
            language_cfg.setdefault("style", style)
            language_cfg.setdefault("joiner", joiner)
            language_cfg.setdefault("color", colors.get("languages") or "blue")
            badges.extend(_language_badge_list(profile_data, language_cfg))

    return joiner.join(badges)
