# AGENTS.md — guidance for AI agents working on Book Author

## What this project is

A FastAPI web app that helps authors develop books with AI assistance. Core
hierarchy: **Universe → Series → Book**, with Characters, Background, Themes,
Arcs, Outlines, Chapters and Ideas. Ideas link to Characters/Outlines/
Background/Themes/Arcs. All text is **markdown**; export to TXT/MD/HTML/EPUB/
Amazon (KDP). Auth is Email+password **and** Google OAuth.

## Hard rules

- **No default password.** The first user created (via the `/` first-run setup
  page or `/auth/register`) becomes the admin. Never hard-code credentials.
- **Secrets are never committed.** `.env`, `secrets.yaml`, DB files, `uploads/`
  and logs are git-ignored. Secrets come from env / `.env` only.
- **All actions are REST endpoints** and covered by Swagger (`/docs`).
- **AI endpoint/model are fixed:** base `https://llm-router.iam.hpc.fau.edu/v1`,
  model `ornith-1.5`, fast model `ornith-1.5:9b`, 100k context, compress when
  the assembled context overflows (see `app/ai.py`).
- **Database must support SQLite, PostgreSQL and MariaDB** (see `app/database.py`).

## Configuration layers (in priority order)

1. `config.yaml` — basic, non-secret settings only.
2. Environment / `.env` — secrets and the DB URL.
3. Database (`Setting` table, `/settings` API) — runtime config.

## Conventions

- Every prose/body field is stored as markdown. Keep it that way.
- IDs are hex UUIDs (`app/models.py::_uuid`).
- Ownership is enforced on every content endpoint (check `owner_id`).
- When adding a new content type, add CRUD in `app/routers/items.py`, a Pydantic
  schema in `app/schemas.py`, and (if it can be an idea target) register it in
  `schemas.TARGET_TYPES` and the `_validate_target` map.
- Keep the OpenAPI schema current — Swagger is the contract.

## Testing

```bash
pip install -r requirements.txt
pytest
```

Tests use `fastapi.testclient.TestClient` with an in-memory SQLite DB
(override `DATABASE_URL` before importing `app.database`).

## Do not

- Do not commit `.env`, databases, or uploads.
- Do not introduce a default password or disable auth on any endpoint.
- Do not change the AI endpoint/model without updating `config.py` and this file.
