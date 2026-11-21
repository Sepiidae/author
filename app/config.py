"""Application configuration.

Basic configs are stored in YAML, but most runtime configs persist to the
database (see :mod:`app.models`). Local secrets live in a ``.env`` file that is
ignored by git (see ``.gitignore``).

The database URL, secret key, OAuth credentials and AI endpoint are read from
environment / ``.env`` so no password or secret is ever hard-coded. On first run
the admin is prompted in the web UI for the initial admin password
(see ``app/first_run.py``).
"""
from __future__ import annotations

import os
from functools import lru_cache

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
# YAML based basic configuration
# ---------------------------------------------------------------------------
# The YAML file holds only *basic* (non-secret) settings. Everything that can
# change at runtime lives in the database instead. The path is overridable so
# tests and deployments can point at their own file.
CONFIG_PATH = os.environ.get("BOOK_AUTHOR_CONFIG", "config.yaml")


def load_yaml_config(path: str = CONFIG_PATH) -> dict:
    """Load the basic YAML config, returning ``{}`` when it does not exist."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    assert isinstance(data, dict)
    return data


class Settings(BaseSettings):
    """Runtime settings, layered: env / ``.env`` override YAML defaults."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Book Author"
    admin_email: str = ""

    # --- Database -------------------------------------------------------
    # Supported schemes: sqlite (default), postgresql, mysql/mariadb.
    # Examples:
    #   sqlite:      sqlite:///./data/book_author.db
    #   postgres:    postgresql+psycopg2://user:pass@host:5432/book_author
    #   mariadb:     mysql+pymysql://user:pass@host:3306/book_author
    database_url: str = "sqlite:///./data/book_author.db"

    # --- Auth -----------------------------------------------------------
    secret_key: str = "change-me-on-first-run"
    access_token_expire_minutes: int = 60 * 24
    # Google OAuth (optional). Leave client id/secret blank to disable.
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    # --- AI -------------------------------------------------------------
    # Our endpoint + model (see README for details).
    ai_base_url: str = "https://llm-router.iam.hpc.fau.edu/v1"
    ai_model: str = "ornith-1.5"
    ai_fast_model: str = "ornith-1.5:9b"
    ai_api_key: str = ""
    ai_context_tokens: int = 100_000
    # Reserve headroom for output + safety when compressing context.
    ai_reserve_tokens: int = 20_000

    # --- Uploads --------------------------------------------------------
    upload_dir: str = "uploads"
    data_dir: str = "data"

    # --- Project metadata (from YAML) ----------------------------------
    default_language: str = "en"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings, seeding non-secret basics from YAML."""
    yaml_cfg = load_yaml_config()
    overrides = {
        k: v
        for k, v in yaml_cfg.get("app", {}).items()
        if k not in {"secret_key", "database_url"}  # secrets/urls come from env
    }
    return Settings(**overrides)
