# Backend

Debes ejecutar uvicorn **desde esta carpeta** (`backend/`). Si lo ejecutas desde la raíz del repo, Python puede cargar el `app` de otro proyecto.

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --reload-exclude '.venv'
```

`--reload-exclude '.venv'` evita que uvicorn recargue al detectar cambios dentro del virtualenv (pip, site-packages).

Sin reload (producción):

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## GitHub token (recomendado)

Sin token, la API de GitHub limita las peticiones (60/hora). Con un token obtienes 5 000/hora.

1. En GitHub: **Settings → Developer settings → Personal access tokens** (o [crear token](https://github.com/settings/tokens)).
2. Crea un token con al menos el permiso **public_repo** (o sin permisos extra si solo quieres leer perfiles públicos).
3. Crea un archivo `.env` en la carpeta **`backend/`** (o en la raíz del repo) con:
   ```env
   GITHUB_TOKEN=ghp_tu_token_aqui
   ```
   El backend carga `.env` al arrancar (usa `python-dotenv`).
4. Reinicia el backend.

## Charts en GitHub

Los charts (stats, top languages) usan **github-readme-stats-fast.vercel.app**, un fork del original con mejor disponibilidad. Si en tu README de GitHub las imágenes de charts no cargan:

1. **Espera y recarga** — GitHub cachea imágenes; a veces tardan en aparecer.
2. **Comprueba la URL** — Debe ser `https://github-readme-stats-fast.vercel.app/api?username=TU_USER` (y similar para top-langs).
3. **Self-host** — Si el servicio público falla, puedes desplegar tu propia instancia: [github-readme-stats-fast](https://github.com/Pranesh-2005/github-readme-stats-fast) o [original](https://github.com/anuraghazra/github-readme-stats). Luego cambia `STATS_API_BASE` en `app/charts.py` a tu URL.

## Endpoints

- `GET /api/profile/{username}` — ProfileData
- `POST /api/generate` — Body: `{ "username": string, "config": object }` → GeneratedReadme
