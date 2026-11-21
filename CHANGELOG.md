# Changelog

All notable changes to this project are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-11-21

### Added

- Initial release of **Book Author**, an AI-assisted book-development tool.
- Data hierarchy: **Universe → Series → Book**, with Characters, Background,
  Themes, Arcs, Outlines, Chapters, Ideas and Artwork.
- All text stored as markdown; export to **TXT, MD, HTML, EPUB** and
  **Amazon (KDP)** formats.
- **Ideas** that link to Characters, Outlines, Background, Themes and Arcs.
- Authentication via **Email + password** and **Google OAuth**; no default
  password (first-run admin setup in the web UI).
- User-generated **API bearer tokens** for direct REST access.
- REST API for all actions with **Swagger / ReDoc** documentation.
- AI assistance via the OpenAI Python client against
  `https://llm-router.iam.hpc.fau.edu/v1` (model `ornith-1.5`, fast model
  `ornith-1.5:9b`), 100k context window with **context compression**.
- Database support for **SQLite, PostgreSQL and MariaDB**.
- Basic configuration in `config.yaml`; runtime configuration persisted in the
  database (`/settings`).
- Local secrets ignored by git (`.env`, DBs, uploads, logs).
- `README.md`, `AGENTS.md`, `CHANGELOG.md`.

### Changed

- (none yet)

### Fixed

- (none yet)
