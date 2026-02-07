# API Contracts

**Do not break.** Backend responses must match these shapes. Frontend consumes them in `frontend/src/api.ts`.

Schema definitions (source of truth): **`backend/app/schemas.py`**.

---

## Endpoints

| Method | Path                      | Description                                                                                                 |
| ------ | ------------------------- | ----------------------------------------------------------------------------------------------------------- |
| GET    | `/api/profile/{username}` | Returns **ProfileData**. 400 if username empty; 404 if GitHub user not found.                               |
| POST   | `/api/generate`           | Body: `{ "username": string, "config": ReadmeConfig }`. Returns **GeneratedReadme**. 400 if username empty. |

---

## ProfileData (GET /api/profile/{username})

| Field           | Type                 | Required | Notes                                   |
| --------------- | -------------------- | -------- | --------------------------------------- |
| `username`      | string               | yes      | GitHub login                            |
| `name`          | string \| null       | no       | Display name                            |
| `bio`           | string \| null       | no       | Profile bio                             |
| `followers`     | number \| null       | no       | Top-level for frontend and badges/stats |
| `public_repos`  | number \| null       | no       | Top-level for frontend and badges/stats |
| `top_languages` | `[string, number][]` | yes      | List of `[language_name, bytes]` tuples |
| `repos`         | ProfileRepo[]        | yes      | Array of repo objects                   |

**ProfileRepo:** `name`, `url`, `description?`, `stars?`, `forks?`, `language?` (all optional except `name`, `url`).

Backend may include extra fields (e.g. `avatar_url`, `profile_url`, `stats`, `languages`). Frontend and readme_builder use only the fields above.

---

## ReadmeConfig (POST /api/generate body.config)

| Field      | Type     | Default                                   |
| ---------- | -------- | ----------------------------------------- |
| `sections` | string[] | `[]` (backend then uses default sections) |
| `theme`    | string   | `"light"`                                 |
| `layout`   | string   | `"default"`                               |

---

## GeneratedReadme (POST /api/generate response)

| Field      | Type                           | Required | Notes                             |
| ---------- | ------------------------------ | -------- | --------------------------------- |
| `markdown` | string                         | yes      | Generated README markdown         |
| `assets`   | Record<string, string> \| null | no       | Optional asset URLs keyed by name |

---

## Error responses

- **400** – Bad request (e.g. missing or empty `username`). Body: `{ "detail": string }`.
- **404** – GitHub user not found. Body: `{ "detail": "GitHub user not found" }`.
- **502** – GitHub API or network failure. Body: `{ "detail": string }`.

Errors use FastAPI default: `application/json` with `detail` message.
