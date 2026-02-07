from __future__ import annotations

from typing import Iterable, Mapping
from urllib.parse import urlencode

DEFAULT_CHARTS: tuple[str, ...] = ("stats", "top_languages")


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


def _stringify_param(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _merge_params(
    base: Mapping[str, object],
    extra: Mapping[str, object] | None,
    reserved: Iterable[str] | None = None,
) -> dict[str, object]:
    params = dict(base)
    reserved_set = set(reserved or [])
    if isinstance(extra, Mapping):
        for key, value in extra.items():
            if key in reserved_set or value is None:
                continue
            params[key] = value
    return params


def _build_url(base_url: str, params: Mapping[str, object]) -> str:
    encoded = urlencode({key: _stringify_param(value) for key, value in params.items()})
    return f"{base_url}?{encoded}"


def build_stats_chart(
    username: str,
    config: Mapping[str, object] | None = None,
    *,
    theme: str | None = None,
    hide_border: bool = True,
) -> str:
    cfg = config or {}
    params: dict[str, object] = {
        "username": username,
        "show_icons": True,
        "hide_border": hide_border,
    }
    if theme:
        params["theme"] = theme
    params = _merge_params(params, cfg, reserved=("alt",))
    url = _build_url("https://github-readme-stats.vercel.app/api", params)
    alt = str(cfg.get("alt") or "GitHub stats")
    return f"![{alt}]({url})"


def build_top_languages_chart(
    username: str,
    config: Mapping[str, object] | None = None,
    *,
    theme: str | None = None,
    hide_border: bool = True,
) -> str:
    cfg = config or {}
    layout = cfg.get("layout", "compact")
    langs_count = cfg.get("langs_count", 8)
    params: dict[str, object] = {
        "username": username,
        "hide_border": hide_border,
    }
    if layout:
        params["layout"] = layout
    if langs_count is not None:
        params["langs_count"] = langs_count
    if theme:
        params["theme"] = theme
    params = _merge_params(params, cfg, reserved=("alt",))
    url = _build_url("https://github-readme-stats.vercel.app/api/top-langs", params)
    alt = str(cfg.get("alt") or "Top languages")
    return f"![{alt}]({url})"


def build_streak_chart(
    username: str,
    config: Mapping[str, object] | None = None,
    *,
    theme: str | None = None,
    hide_border: bool = True,
) -> str:
    cfg = config or {}
    params: dict[str, object] = {
        "user": username,
        "hide_border": hide_border,
    }
    if theme:
        params["theme"] = theme
    params = _merge_params(params, cfg, reserved=("alt",))
    url = _build_url("https://streak-stats.demolab.com", params)
    alt = str(cfg.get("alt") or "GitHub streak")
    return f"![{alt}]({url})"


def build_charts(profile_data: Mapping[str, object], config: Mapping[str, object] | None = None) -> str:
    cfg = config or {}
    username = profile_data.get("username")
    if not username:
        return ""
    enabled = _normalize_list(cfg.get("charts"), DEFAULT_CHARTS)
    joiner = str(cfg.get("joiner") or "\n")
    theme = cfg.get("theme")
    hide_border = bool(cfg.get("hide_border", True))

    parts: list[str] = []
    for chart in enabled:
        if chart == "stats":
            parts.append(
                build_stats_chart(
                    str(username),
                    cfg.get("stats") if isinstance(cfg.get("stats"), dict) else None,
                    theme=theme,
                    hide_border=hide_border,
                )
            )
        elif chart == "top_languages":
            parts.append(
                build_top_languages_chart(
                    str(username),
                    cfg.get("top_languages") if isinstance(cfg.get("top_languages"), dict) else None,
                    theme=theme,
                    hide_border=hide_border,
                )
            )
        elif chart == "streak":
            parts.append(
                build_streak_chart(
                    str(username),
                    cfg.get("streak") if isinstance(cfg.get("streak"), dict) else None,
                    theme=theme,
                    hide_border=hide_border,
                )
            )

    return joiner.join([part for part in parts if part])
