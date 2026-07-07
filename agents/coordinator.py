"""
Coordinator Agent
=================
Top-level orchestrator for the Knowledge Concierge multi-agent system.

The Coordinator demonstrates the "Agent / Multi-agent System (ADK)"
course concept by implementing a coordinator-agent topology:

    CoordinatorAgent
         │
         ├── CuratorAgent      (Stage 1: Fetch & score)
         ├── SummarizerAgent   (Stage 2: Digest & summarize)
         └── GraphBuilderAgent (Stage 3: Map & visualize)

The coordinator:
1. Reads user preferences (interests, sources)
2. Dispatches to each sub-agent in sequence
3. Collects and merges results
4. Persists everything to the memory store
5. Returns a complete briefing package

This pipeline pattern is directly inspired by Google's ADK framework.
Each agent is specialized and reusable — you could swap in a different
summarizer or add new curator sources without changing the coordinator.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from memory.memory_store import MemoryStore
from mcp_server.server import MCPServer, create_mcp_server
from utils.config import Config
from utils.demo_data import DEMO_PREFERENCES

from .curator import CuratorAgent
from .summarizer import SummarizerAgent
from .graph_builder import GraphBuilderAgent

logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """
    Orchestrates the multi-agent pipeline for generating daily briefings.

    Pipeline:
        User Preferences → Curator → Summarizer → Graph Builder → Briefing

    Each stage feeds into the next. The coordinator handles:
    - Configuration loading (interests, sources, limits)
    - Progress tracking (for UI progress indicators)
    - Error handling (if one stage fails, the pipeline continues gracefully)
    - Result aggregation into a briefing package
    """

    def __init__(self, memory_store: Optional[MemoryStore] = None):
        """Initialize the coordinator with sub-agents, MCP server, and memory store.

        Args:
            memory_store: Optional shared MemoryStore. If not provided, a new
                          one is created. Use this to share a single memory
                          store between the coordinator and the UI.
        """
        # Initialize shared services — use provided store or create a new one
        self.memory = memory_store or MemoryStore()
        self.mcp: MCPServer = create_mcp_server(self.memory)

        # Initialize sub-agents with shared services
        # Each agent gets access to the MCP server for tool calls
        # and the memory store for persistence
        self.curator = CuratorAgent(
            mcp_server=self.mcp,
            memory_store=self.memory,
        )
        self.summarizer = SummarizerAgent(
            mcp_server=self.mcp,
            memory_store=self.memory,
        )
        self.graph_builder = GraphBuilderAgent(
            mcp_server=self.mcp,
            memory_store=self.memory,
        )

        # Pipeline state for progress tracking
        self._progress: dict[str, str] = {}
        self._progress_callbacks: list[callable] = []

    def on_progress(self, callback: callable) -> None:
        """
        Register a progress callback for UI updates.

        The callback receives a dict with 'stage' and 'status' keys.
        Used by the Streamlit frontend to show the progress stepper.
        """
        self._progress_callbacks.append(callback)

    def _update_progress(self, stage: str, status: str) -> None:
        """Update pipeline progress and notify callbacks."""
        self._progress[stage] = status
        for cb in self._progress_callbacks:
            try:
                cb({"stage": stage, "status": status, "progress": dict(self._progress)})
            except Exception:
                pass

    def run_pipeline(
        self,
        interests: Optional[list[str]] = None,
        sources: Optional[list[str]] = None,
        max_articles: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Execute the full agent pipeline and return a briefing package.

        Args:
            interests: Topic keywords. Uses saved preferences if None.
            sources: Source names. Uses saved preferences if None.
            max_articles: Max articles to fetch. Uses config default if None.

        Returns:
            Briefing package with:
            - curated: List of curated articles with scores
            - digested: Articles with summaries added
            - graph: Knowledge graph nodes and edges
            - mindmap: Mermaid.js mind map syntax
            - stats: Pipeline statistics
            - pipeline_stages: Status of each stage
        """
        # Load preferences. In demo mode, fall back to DEMO_PREFERENCES.
        # In live mode, the user must configure their own — no presets.
        prefs = self.memory.get_preferences()
        if not prefs and Config.DEMO_MODE:
            prefs = DEMO_PREFERENCES
        interests = interests or prefs.get("interests", [])
        sources = sources or prefs.get("sources", [])
        max_articles = max_articles or prefs.get("max_articles", Config.MAX_ARTICLES_PER_BRIEFING)

        # Guard: require at least one interest and one source
        if not interests:
            return {
                "pipeline_run_id": f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "started_at": datetime.now().isoformat(),
                "pipeline_stages": {},
                "curated": [], "digested": [], "graph": {}, "mindmap": "",
                "stats": {}, "errors": [
                    "No interests configured. Add topics on the Interests page first."
                ],
            }
        if not sources:
            sources = ["ArXiv"]  # sensible default

        logger.info(f"Starting pipeline: {len(interests)} interests, "
                     f"{len(sources)} sources, max {max_articles} articles")

        result = {
            "pipeline_run_id": f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "started_at": datetime.now().isoformat(),
            "pipeline_stages": {},
            "curated": [],
            "digested": [],
            "graph": {},
            "mindmap": "",
            "stats": {},
            "errors": [],
        }

        # ── Stage 1: Curation ──────────────────────────────────────────
        self._update_progress("curation", "running")
        try:
            curated = self.curator.curate(
                interests=interests,
                sources=sources,
                max_articles=max_articles,
            )
            result["curated"] = curated
            result["pipeline_stages"]["curation"] = {
                "status": "completed",
                "articles_found": len(curated),
                "sources_queried": sources,
            }
            self._update_progress("curation", "completed")
            logger.info(f"Stage 1 (Curation): Found {len(curated)} articles")
        except Exception as e:
            result["errors"].append(f"Curation failed: {e}")
            result["pipeline_stages"]["curation"] = {"status": "failed", "error": str(e)}
            self._update_progress("curation", "failed")
            logger.error(f"Curation failed: {e}")

        # ── Stage 2: Summarization ─────────────────────────────────────
        self._update_progress("summarization", "running")
        try:
            digested = self.summarizer.digest(result["curated"])
            result["digested"] = digested
            result["pipeline_stages"]["summarization"] = {
                "status": "completed",
                "articles_digested": len(digested),
            }
            self._update_progress("summarization", "completed")
            logger.info(f"Stage 2 (Summarization): Digested {len(digested)} articles")
        except Exception as e:
            result["errors"].append(f"Summarization failed: {e}")
            result["pipeline_stages"]["summarization"] = {"status": "failed", "error": str(e)}
            result["digested"] = result["curated"]  # Pass through un-digested
            self._update_progress("summarization", "failed")
            logger.error(f"Summarization failed: {e}")

        # ── Stage 3: Graph Building ────────────────────────────────────
        self._update_progress("graph_building", "running")
        try:
            graph_result = self.graph_builder.build_graph(result["digested"])
            result["graph"] = graph_result.get("graph", {})
            result["mindmap"] = graph_result.get("mindmap", "")
            result["pipeline_stages"]["graph_building"] = {
                "status": "completed",
                "graph_nodes": graph_result.get("graph", {}).get("total_nodes", 0),
                "graph_edges": graph_result.get("graph", {}).get("total_edges", 0),
            }
            self._update_progress("graph_building", "completed")
            logger.info(f"Stage 3 (Graph): Built graph with "
                         f"{result['pipeline_stages']['graph_building']['graph_nodes']} nodes")
        except Exception as e:
            result["errors"].append(f"Graph building failed: {e}")
            result["pipeline_stages"]["graph_building"] = {"status": "failed", "error": str(e)}
            self._update_progress("graph_building", "failed")
            logger.error(f"Graph building failed: {e}")

        # ── Finalize ───────────────────────────────────────────────────
        result["completed_at"] = datetime.now().isoformat()
        result["stats"] = self.memory.get_stats()
        result["stats"]["pipeline_duration_seconds"] = round(
            (datetime.fromisoformat(result["completed_at"]) -
             datetime.fromisoformat(result["started_at"])).total_seconds(), 2
        )

        logger.info(f"Pipeline complete: {result['stats']}")
        self._update_progress("pipeline", "completed")

        return result

    def get_daily_briefing(self) -> dict[str, Any]:
        """
        Convenience method: Run pipeline with saved preferences.

        Returns the same briefing package as run_pipeline().
        """
        return self.run_pipeline()

    def search_knowledge_base(self, query: str) -> list[dict[str, Any]]:
        """
        Search the reading history for articles matching a query.

        Args:
            query: Search string.

        Returns:
            List of matching reading history entries.
        """
        return self.memory.search_readings(query)

    def get_mindmap(self, topic: str = "AI Agents") -> str:
        """
        Generate a mind map centered on a specific topic.

        Args:
            topic: Central topic for the mind map.

        Returns:
            Mermaid.js mind map syntax.
        """
        return self.graph_builder.get_mindmap_for_topic(topic)
