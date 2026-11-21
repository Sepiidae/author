# Book Author

An AI-assisted tool for developing books, built as a Python (FastAPI) web
application. It helps an author generate **Background, Characters, Outlines and
Chapters** with AI assistance, while the author provides input at every step
(dialog, character descriptions, government, worldbuilding, etc.).

Ideas can be **linked** to Characters, Outlines, Background, Themes and Arcs.
Artwork (PNG / vector) can be attached to books. All text is stored as
**markdown** and can be exported to **TXT, MD, HTML, EPUB** and **Amazon (KDP)**
formats.

## Data model

```
Universe ── Series ── Book
   │                     │
   ├── Characters        ├── Outlines
   ├── Background        ├── Chapters
   ├── Themes            ├── Characters (book-scoped)
   ├── Arcs              └── Artwork (PNG / SVG)
   └── Ideas ──linked to── Character / Outline / Background / Theme / Arc
```

- **Universe → Series → Book** is the core hierarchy.
- Every prose field (description, body, dialog, etc.) is **markdown**.
- **Ideas** are free-form notes that link to any of the five target types.
- **Artwork** is stored on disk as PNG or vector (SVG); metadata in the DB.

## Features

- Email + password **and** Google OAuth authentication.
- No default password — the first user created in the web UI becomes the admin.
- Users can generate **API bearer tokens** to call the REST API directly.
- **REST API** for every action, with **Swagger / ReDoc** docs.
- AI via the OpenAI Python client against our endpoint
  (`https://llm-router.iam.hpc.fau.edu/v1`, model `ornith-1.5`, fast model
  `ornith-1.5:9b`). Context window is **100k** tokens; context is **compressed**
  when it would overflow.
- Persistent database supporting **SQLite, PostgreSQL and MariaDB**.
- Basic config in `config.yaml`; most runtime config persists in the **database**
  (see the `/settings` API).
- Export to TXT / MD / HTML / EPUB / Amazon (KDP).

## Quick start

```bash
# 1. Create a virtualenv and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure secrets (never committed)
cp .env.example .env
#   edit .env: set DATABASE_URL, SECRET_KEY, and AI_API_KEY

# 3. Run
uvicorn app.main:app --reload
```

Open <http://localhost:8000/docs> for the Swagger UI.

On first run you will be redirected to `/` where the **first-run setup page**
asks for an email + password — this creates the initial **admin** account. There
is no default password.

## Configuration

| Setting | Source | Notes |
| --- | --- | --- |
| `DATABASE_URL` | env / `.env` | `sqlite:///…`, `postgresql+psycopg2://…`, `mysql+pymysql://…` |
| `SECRET_KEY` | env / `.env` | Required; generate a random value |
| `AI_API_KEY` | env / `.env` | Sent to our endpoint |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | env / `.env` | Optional; enables Google login |
| basic app settings | `config.yaml` | Non-secret basics only |
| runtime settings | database (`/settings`) | Everything else |

Local secrets (`.env`, `secrets.yaml`, DB files, `uploads/`, logs) are ignored
by git — see `.gitignore`.

## API overview

| Group | Prefix | Purpose |
| --- | --- | --- |
| Auth | `/auth` | register, login, `/me`, API tokens, Google OAuth |
| Content | `/content` | Universe / Series / Book CRUD |
| Items | `/items` | Characters, Background, Themes, Arcs, Outlines, Chapters, Ideas + links |
| AI | `/ai` | AI-assisted generation of any element |
| Artwork | `/artwork` | Upload / list / download / delete images |
| Export | `/export` | Export a book to txt / md / html / amazon / epub |
| Settings | `/settings` | Database-persisted configuration |

### Example: create a universe, then a book, then export it

```bash
# register (first user becomes admin)
TOKEN=$(curl -s -X POST localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"author@example.com","password":"changeme123"}' \
  | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

# create a universe
U=$(curl -s -X POST localhost:8000/content/universes \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"title":"My Universe","description":"A world of ideas."}' \
  | python -c 'import sys,json;print(json.load(sys.stdin)["id"])')

# create a series, then a book
S=$(curl -s -X POST "localhost:8000/content/series?universe_id=$U" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"title":"Series One"}' \
  | python -c 'import sys,json;print(json.load(sys.stdin)["id"])')

B=$(curl -s -X POST "localhost:8000/content/books?series_id=$S" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"title":"Book One"}' \
  | python -c 'import sys,json;print(json.load(sys.stdin)["id"])')

# export the book as EPUB
curl -s -o book.epub "localhost:8000/export/books/$B?fmt=epub" \
  -H "Authorization: Bearer $TOKEN"
```

## Calling the API with a bearer token

Generate a token under **/auth/tokens** (or via the API):

```bash
curl -s -X POST "localhost:8000/auth/tokens?name=cli" \
  -H "Authorization: Bearer $TOKEN"
# returns a raw token once — store it, then use it as a Bearer token
```

The token is returned once; only a hash is stored. Use it like any Bearer token:

```bash
curl localhost:8000/auth/me -H "Authorization: Bearer <your-token>"
```

## AI context compression

When the assembled universe/book context exceeds the reserved token budget
(`AI_CONTEXT_TOKENS` − `AI_RESERVE_TOKENS`, i.e. ~80k of the 100k window), the
fast model (`ornith-1.5:9b`) summarises it, preserving named entities and plot
structure, before generation.

## Project layout

```
app/
  main.py          # FastAPI app, routing, first-run redirect
  config.py        # YAML + env settings
  database.py      # engine, session, Base (SQLite/Postgres/MariaDB)
  models.py        # ORM models
  schemas.py       # Pydantic schemas
  security.py      # password hashing + JWT / token auth
  ai.py            # OpenAI client, context compression, prompts
  first_run.py     # first-run admin setup page
  export.py        # TXT/MD/HTML/EPUB/Amazon exporters
  deps.py          # current-user / admin dependencies
  routers/         # auth, content, items, ai_api, artwork, export, settings
static/            # minimal demo frontend
config.yaml        # basic (non-secret) config
CHANGELOG.md
AGENTS.md
```

## Development

```bash
pip install -r requirements.txt
pytest            # run the test suite
```

## License

MIT
