"""
Memory Store Module
===================
Persistent JSON-based memory for the Knowledge Concierge.
Stores reading history, preferences, and knowledge graph data.

The memory store is the "brain" of the agent — it persists everything
the agent has learned across sessions, enabling the knowledge graph
and reading history features.

Design: File-based JSON storage for hackathon simplicity.
No external database required — the entire memory is a single JSON file.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from utils.config import Config


class MemoryStore:
    """
    JSON-file-based persistent memory for the agent system.

    Stores three categories of data:
    1. Reading history — all articles processed by the agent
    2. Preferences — user's configured interests and sources
    3. Knowledge graph — nodes and edges for the mind map

    Uses separate files for demo vs live mode (memory_demo.json / memory_live.json)
    via Config.MEMORY_STORE_PATH.
    """

    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize the memory store.

        Args:
            file_path: Path to the JSON file. Defaults to Config.MEMORY_STORE_PATH.
        """
        if file_path is None:
            file_path = Config.MEMORY_STORE_PATH
        self.file_path = file_path
        self._data = self._load()

    def _load(self) -> dict[str, Any]:
        """Load memory from disk, or initialize empty store."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # Fresh memory store
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "reading_history": [],
            "preferences": {},
            "knowledge_graph": {
                "nodes": [],
                "edges": [],
            },
        }

    def _save(self) -> None:
        """Persist the current memory state to disk."""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    # ── Reading History ───────────────────────────────────────────────────

    def add_reading(self, article: dict[str, Any]) -> None:
        """
        Add an article to the reading history.

        Args:
            article: Dict with at least 'id', 'title', 'date'.
                     May include 'summary', 'topics', 'source', etc.
        """
        entry = {
            **article,
            "processed_at": datetime.now().isoformat(),
        }
        # Avoid duplicates — replace if same ID exists
        existing = self.get_reading(article.get("id", ""))
        if existing:
            self._data["reading_history"].remove(existing)
        self._data["reading_history"].append(entry)
        self._save()

    def get_reading(self, article_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a single reading by article ID."""
        for entry in self._data["reading_history"]:
            if entry.get("id") == article_id:
                return entry
        return None

    def get_all_readings(self) -> list[dict[str, Any]]:
        """Return all reading history, most recent first."""
        return sorted(
            self._data["reading_history"],
            key=lambda r: r.get("processed_at", r.get("date", "")),
            reverse=True,
        )

    def search_readings(self, query: str) -> list[dict[str, Any]]:
        """
        Simple keyword search across reading history.
        Searches title, topics, and summary fields.

        Args:
            query: Search keywords.

        Returns:
            Matching readings, ranked by relevance (title matches first).
        """
        query_lower = query.lower()
        results = []
        for entry in self._data["reading_history"]:
            score = 0
            title = entry.get("title", "").lower()
            if query_lower in title:
                score += 10

            topics = " ".join(entry.get("topics", [])).lower()
            if query_lower in topics:
                score += 5

            summary = entry.get("tl_dr", "") + entry.get("full_summary", "")
            if query_lower in summary.lower():
                score += 2

            if score > 0:
                results.append((score, entry))

        results.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in results]

    # ── Preferences ────────────────────────────────────────────────────────

    def get_preferences(self) -> dict[str, Any]:
        """Get user preferences dict."""
        return self._data.get("preferences", {})

    def save_preferences(self, preferences: dict[str, Any]) -> None:
        """Save user preferences."""
        self._data["preferences"] = {
            **self._data.get("preferences", {}),
            **preferences,
            "updated_at": datetime.now().isoformat(),
        }
        self._save()

    # ── Knowledge Graph ────────────────────────────────────────────────────

    def get_graph(self) -> dict[str, Any]:
        """Get the full knowledge graph (nodes + edges)."""
        return self._data.get("knowledge_graph", {"nodes": [], "edges": []})

    def add_graph_node(self, node_id: str, label: str,
                       node_type: str = "article",
                       group: str = "default",
                       metadata: Optional[dict[str, Any]] = None) -> None:
        """
        Add a node to the knowledge graph.

        Args:
            node_id: Unique identifier.
            label: Display label.
            node_type: 'article' or 'topic'.
            group: Category for visual grouping.
            metadata: Extra key-value pairs.
        """
        nodes = self._data["knowledge_graph"]["nodes"]
        # Replace if exists
        nodes = [n for n in nodes if n.get("id") != node_id]
        nodes.append({
            "id": node_id,
            "label": label,
            "type": node_type,
            "group": group,
            "metadata": metadata or {},
            "added_at": datetime.now().isoformat(),
        })
        self._data["knowledge_graph"]["nodes"] = nodes
        self._save()

    def add_graph_edge(self, source: str, target: str,
                       relation: str = "related_to") -> None:
        """
        Add an edge between two nodes in the knowledge graph.

        Args:
            source: Source node ID.
            target: Target node ID.
            relation: Type of relationship (e.g., 'builds_on', 'enables').
        """
        edges = self._data["knowledge_graph"]["edges"]
        # Avoid duplicate edges
        for e in edges:
            if e.get("source") == source and e.get("target") == target:
                return
        edges.append({
            "source": source,
            "target": target,
            "relation": relation,
            "added_at": datetime.now().isoformat(),
        })
        self._data["knowledge_graph"]["edges"] = edges
        self._save()

    def upsert_graph_edge(self, source: str, target: str,
                          relation: str = "related_to") -> None:
        """
        Add or update an edge. If the edge exists, update its relation.
        """
        edges = self._data["knowledge_graph"]["edges"]
        for e in edges:
            if e.get("source") == source and e.get("target") == target:
                e["relation"] = relation
                e["updated_at"] = datetime.now().isoformat()
                self._save()
                return
        self.add_graph_edge(source, target, relation)

    def clear_graph(self) -> None:
        """Reset the knowledge graph."""
        self._data["knowledge_graph"] = {"nodes": [], "edges": []}
        self._save()

    def clear_all(self) -> None:
        """Reset the entire memory store — readings, preferences, and graph."""
        self._data = {
            "version": self._data.get("version", "1.0"),
            "created_at": datetime.now().isoformat(),
            "reading_history": [],
            "preferences": {},
            "knowledge_graph": {"nodes": [], "edges": []},
        }
        self._save()

    # ── Stats ──────────────────────────────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        """
        Get summary statistics about the memory store.

        Returns:
            Dict with counts and computed stats.
        """
        readings = self._data["reading_history"]
        graph = self._data["knowledge_graph"]
        topics = set()
        for r in readings:
            for t in r.get("topics", []):
                topics.add(t)

        return {
            "total_readings": len(readings),
            "unique_topics": len(topics),
            "graph_nodes": len(graph["nodes"]),
            "graph_edges": len(graph["edges"]),
            "top_topics": sorted(topics)[:10],
            "first_reading": readings[-1].get("date") if readings else None,
            "last_reading": readings[0].get("date") if readings else None,
        }
