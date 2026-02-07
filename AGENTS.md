# Multi-Agent Plan: GitHub Profile README Generator

## Goal

Generate a GitHub Profile README.md from GitHub data + user config, with preview and export.

## Shared Contracts (DO NOT BREAK)

- Backend returns JSON schemas in backend/app/schemas.py
- Frontend consumes backend endpoints in frontend/src/api.ts

## Data Schemas

- ProfileData: repos, languages, stats
- ReadmeConfig: sections, theme, layout
- GeneratedReadme: markdown, assets(optional)

## Agent Ownership

### Agent 1 — GitHub Data (backend/app/github_client.py)

- Fetch user profile, repos, languages, contribution stats (as possible via API)
- Provide ProfileData

### Agent 2 — Badges + Charts (backend/app/badges.py, backend/app/charts.py)

- Build badge markdown blocks
- Build chart URLs/markdown (no heavy image generation required)

### Agent 3 — Sections Builder (backend/app/readme_builder.py)

- Turn ProfileData + ReadmeConfig into Markdown sections
- Ensure stable markdown output

### Agent 4 — Frontend Preview + Export (frontend/)

- UI form to configure sections
- Live markdown preview
- Export README.md (download/copy)

## Endpoints

- GET /api/profile/{username} -> ProfileData
- POST /api/generate -> GeneratedReadme (input: ReadmeConfig + ProfileData OR username)

## Definition of Done

- Generate README for a username with default config
- Frontend shows preview and exports markdown
- Minimal tests for backend generation
