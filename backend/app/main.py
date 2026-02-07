from pathlib import Path
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel

# Carga .env desde backend/ o desde la raíz del repo
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv()

from app.github_client import fetch_profile_data
from app.readme_builder import build_readme

# Dominios permitidos para el proxy de imágenes (charts y badges)
ALLOWED_IMAGE_HOSTS = frozenset({
    "github-readme-stats.vercel.app",
    "github-readme-stats-fast.vercel.app",
    "streak-stats.demolab.com",
    "img.shields.io",
})

# Dominios que generan charts (si fallan, devolvemos placeholder en vez de 502)
CHART_HOSTS = frozenset({
    "github-readme-stats.vercel.app",
    "github-readme-stats-fast.vercel.app",
    "streak-stats.demolab.com",
})

# SVG placeholder cuando el servicio de charts no responde (timeout/error)
CHART_PLACEHOLDER_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="120" viewBox="0 0 400 120">'
    b'<rect width="400" height="120" fill="#f0f0f0" stroke="#ccc" stroke-width="1" rx="4"/>'
    b'<text x="200" y="65" text-anchor="middle" font-family="sans-serif" font-size="14" fill="#666">'
    + "Chart: se verá en tu README de GitHub".encode("utf-8")
    + b"</text></svg>"
)

app = FastAPI()


class GenerateRequest(BaseModel):
    username: str
    config: dict = {}


def _validate_username(username: str) -> str:
    cleaned = (username or "").strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="username is required and cannot be empty")
    return cleaned


@app.get("/api/profile/{username}")
async def profile(username: str):
    validated = _validate_username(username)
    return await fetch_profile_data(validated)


@app.get("/api/proxy-image")
async def proxy_image(url: str = Query(..., description="URL de la imagen")):
    """Proxy para imágenes externas (charts, badges) para evitar bloqueos por origen/referrer."""
    try:
        parsed = urlparse(url)
    except Exception:
        raise HTTPException(status_code=400, detail="URL inválida")
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(status_code=400, detail="URL inválida")
    if parsed.netloc.lower() not in ALLOWED_IMAGE_HOSTS:
        raise HTTPException(status_code=403, detail="Dominio no permitido para proxy")
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; GitHub-Readme-Generator/1.0; +https://github.com)",
        "Accept": "image/svg+xml,image/*,*/*",
    }
    host = parsed.netloc.lower()
    async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
        try:
            resp = await client.get(url, headers=headers)
        except httpx.HTTPError as e:
            if host in CHART_HOSTS:
                return Response(
                    content=CHART_PLACEHOLDER_SVG,
                    media_type="image/svg+xml",
                )
            raise HTTPException(status_code=502, detail="Error al obtener imagen") from e
    if resp.status_code != 200:
        if host in CHART_HOSTS:
            return Response(
                content=CHART_PLACEHOLDER_SVG,
                media_type="image/svg+xml",
            )
        raise HTTPException(status_code=502, detail="La imagen externa no está disponible")
    media_type = resp.headers.get("content-type", "image/png")
    return Response(content=resp.content, media_type=media_type)


@app.post("/api/generate")
async def generate(req: GenerateRequest):
    validated = _validate_username(req.username)
    profile_data = await fetch_profile_data(validated)
    result = build_readme(profile_data, req.config)
    return result
