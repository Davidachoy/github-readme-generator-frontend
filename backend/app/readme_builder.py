from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    from app.badges import build_badges as _build_badges
except Exception:
    _build_badges = None

try:
    from app.charts import build_charts as _build_charts
except Exception:
    _build_charts = None

DEFAULT_SECTIONS = [
    "header",
    "badges",
    "bio",
    "stats",
    "languages",
    "repos",
    "charts",
]

SECTION_TITLES = {
    "badges": "Badges",
    "bio": "About",
    "stats": "Stats",
    "languages": "Top Languages",
    "repos": "Top Repositories",
    "charts": "Charts",
}

# Plantillas que definen secciones por defecto y títulos
TEMPLATES: Dict[str, Dict[str, Any]] = {
    "minimal": {
        "sections": ["header", "bio", "repos"],
        "titles": {"bio": "About", "repos": "Projects"},
    },
    "professional": {
        "sections": ["header", "badges", "bio", "stats", "languages", "repos", "charts"],
        "titles": {"badges": "Badges", "bio": "About", "stats": "Statistics", "languages": "Languages", "repos": "Repositories", "charts": "Activity"},
    },
    "creative": {
        "sections": ["header", "badges", "bio", "stats", "languages", "repos", "charts"],
        "titles": {"badges": "🔗 Links", "bio": "👋 About me", "stats": "📊 Stats", "languages": "💻 Languages", "repos": "⭐ Projects", "charts": "📈 Activity"},
    },
}


def build_readme(profile_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    config = config or {}
    # Aplicar plantilla si se especifica
    template_name = (config.get("template") or "").strip().lower()
    if template_name in TEMPLATES:
        t = TEMPLATES[template_name]
        config = dict(config)
        if "titles" not in config or not config["titles"]:
            config["titles"] = dict(t.get("titles") or {})
        else:
            config["titles"] = {**(t.get("titles") or {}), **config["titles"]}
    sections = _normalize_sections(config.get("sections"))
    if not sections:
        sections = list(TEMPLATES.get(template_name, {}).get("sections", DEFAULT_SECTIONS) if template_name else DEFAULT_SECTIONS)
        if not sections:
            sections = list(DEFAULT_SECTIONS)

    lines: List[str] = []
    assets: Dict[str, Any] = {}

    if "header" in sections:
        lines.extend(_section_header(profile_data, config))

    for section in sections:
        if section == "header":
            continue

        if section == "badges":
            body, new_assets = _section_badges(profile_data, config)
            assets = _merge_assets(assets, new_assets)
        elif section == "charts":
            body, new_assets = _section_charts(profile_data, config)
            assets = _merge_assets(assets, new_assets)
        elif section == "bio":
            body = _section_bio(profile_data)
        elif section == "stats":
            body = _section_stats(profile_data)
        elif section == "languages":
            body = _section_languages(profile_data, config)
        elif section == "repos":
            body = _section_repos(profile_data, config)
        else:
            body = []

        title = _section_title(section, config)
        _append_section(lines, title, body)

    markdown = "\n".join(lines).strip()
    if markdown:
        markdown += "\n"

    result: Dict[str, Any] = {"markdown": markdown}
    if assets:
        result["assets"] = assets
    return result


def _section_title(section: str, config: Dict[str, Any]) -> Optional[str]:
    titles = config.get("titles")
    if isinstance(titles, dict):
        custom = titles.get(section)
        if isinstance(custom, str) and custom.strip():
            return custom.strip()
    return SECTION_TITLES.get(section)


def _section_header(profile_data: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
    title = _build_title(profile_data)
    lines = [f"# {title}"]
    subtitle = config.get("subtitle") or config.get("tagline")
    if isinstance(subtitle, str) and subtitle.strip():
        lines.append(subtitle.strip())
    return lines


def _section_bio(profile_data: Dict[str, Any]) -> List[str]:
    bio = profile_data.get("bio")
    if not isinstance(bio, str) or not bio.strip():
        return []
    return _split_lines(bio.strip())


def _section_stats(profile_data: Dict[str, Any]) -> List[str]:
    items = []
    followers = profile_data.get("followers")
    public_repos = profile_data.get("public_repos")
    if followers is not None:
        items.append(f"- Followers: {followers}")
    if public_repos is not None:
        items.append(f"- Public repos: {public_repos}")
    return items


def _section_languages(profile_data: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
    langs_raw = profile_data.get("top_languages") or []
    normalized_all = []
    for item in langs_raw:
        parsed = _parse_language_item(item)
        if parsed:
            normalized_all.append(parsed)

    if not normalized_all:
        return []

    total_all = sum(value for _, value in normalized_all)

    max_langs = _coerce_int(config.get("max_languages") or config.get("language_count"))
    normalized = normalized_all
    if max_langs is not None and max_langs > 0:
        normalized = normalized[:max_langs]

    show_percent = config.get("show_language_percent", True)
    lines = []
    for name, value in normalized:
        if total_all > 0 and show_percent:
            percent = (value / total_all) * 100
            lines.append(f"- {name} - {percent:.1f}%")
        else:
            lines.append(f"- {name}")
    return lines


def _section_repos(profile_data: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
    repos = profile_data.get("repos") or []
    if not isinstance(repos, list):
        return []

    max_repos = _coerce_int(config.get("max_repos") or config.get("repo_count"))
    if max_repos is not None and max_repos > 0:
        repos = repos[:max_repos]

    layout = (config.get("layout") or "default").lower()
    show_stats = config.get("show_repo_stats")
    if show_stats is None:
        show_stats = layout not in ("compact", "compacto")

    if layout == "table":
        return _section_repos_table(repos, show_stats=bool(show_stats))
    lines = []
    for repo in repos:
        if not isinstance(repo, dict):
            continue
        formatted = _format_repo(repo, show_stats=bool(show_stats))
        if formatted:
            lines.append(f"- {formatted}")
    return lines


def _html_escape(s: str) -> str:
    """Escapa caracteres para uso seguro en HTML."""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _section_repos_table(repos: List[Dict[str, Any]], show_stats: bool = True) -> List[str]:
    """Repos en tabla HTML (GitHub la renderiza bien). Columnas: Repository, Description, Language."""
    if not repos:
        return []
    rows: List[List[str]] = []
    for repo in repos:
        if not isinstance(repo, dict):
            continue
        name = repo.get("name") or "repo"
        url = repo.get("url") or "#"
        cell_name = f'<a href="{_html_escape(url)}">{_html_escape(name)}</a>'
        desc = (repo.get("description") or "").strip()
        desc = _html_escape(desc) if desc else "—"
        if len(desc) > 60:
            desc = desc[:57] + "..."
        lang = (repo.get("language") or "").strip()
        lang = _html_escape(lang) if lang else "—"
        rows.append([cell_name, desc, lang])
    if not rows:
        return []
    header = "<thead><tr><th>Repository</th><th>Description</th><th>Language</th></tr></thead>"
    body_rows = "".join(
        f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>"
        for a, b, c in rows
    )
    table = f"<table>{header}<tbody>{body_rows}</tbody></table>"
    return [table]


def _section_badges(profile_data: Dict[str, Any], config: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
    return _optional_markdown(_build_badges, profile_data, config)


def _section_charts(profile_data: Dict[str, Any], config: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
    return _optional_markdown(_build_charts, profile_data, config)


def _optional_markdown(
    fn: Optional[Any],
    profile_data: Dict[str, Any],
    config: Dict[str, Any],
) -> Tuple[List[str], Dict[str, Any]]:
    if fn is None:
        return [], {}
    try:
        value = fn(profile_data, config)
    except TypeError:
        value = fn(profile_data)
    return _extract_markdown(value)


def _extract_markdown(value: Any) -> Tuple[List[str], Dict[str, Any]]:
    if value is None:
        return [], {}

    assets: Dict[str, Any] = {}
    if isinstance(value, dict):
        assets = value.get("assets") or {}
        markdown = value.get("markdown")
        if markdown is None:
            markdown = value.get("content") or value.get("text")
        value = markdown

    if isinstance(value, str):
        return _trim_empty_lines(_split_lines(value)), assets

    if isinstance(value, (list, tuple)):
        lines: List[str] = []
        for item in value:
            if item is None:
                continue
            if isinstance(item, str):
                lines.extend(_split_lines(item))
            else:
                lines.append(str(item))
        return _trim_empty_lines(lines), assets

    return [str(value)], assets


def _parse_language_item(item: Any) -> Optional[Tuple[str, float]]:
    if isinstance(item, (list, tuple)) and len(item) >= 2:
        name, value = item[0], item[1]
        if name is None or value is None:
            return None
        return str(name), float(value)
    if isinstance(item, dict):
        name = item.get("name") or item.get("language")
        value = item.get("bytes") or item.get("value") or item.get("count")
        if name is None or value is None:
            return None
        return str(name), float(value)
    return None


def _format_repo(repo: Dict[str, Any], show_stats: bool = True) -> Optional[str]:
    name = repo.get("name") or "repository"
    url = repo.get("url")
    description = repo.get("description")
    stars = repo.get("stars")
    forks = repo.get("forks")
    language = repo.get("language")

    title = f"[{name}]({url})" if url else str(name)
    if isinstance(description, str) and description.strip():
        title = f"{title} - {description.strip()}"

    stats: List[str] = []
    if show_stats:
        if stars is not None:
            stats.append(f"Stars: {stars}")
        if forks is not None:
            stats.append(f"Forks: {forks}")
        if isinstance(language, str) and language.strip():
            stats.append(f"Language: {language.strip()}")

    if stats:
        title = f"{title} ({', '.join(stats)})"
    return title


def _normalize_sections(sections_value: Any) -> List[str]:
    if not sections_value:
        return []
    if not isinstance(sections_value, list):
        sections_value = [sections_value]

    normalized: List[str] = []
    for item in sections_value:
        name = None
        enabled = True
        if isinstance(item, str):
            name = item
        elif isinstance(item, dict):
            enabled = item.get("enabled", True)
            name = item.get("id") or item.get("name") or item.get("section")

        if not enabled or not name:
            continue

        canonical = _canonical_section(str(name))
        if canonical and canonical not in normalized:
            normalized.append(canonical)

    return normalized


def _canonical_section(name: str) -> Optional[str]:
    key = name.strip().lower()
    mapping = {
        "header": "header",
        "title": "header",
        "titulo": "header",
        "badges": "badges",
        "insignias": "badges",
        "bio": "bio",
        "about": "bio",
        "acerca": "bio",
        "stats": "stats",
        "statistics": "stats",
        "estadisticas": "stats",
        "languages": "languages",
        "lenguajes": "languages",
        "repos": "repos",
        "repositories": "repos",
        "repositorios": "repos",
        "charts": "charts",
        "graficos": "charts",
    }
    return mapping.get(key)


def _build_title(profile_data: Dict[str, Any]) -> str:
    username = profile_data.get("username")
    name = profile_data.get("name")
    if isinstance(name, str) and name.strip():
        if isinstance(username, str) and username.strip():
            if name.strip().lower() != username.strip().lower():
                return f"{name.strip()} (@{username.strip()})"
        return name.strip()
    if isinstance(username, str) and username.strip():
        return f"@{username.strip()}"
    return "GitHub Profile"


def _append_section(lines: List[str], title: Optional[str], body: Iterable[str]) -> None:
    body_lines: List[str] = []
    for line in body:
        if isinstance(line, str):
            body_lines.append(line.rstrip())
        else:
            body_lines.append(str(line))

    body_lines = _trim_empty_lines(body_lines)
    if not body_lines:
        return
    if lines:
        lines.append("")
    if title:
        lines.append(f"## {title}")
        lines.append("")
    lines.extend(body_lines)


def _split_lines(text: str) -> List[str]:
    return [line.rstrip() for line in text.splitlines()]


def _trim_empty_lines(lines: List[str]) -> List[str]:
    start = 0
    end = len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return lines[start:end]


def _merge_assets(existing: Dict[str, Any], new_assets: Dict[str, Any]) -> Dict[str, Any]:
    if not new_assets:
        return existing
    merged = dict(existing)
    for key, value in new_assets.items():
        if key not in merged:
            merged[key] = value
        else:
            merged[key] = value
    return merged


def _coerce_int(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
