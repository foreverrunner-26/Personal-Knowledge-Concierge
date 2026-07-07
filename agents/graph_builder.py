"""
Graph Builder Agent
====================
Stage 3 of the agent pipeline: Transforms processed articles into
a connected knowledge graph and generates Mermaid.js mind maps.

The Graph Builder Agent demonstrates:
- Knowledge representation (nodes + edges)
- Cross-article relationship identification
- Visual synthesis via Mermaid.js

This is the "memory" of the Knowledge Concierge — it builds the
persistent, queryable structure that connects everything the user
has read.
"""

import time
from datetime import datetime
from typing import Any, Optional

from memory.memory_store import MemoryStore
from utils.config import Config
from utils.demo_data import DEMO_GRAPH_EDGES, DEMO_GRAPH_NODES


class GraphBuilderAgent:
    """
    Maintains the knowledge graph and generates visual mind maps.

    The graph has two types of nodes:
    - Topic nodes: High-level concepts (e.g., "AI Agents")
    - Article nodes: Individual readings attached to topics

    Edges represent relationships:
    - "about": Article is about this topic
    - "builds_on": Article extends/improves another article's work
    - "related_to": General conceptual connection
    - "enables": Article describes technology that enables another
    """

    RELATION_TYPES = [
        "about",
        "builds_on",
        "related_to",
        "enables",
        "extends",
        "implements",
        "used_by",
        "applies",
        "contextualizes",
    ]

    def __init__(self, mcp_server=None, memory_store: Optional[MemoryStore] = None):
        """
        Args:
            mcp_server: MCPServer instance for add_to_graph, generate_mindmap.
            memory_store: MemoryStore instance for graph persistence.
        """
        self.mcp = mcp_server
        self.memory = memory_store or MemoryStore()

    def build_graph(self, articles: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Add processed articles to the knowledge graph and generate
        a Mermaid.js mind map.

        Args:
            articles: List of digested articles with topics and relations.

        Returns:
            Dict with 'graph' (nodes+edges) and 'mindmap' (Mermaid.js syntax).
        """
        if Config.DEMO_MODE:
            return self._build_graph_demo(articles)
        return self._build_graph_live(articles)

    def _build_graph_demo(self, articles: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Demo mode: Build the graph from the articles that were actually curated,
        plus relevant existing demo nodes/edges that relate to those articles.
        No longer blindly adds every demo node — the graph reflects the *current*
        briefing, not the entire demo corpus.

        Also persists nodes and edges to the shared memory store so the sidebar
        stats and Knowledge Graph page reflect the pipeline results.
        """
        if not articles:
            return {
                "graph": {"nodes": [], "edges": [], "total_nodes": 0, "total_edges": 0},
                "mindmap": "mindmap\n  root(No articles curated)\n    (Try broader interests or more sources)",
                "built_at": datetime.now().isoformat(),
            }

        # Collect IDs of curated articles and their related articles
        curated_ids: set[str] = set()
        topic_labels: set[str] = set()

        for a in articles:
            aid = a.get("id", "")
            if aid:
                curated_ids.add(aid)
            for t in a.get("topics", []):
                topic_labels.add(t)
            for rid in a.get("related_to", []):
                curated_ids.add(rid)

        # ── Build nodes: only topics + curated (and related) articles ────
        nodes: list[dict[str, Any]] = []
        seen_nids: set[str] = set()

        # Add topic nodes for every topic tagged on the curated articles
        for label in topic_labels:
            tid = f"topic-{label.lower().replace(' ', '-').replace('&', 'and')}"
            if tid not in seen_nids:
                seen_nids.add(tid)
                nodes.append({
                    "id": tid, "label": label, "type": "topic", "group": "core",
                })

        # Add article nodes for curated + related articles (from demo data
        # so labels and groups are preserved)
        for n in DEMO_GRAPH_NODES:
            if n["id"] in curated_ids and n["id"] not in seen_nids:
                seen_nids.add(n["id"])
                nodes.append(dict(n))

        # Fallback: if an article id wasn't in DEMO_GRAPH_NODES, add a basic node
        for a in articles:
            aid = a.get("id", "")
            if aid and aid not in seen_nids:
                seen_nids.add(aid)
                nodes.append({
                    "id": aid,
                    "label": a.get("title", aid)[:50],
                    "type": "article",
                    "group": a.get("topics", ["default"])[0],
                })

        # ── Build edges: article→topic + cross-article ──────────────────
        edges: list[tuple[str, str, str]] = []
        seen_edges: set[tuple[str, str]] = set()

        def add_edge(src: str, tgt: str, rel: str) -> None:
            key = (src, tgt)
            if key not in seen_edges:
                seen_edges.add(key)
                edges.append((src, tgt, rel))

        for a in articles:
            aid = a.get("id", "")
            # Article → its topics
            for topic in a.get("topics", []):
                tid = f"topic-{topic.lower().replace(' ', '-').replace('&', 'and')}"
                add_edge(aid, tid, "about")
            # Cross-article edges from demo graph
            for (src, tgt, rel) in DEMO_GRAPH_EDGES:
                if (src == aid and tgt in curated_ids) or (tgt == aid and src in curated_ids):
                    add_edge(src, tgt, rel)

        # Also include edges where both ends are curated topics (topic–topic)
        for (src, tgt, rel) in DEMO_GRAPH_EDGES:
            if src in seen_nids and tgt in seen_nids:
                add_edge(src, tgt, rel)

        # ── Assemble result ──────────────────────────────────────────────
        unique_edges: list[dict[str, Any]] = [
            {"source": s, "target": t, "relation": r} for s, t, r in edges
        ]

        # Persist nodes and edges to the shared memory store so sidebar
        # stats and the Knowledge Graph page stay in sync.
        for node in nodes:
            self.memory.add_graph_node(
                node["id"], node["label"],
                node.get("type", "concept"),
                node.get("group", "default"),
            )
        for edge in unique_edges:
            self.memory.upsert_graph_edge(
                edge["source"], edge["target"], edge.get("relation", "related_to"),
            )

        built_graph = {"nodes": nodes, "edges": unique_edges}
        primary_topic = (
            articles[0]["topics"][0]
            if articles and articles[0].get("topics")
            else "AI Agents"
        )
        mindmap = self._build_mindmap_from_graph(built_graph, primary_topic)

        # Simulate processing
        time.sleep(0.3)

        return {
            "graph": {
                "nodes": nodes,
                "edges": unique_edges,
                "total_nodes": len(nodes),
                "total_edges": len(unique_edges),
            },
            "mindmap": mindmap,
            "built_at": datetime.now().isoformat(),
        }

    def _build_graph_live(self, articles: list[dict[str, Any]]) -> dict[str, Any]:
        """Live mode: Use MCP tools to update the graph."""
        if not self.mcp:
            return self._build_graph_demo(articles)

        for article in articles:
            self.mcp.call_tool("add_to_graph", {
                "article_id": article.get("id", ""),
                "title": article.get("title", ""),
                "topics": article.get("topics", []),
                "related_articles": article.get("related_to", []),
            })

        # Get the full graph
        graph_result = self.mcp.call_tool("query_graph", {"query_type": "all"})

        # Generate mind map
        primary_topic = articles[0]["topics"][0] if articles and articles[0].get("topics") else "AI Agents"
        mindmap_result = self.mcp.call_tool("generate_mindmap", {
            "central_topic": primary_topic,
            "max_depth": 3,
        })

        return {
            "graph": graph_result.get("data", {}),
            "mindmap": mindmap_result.get("data", {}).get("mindmap", ""),
            "built_at": datetime.now().isoformat(),
        }

    def _generate_mindmap(self, central_topic: str) -> str:
        """Generate Mermaid.js mind map syntax from the knowledge graph."""
        if self.mcp:
            result = self.mcp.call_tool("generate_mindmap", {
                "central_topic": central_topic,
                "max_depth": 3,
            })
            if result.get("success"):
                return result["data"].get("mindmap", "")

        # Fallback: build mind map from memory store graph
        return self._build_mindmap_from_graph(self.memory.get_graph(), central_topic)

    def _build_mindmap_from_graph(self, graph: dict[str, Any],
                                    central_topic: str) -> str:
        """
        Build a Mermaid.js mind map from the given graph dict.

        Args:
            graph: Dict with 'nodes' and 'edges' keys.
            central_topic: The topic to center the mind map on.

        Returns:
            Mermaid.js mindmap syntax string.
        """
        nodes = {n["id"]: n for n in graph["nodes"]}
        edges = graph["edges"]

        # Build adjacency list
        adj: dict[str, list[tuple[str, str]]] = {}
        for edge in edges:
            src = edge["source"]
            tgt = edge["target"]
            rel = edge.get("relation", "related_to")
            adj.setdefault(src, []).append((tgt, rel))
            adj.setdefault(tgt, []).append((src, rel))

        # Find the topic node matching central_topic
        root_id = None
        root_label = central_topic
        for nid, node in nodes.items():
            if central_topic.lower() in node.get("label", "").lower():
                root_id = nid
                root_label = node["label"]
                break

        if not root_id:
            # Pick the most connected topic node
            max_degree = -1
            for nid in nodes:
                if nodes[nid].get("type") == "topic":
                    degree = sum(1 for e in edges
                                 if e["source"] == nid or e["target"] == nid)
                    if degree > max_degree:
                        max_degree = degree
                        root_id = nid
                        root_label = nodes[nid]["label"]

        if not root_id:
            return f"mindmap\n  root({central_topic})\n    (No connections yet)"

        # BFS to build mind map tree
        lines = ["mindmap"]
        visited = {root_id}
        root_label_clean = root_label.replace('"', "'")
        lines.append(f"  root({root_label_clean})")

        def add_level(parent_indent: str, node_id: str, depth: int) -> None:
            if depth >= 4:  # Max depth for readability
                return
            children = []
            for neighbor, rel in adj.get(node_id, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    label = nodes.get(neighbor, {}).get("label", neighbor)
                    label = label.replace('"', "'")[:50]
                    children.append((neighbor, label, rel))

            for _, label, _ in children[:8]:  # Limit children per node
                lines.append(f"{parent_indent}    {label}")
                # Go deeper for topic nodes only (not articles)
                # but for simplicity, stop at depth 3 for all

        add_level("  ", root_id, 1)

        return "\n".join(lines)

    def get_mindmap_for_topic(self, topic: str) -> str:
        """Get a Mermaid.js mind map centered on a specific topic."""
        return self._generate_mindmap(topic)

    def get_full_graph(self) -> dict[str, Any]:
        """Get the complete knowledge graph."""
        return self.memory.get_graph()
