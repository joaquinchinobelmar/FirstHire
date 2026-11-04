"""Runtime settings, read once from environment variables / .env files."""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BACKEND_DIR.parent

# backend/.env wins; the repo-root .env (used by the original skeleton) is a fallback.
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(REPO_DIR / ".env")


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    db_path: Path = Path(os.getenv("DB_PATH", BACKEND_DIR / "data" / "firsthire.db"))
    data_dir: Path = BACKEND_DIR / "data"

    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
    claude_effort: str = os.getenv("CLAUDE_EFFORT", "medium")
    ai_mode: str = os.getenv("AI_MODE", "auto").lower()

    companies_house_key: str = os.getenv("COMPANIES_HOUSE_API_KEY", "").strip()

    # Sign In with LinkedIn using OpenID Connect (students only)
    linkedin_client_id: str = os.getenv("LINKEDIN_CLIENT_ID", "").strip()
    linkedin_client_secret: str = os.getenv("LINKEDIN_CLIENT_SECRET", "").strip()
    linkedin_redirect_uri: str = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:5173/api/auth/linkedin/callback")

    session_ttl_hours: int = int(os.getenv("SESSION_TTL_HOURS", "12"))
    cookie_secure: bool = _bool("COOKIE_SECURE", False)
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    # Product rules enforced in code (never by the model)
    monthly_application_limit: int = 8
    min_answer_chars: int = 40

    @property
    def linkedin_mode(self) -> str:
        """live = real LinkedIn OAuth; demo = local simulated consent screen (no keys configured)."""
        return "live" if self.linkedin_client_id and self.linkedin_client_secret else "demo"

    @property
    def ai_enabled(self) -> bool:
        if self.ai_mode == "offline":
            return False
        has_creds = bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"))
        return has_creds or self.ai_mode == "claude"


settings = Settings()
