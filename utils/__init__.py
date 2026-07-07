"""
Utilities Package — Personal Knowledge Concierge
=================================================
Shared utilities for configuration, LLM client, and demo data.

Modules:
    - config: Environment variable loading and configuration
    - llm_client: LLM API client wrapper (OpenAI SDK, provider-agnostic)
    - demo_data: Pre-loaded demo data for instant demos
"""

from .config import Config
from .llm_client import LLMClient

__all__ = ["Config", "LLMClient"]
