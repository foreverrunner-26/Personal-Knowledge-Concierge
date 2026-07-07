"""
Curator Agent
=============
Stage 1 of the agent pipeline: Fetches and scores articles from
configured sources based on user interests.

The Curator Agent uses an LLM-as-a-Judge pattern:
  - Candidate articles are fetched from sources (APIs or demo data)
  - The LLM evaluates each article against user interests
  - Returns ranked articles with reasoning

When the LLM is unavailable, falls back to a lightweight keyword matcher.
"""

import json
import re
import time
from datetime import datetime
from typing import Any, Optional

from memory.memory_store import MemoryStore
from utils.config import Config
from utils.demo_data import DEMO_ARTICLES


class CuratorAgent:
    """
    Fetches and scores articles from multiple sources.

    Uses LLM-as-a-Judge for relevance scoring: candidate articles
    are sent to the LLM with a judging prompt that asks it to score
    and rank by relevance. Falls back to simple keyword matching
    when the LLM is unavailable.
    """

    def __init__(self, mcp_server=None, memory_store: Optional[MemoryStore] = None):
        self.mcp = mcp_server
        self.memory = memory_store or MemoryStore()

    # ── Public API ──────────────────────────────────────────────────────────

    def curate(self, interests: list[str], sources: list[str],
               max_articles: int = 10) -> list[dict[str, Any]]:
        """
        Fetch and score articles from configured sources.

        Returns articles sorted by LLM-assigned relevance score (descending).
        """
        # ── Step 1: Fetch candidates ────────────────────────────────────
        candidates = self._fetch_candidates(interests, sources, max_articles)

        if not candidates:
            return []

        # ── Step 2: Judge with LLM ──────────────────────────────────────
        scored = self._judge_articles_with_llm(candidates, interests)

        if scored is None:
            # LLM unavailable → lightweight fallback
            scored = self._score_fallback(candidates, interests)

        # Sort by LLM score descending, take top N
        scored.sort(key=lambda a: a.get("relevance_score", 0), reverse=True)
        return scored[:max_articles]

    # ── Step 1: Fetch candidates ────────────────────────────────────────────

    def _fetch_candidates(self, interests: list[str], sources: list[str],
                          max_articles: int) -> list[dict[str, Any]]:
        """Gather candidate articles from all configured sources."""
        if self.mcp and Config.is_live_mode():
            candidates = self._fetch_live(interests, sources, max_articles)
            if candidates:
                return candidates

        # Fallback: use demo articles
        return self._fetch_demo(sources)

    def _fetch_demo(self, sources: list[str]) -> list[dict[str, Any]]:
        """Collect all matching demo articles without scoring them."""
        candidates = []
        for article in DEMO_ARTICLES:
            if article["source"] in sources:
                candidates.append(dict(article))
        return candidates

    def _fetch_live(self, interests: list[str], sources: list[str],
                    max_articles: int) -> list[dict[str, Any]]:
        """Fetch from real APIs via MCP tools."""
        if not self.mcp:
            return []

        all_articles: list[dict[str, Any]] = []

        for interest in interests[:5]:
            n_per = max(2, max_articles // max(1, len(interests)))

            if "ArXiv" in sources:
                r = self.mcp.call_tool("search_arxiv",
                                       {"query": interest, "max_results": n_per})
                if r.get("success"):
                    for i, item in enumerate(r["data"].get("results", [])):
                        item.setdefault("topics", [interest])
                        item["source"] = "ArXiv"
                        all_articles.append(self._ensure_id(item, i))

            if "GitHub Trending" in sources:
                r = self.mcp.call_tool("search_github_trending",
                                       {"topic": interest, "max_results": n_per})
                if r.get("success"):
                    for i, item in enumerate(r["data"].get("results", [])):
                        item.setdefault("topics", [interest])
                        item["source"] = "GitHub Trending"
                        all_articles.append(self._ensure_id(item, i))

        # Deduplicate
        seen: set[str] = set()
        deduped = []
        for a in all_articles:
            key = a.get("title", "")[:60].lower().strip()
            if key and key not in seen:
                seen.add(key)
                deduped.append(a)

        return deduped

    # ── Step 2: LLM-as-a-Judge ──────────────────────────────────────────────

    def _judge_articles_with_llm(self, candidates: list[dict[str, Any]],
                                 interests: list[str]) -> Optional[list[dict[str, Any]]]:
        """
        Send candidate articles + user interests to the LLM for scoring.

        Returns None if the LLM is unavailable or fails, signalling
        the caller to use the fallback scorer.
        """
        if not self.mcp:
            return None

        # Check if LLM is available via the MCP server's call_tool
        try:
            result = self.mcp.call_tool("judge_articles", {
                "articles": [
                    {
                        "id": a.get("id", ""),
                        "title": a.get("title", ""),
                        "topics": a.get("topics", []),
                        "summary": (a.get("summary") or a.get("tl_dr") or "")[:300],
                        "source": a.get("source", ""),
                    }
                    for a in candidates[:20]  # Cap to avoid huge prompts
                ],
                "interests": interests,
            })

            if not result.get("success"):
                return None

            data = result.get("data", {})
            scored_list = data.get("scored", [])

            if not scored_list:
                return None

            # Merge scores back into candidate articles
            scored_map = {s["id"]: s for s in scored_list}
            merged = []
            for a in candidates:
                aid = a.get("id", "")
                if aid in scored_map:
                    a["relevance_score"] = scored_map[aid].get("score", 0.5)
                    a["judge_reason"] = scored_map[aid].get("reason", "")
                    a["judge_verdict"] = scored_map[aid].get("verdict", "relevant")
                else:
                    a["relevance_score"] = 0.3
                    a["judge_reason"] = "Not evaluated by judge"
                a["curated_at"] = datetime.now().isoformat()
                merged.append(a)

            return merged
        except Exception:
            return None

    # ── Fallback scorer (LLM unavailable) ──────────────────────────────────

    @staticmethod
    def _score_fallback(candidates: list[dict[str, Any]],
                        interests: list[str]) -> list[dict[str, Any]]:
        """Lightweight keyword scorer — used only when LLM is unavailable."""
        interests_lower = [i.lower() for i in interests]

        for a in candidates:
            title = a.get("title", "").lower()
            topics = " ".join(a.get("topics", [])).lower()
            summary = (a.get("summary") or a.get("tl_dr") or "").lower()

            score = 0.25  # base
            for interest in interests_lower:
                if interest in title:
                    score += 0.45
                elif interest in topics:
                    score += 0.35
                elif interest in summary:
                    score += 0.20
                elif any(w in title for w in interest.split() if len(w) > 3):
                    score += 0.10

            a["relevance_score"] = round(min(1.0, score), 3)
            a["judge_reason"] = "Keyword match (LLM unavailable)"
            a["curated_at"] = datetime.now().isoformat()

        return candidates

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _ensure_id(self, article: dict[str, Any], index: int) -> dict[str, Any]:
        """Ensure every article has a unique id for UI selection state."""
        if not article.get("id"):
            title = article.get("title", f"article-{index}")
            article["id"] = f"live-{hash(title) & 0x7FFFFFFF:08x}"
        return article
