# GitHub Profile README Generator

A small full-stack app that generates a **GitHub Profile README.md** from your GitHub data and a configurable set of sections (badges, stats, top languages, featured repos). Includes a live preview and export.

<!-- Add a short demo GIF here when you have one:
![Demo](./docs/demo.gif)
-->

## Why this project exists

This project was created to **explore multi-agent development workflows** and “vibe coding.” It demonstrates structured agent collaboration: separate agents own GitHub data, badges/charts, section building, and the frontend. It is **not** an enterprise-grade product—it is a **learning and experimentation** repository. See [AGENTS.md](./AGENTS.md) for the agent plan and ownership.

## Tech stack

| Layer    | Stack                                                                |
| -------- | -------------------------------------------------------------------- |
| Backend  | Python 3.12, FastAPI, Uvicorn, httpx, Pydantic                       |
| Frontend | React 19, TypeScript, Vite                                           |
| APIs     | GitHub REST API (profile, repos, languages)                          |
| Charts   | External services (e.g. github-readme-stats) for stats/language SVGs |

## Architecture overview

```
┌─────────────┐     /api/*      ┌─────────────┐     GitHub API
│   Frontend  │ ◄──────────────►│   Backend   │ ◄──────────────► api.github.com
│ (React/Vite)│   proxy or      │ (FastAPI)   │
└─────────────┘   same-origin   └─────────────┘
                                       │
                                       ▼
                                readme_builder,
                                badges, charts
```

- **Backend** (`backend/app/`): `GET /api/profile/{username}` returns profile + repos + languages; `POST /api/generate` returns generated markdown. See [CONTRACTS.md](./CONTRACTS.md) for API contracts.
- **Frontend**: Form to set username and config, live markdown preview, copy/download README.

## Installation

### Manual setup

#### Backend

- **Python**: 3.12+ recommended.
- From the repo root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Run the API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run from the `backend/` directory so the `app` package resolves correctly.

#### Frontend

- **Node**: 18+ (20 LTS recommended).
- From the repo root:

```bash
cd frontend
npm install
npm run dev
```

Dev server runs with Vite and proxies `/api` to the backend (default `http://127.0.0.1:8000`).

#### Environment setup

1. Copy the example env file and add your values (never commit real secrets):

```bash
cp backend/.env.example backend/.env
```

2. Edit `backend/.env`:

- **GITHUB_TOKEN** (recommended): [Create a token](https://github.com/settings/tokens) (e.g. no scopes or `public_repo`). Without it, GitHub allows ~60 requests/hour; with it, ~5000/hour.
- Optional: `GITHUB_MAX_REPOS`, `GITHUB_LANGUAGE_REPO_LIMIT`, `GITHUB_REPO_RESULT_LIMIT` (see `backend/.env.example`).

3. Frontend: optional; see `frontend/.env.example` only if you add something like `VITE_API_URL` later.

### Docker

Before first run, create `backend/.env` (required by Compose; you can leave values as placeholders or set `GITHUB_TOKEN` for higher API limits):

```bash
cp backend/.env.example backend/.env
```

Then from the repo root:

```bash
docker compose up --build
```

- Backend: http://localhost:8000
- Frontend (production build behind nginx): http://localhost:3000

Frontend container proxies `/api` to the backend service.

## API usage example

```bash
# Profile data
curl -s http://localhost:8000/api/profile/octocat | jq .

# Generate README
curl -s -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"username":"octocat","config":{"sections":["intro","stats","languages","repos"],"theme":"dark","layout":"default"}}' | jq -r .markdown
```

## Folder structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, routes
│   │   ├── github_client.py # GitHub API client
│   │   ├── readme_builder.py
│   │   ├── badges.py
│   │   ├── charts.py
│   │   └── schemas.py       # Pydantic / contract shapes
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api.ts          # API client (contract consumer)
│   │   └── ...
│   ├── nginx.conf          # Used by frontend Docker image
│   ├── .env.example
│   └── Dockerfile
├── docker-compose.yml
├── AGENTS.md               # Multi-agent plan
├── CONTRACTS.md            # API contracts
└── README.md
```

## Contributing

Contributions are welcome. Please open an issue or PR. Keep API contracts in sync with `backend/app/schemas.py` and `frontend/src/api.ts`; see [CONTRACTS.md](./CONTRACTS.md).

## License

See [LICENSE](./LICENSE) (MIT).
