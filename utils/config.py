"""
Configuration Module
====================
Loads environment variables and provides a centralized configuration
object for the entire application.

LLM Provider: OpenAI-compatible API (DeepSeek, OpenAI, etc.)
Configure via API_KEY, BASE_URL, and MODEL in your .env file.

Security: API keys are loaded from environment variables only,
never hardcoded. Use .env.template as a reference.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Config:
    """
    Centralized configuration for the Personal Knowledge Concierge.

    All sensitive values are loaded from environment variables.
    For the hackathon demo, DEMO_MODE defaults to True so the app
    works out-of-the-box without API keys.

    LLM Provider: Any OpenAI-compatible API endpoint.
    Configure API_KEY, BASE_URL, and MODEL in your .env file.
    """

    # ── LLM API Configuration (provider-agnostic) ────────────────────────
    # Use API_KEY for any OpenAI-compatible provider.
    # Falls back to DEEPSEEK_API_KEY for backward compatibility.
    API_KEY: str = os.getenv(
        "API_KEY",
        os.getenv("DEEPSEEK_API_KEY",
        os.getenv("ANTHROPIC_API_KEY", "")),
    )

    # Base URL for the API endpoint.
    # Falls back to DEEPSEEK_BASE_URL for backward compatibility.
    BASE_URL: str = os.getenv(
        "BASE_URL",
        os.getenv("DEEPSEEK_BASE_URL",
        "https://api.deepseek.com"),
    )

    # Model name — provider-specific identifier.
    # Falls back to DEEPSEEK_MODEL for backward compatibility.
    MODEL: str = os.getenv(
        "MODEL",
        os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    )

    # ── Backward-compatible aliases (deprecated, prefer API_KEY/BASE_URL/MODEL) ──
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # ── GitHub (optional, for higher rate limits) ───────────────────────
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

    # ── Demo mode — when True, uses pre-loaded demo data instead of live APIs
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() == "true"

    # ── Memory store path (separate for demo vs live) ────────────────────
    _memory_base = Path(__file__).parent.parent / "memory"

    MEMORY_STORE_PATH: str = os.getenv(
        "MEMORY_STORE_PATH",
        str(_memory_base / ("memory_demo.json" if DEMO_MODE else "memory_live.json")),
    )

    # Preferences path (separate for demo vs live)
    PREFERENCES_PATH: str = os.getenv(
        "PREFERENCES_PATH",
        str(_memory_base / ("preferences_demo.json" if DEMO_MODE else "preferences_live.json")),
    )

    # ── Maximum articles per briefing ───────────────────────────────────
    MAX_ARTICLES_PER_BRIEFING: int = int(
        os.getenv("MAX_ARTICLES_PER_BRIEFING", "10")
    )

    # ── Convenience ────────────────────────────────────────────────────
    @classmethod
    def is_live_mode(cls) -> bool:
        """Check if the app should use live API calls."""
        return not cls.DEMO_MODE and bool(cls.API_KEY)

    @classmethod
    def validate(cls) -> list[str]:
        """
        Validate the configuration and return a list of warnings.
        An empty list means everything is configured correctly.
        """
        warnings = []
        if cls.DEMO_MODE:
            warnings.append(
                "[INFO] Running in DEMO MODE — using pre-loaded sample data. "
                "Set DEMO_MODE=false and add API_KEY to .env for live mode."
            )
        elif not cls.API_KEY:
            warnings.append(
                "[WARNING] DEMO_MODE is off but no API_KEY is set. "
                "Live agent features will not work."
            )
        return warnings
