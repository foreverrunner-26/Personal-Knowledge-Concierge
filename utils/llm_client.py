"""
LLM Client Module
=================
Wrapper around OpenAI-compatible APIs for agent text generation.
Provides a clean interface for calling LLM models with system prompts,
tool definitions, and structured output expectations.

Supports any OpenAI-compatible API:
  - DeepSeek:  https://api.deepseek.com
  - OpenAI:    https://api.openai.com/v1

SDK: OpenAI Python SDK (openai>=1.0.0).

Configure via API_KEY, BASE_URL, and MODEL in your .env file.

This module is used by all agents and the MCP server to interact
with the language model.
"""

import json
from typing import Any

from openai import OpenAI

from .config import Config


class LLMClient:
    """
    Wrapper for OpenAI-compatible APIs via the OpenAI SDK.

    Uses the standard OpenAI client pointed at the configured base URL.
    Works with any OpenAI-compatible provider (DeepSeek, OpenAI, etc.) —
    just set API_KEY, BASE_URL, and MODEL in .env.

    Provides a consistent interface for all agent types to call
    the LLM with system prompts and user messages. Supports both
    real API calls and a demo fallback mode.
    """

    def __init__(self):
        self.model = Config.MODEL
        self.base_url = Config.BASE_URL
        self._client = None
        if Config.is_live_mode():
            self._client = OpenAI(
                api_key=Config.API_KEY,
                base_url=self.base_url,
            )

    def is_available(self) -> bool:
        """Check if the live LLM client is ready."""
        return self._client is not None

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate a text response from the LLM.

        Args:
            system_prompt: The system-level instruction.
            user_message: The user's query or context.
            max_tokens: Maximum tokens in the response.
            temperature: Creativity level (0.0 = deterministic, 1.0 = creative).

        Returns:
            The generated text response.

        Raises:
            RuntimeError: If the client is not available (no API key configured).
        """
        if not self._client:
            raise RuntimeError(
                "LLM client is not available. "
                "Set API_KEY in your .env file, or enable DEMO_MODE."
            )

        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )

        # Extract text from the response
        content = response.choices[0].message.content
        return content.strip() if content else ""

    def generate_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[dict[str, Any]],
        max_tokens: int = 2000,
    ) -> dict[str, Any]:
        """
        Generate a response with tool use capability.

        Note: Function-calling support depends on the model/provider.
        Most modern models support function calling natively.

        Args:
            system_prompt: System instruction for the model.
            user_message: User query.
            tools: List of tool definitions in OpenAI format
                   ({"type": "function", "function": {...}}).
            max_tokens: Maximum tokens.

        Returns:
            Dict with 'text' (str) and 'tool_calls' (list) keys.
        """
        if not self._client:
            raise RuntimeError("LLM client is not available.")

        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            tools=tools,
            tool_choice="auto",
        )

        result = {"text": "", "tool_calls": []}
        message = response.choices[0].message

        if message.content:
            result["text"] = message.content.strip()

        if message.tool_calls:
            for tc in message.tool_calls:
                # Parse JSON arguments string into dict
                try:
                    arguments = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, AttributeError):
                    arguments = {}
                result["tool_calls"].append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "input": arguments,
                })

        return result

    def summarize(self, text: str, max_length: int = 200) -> str:
        """
        Generate a concise summary of the given text.

        Args:
            text: The text to summarize.
            max_length: Maximum summary length in words.

        Returns:
            Summarized text.
        """
        if not self._client:
            return self._demo_summary(text, max_length)

        return self.generate(
            system_prompt=(
                f"You are an expert summarizer. Create a concise summary "
                f"in no more than {max_length} words. Focus on the key "
                f"findings, methods, and implications. Be specific and "
                f"avoid vague language."
            ),
            user_message=f"Please summarize the following content:\n\n{text[:8000]}",
            max_tokens=500,
            temperature=0.3,
        )

    @staticmethod
    def _demo_summary(text: str, max_length: int) -> str:
        """Fallback summary for demo mode (simple extractive approach)."""
        sentences = text.replace("\n", " ").split(". ")
        if len(sentences) <= 3:
            return text[:max_length * 6]  # rough char estimate
        # Take first sentence + a couple from the middle
        selected = [sentences[0]] + sentences[len(sentences) // 2: len(sentences) // 2 + 2]
        summary = ". ".join(selected).strip()
        if len(summary.split()) > max_length:
            summary = " ".join(summary.split()[:max_length]) + "..."
        return summary
