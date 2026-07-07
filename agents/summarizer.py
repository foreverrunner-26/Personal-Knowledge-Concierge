"""
Summarizer Agent
================
Stage 2 of the agent pipeline: Generates TL;DR summaries and detailed
digests for curated articles.

The Summarizer Agent demonstrates:
- Tool use via MCP (summarize_text, analyze_repo)
- Integration with the LLM for natural language generation
- Different output formats for different content types

This is the "brain" of the Knowledge Concierge — it reads the articles
so the user doesn't have to, extracting actionable insights.
"""

import time
from datetime import datetime
from typing import Any, Optional

from memory.memory_store import MemoryStore
from utils.config import Config
from utils.demo_data import DEMO_ARTICLES


class SummarizerAgent:
    """
    Generates summaries and walkthroughs for curated content.

    Produces two levels of summary:
    1. TL;DR — 1-2 sentence takeaway for quick scanning
    2. Detailed summary — structured markdown with key findings

    For GitHub repos, generates a code walkthrough instead.
    """

    def __init__(self, mcp_server=None, memory_store: Optional[MemoryStore] = None):
        """
        Args:
            mcp_server: MCPServer instance for tool calls.
            memory_store: MemoryStore instance to persist summaries.
        """
        self.mcp = mcp_server
        self.memory = memory_store or MemoryStore()

    def digest(self, articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Generate summaries for a list of curated articles.

        Args:
            articles: List of article dicts from the Curator Agent.

        Returns:
            The same articles with 'tl_dr', 'full_summary', and
            'digested_at' fields added.
        """
        digested = []

        for article in articles:
            article_id = article.get("id", "")
            source = article.get("source", "")

            if Config.DEMO_MODE:
                # Use pre-loaded summaries from demo data
                digested_article = self._digest_demo(article)
            elif self.mcp:
                # Use MCP tools for live summarization
                digested_article = self._digest_live(article, source)
            else:
                # Fallback: mark as needing live mode
                article["tl_dr"] = article.get("tl_dr", "Summary unavailable in demo-limited mode.")
                article["full_summary"] = article.get("full_summary", "")
                digested_article = article

            digested_article["digested_at"] = datetime.now().isoformat()

            # Persist the full article to reading history (preserves source_url,
            # full_summary, relevance_score, and all other fields)
            self.memory.add_reading(digested_article)

            digested.append(digested_article)

        # Simulate processing time for UX
        if Config.DEMO_MODE:
            time.sleep(0.5)

        return digested

    def _digest_demo(self, article: dict[str, Any]) -> dict[str, Any]:
        """Use pre-loaded summaries from demo data."""
        article_id = article.get("id", "")
        for demo in DEMO_ARTICLES:
            if demo["id"] == article_id:
                article["tl_dr"] = demo["tl_dr"]
                article["full_summary"] = demo["full_summary"]
                article["related_to"] = demo.get("related_to", [])
                article["relation_type"] = demo.get("relation_type", "related_to")
                return article

        # If no demo summary exists, create a simple one
        # Ensure the article has an id for downstream consumers
        if not article.get("id"):
            article["id"] = f"article-{hash(article.get('title', ''))}"
        article["tl_dr"] = (
            f"A {article.get('source', 'recent')} article about "
            f"{', '.join(article.get('topics', ['various topics']))}."
        )
        article["full_summary"] = "Full summary not available in demo mode."
        return article

    def _digest_live(self, article: dict[str, Any], source: str) -> dict[str, Any]:
        """Use MCP tools and LLM for live summarization."""
        article_id = article.get("id", "")

        if source == "GitHub Trending" and self.mcp:
            # Generate code walkthrough
            repo_url = article.get("source_url", "")
            result = self.mcp.call_tool("analyze_repo", {"repo_url": repo_url})
            if result.get("success"):
                article["full_summary"] = result["data"].get("walkthrough", "")
                article["tl_dr"] = article.get("tl_dr", "Code repository analysis.")
        else:
            # Generate article summary
            content = article.get("content", article.get("summary", ""))
            if content and self.mcp:
                result = self.mcp.call_tool("summarize_text", {
                    "text": content,
                    "article_id": article_id,
                })
                if result.get("success"):
                    article["tl_dr"] = result["data"].get("tl_dr", "")
                    article["full_summary"] = result["data"].get("detailed_summary", "")

        return article

    def generate_walkthrough(self, repo_url: str) -> dict[str, Any]:
        """
        Generate a detailed code walkthrough for a GitHub repository.

        Args:
            repo_url: GitHub repository URL.

        Returns:
            Dict with walkthrough content.
        """
        if self.mcp:
            result = self.mcp.call_tool("analyze_repo", {"repo_url": repo_url})
            if result.get("success"):
                return result["data"]

        # Demo fallback
        for article in DEMO_ARTICLES:
            if repo_url in article.get("source_url", ""):
                return {
                    "repo_url": repo_url,
                    "walkthrough": article["full_summary"],
                }

        return {
            "repo_url": repo_url,
            "walkthrough": "Walkthrough not available for this repository.",
        }
