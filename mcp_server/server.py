"""
MCP Server Implementation
==========================
Implements the Model Context Protocol (MCP) server for the Knowledge Concierge.

This server exposes tools that agents call to interact with external data sources
and the memory/graph store. It follows the MCP specification:
- Tools are registered with a name, description, and JSON Schema for inputs.
- Agents discover available tools and call them via the MCP client interface.
- Each tool returns structured output that the agent can reason about.

Course Concept: MCP Server
This module demonstrates the MCP (Model Context Protocol) course concept
by providing a standardized tool interface between the LLM agents and
external systems (APIs, memory store, graph database).
"""

import json
import re
from datetime import datetime
from typing import Any, Callable

from memory.memory_store import MemoryStore
from utils.config import Config
from utils.demo_data import (
    DEMO_ARTICLES,
    DEMO_GRAPH_EDGES,
    DEMO_GRAPH_NODES,
    DEMO_PREFERENCES,
    DEMO_READING_HISTORY,
)


class MCPTool:
    """
    Definition of a single MCP tool.

    Each tool has:
    - name: Unique identifier (e.g., 'fetch_article')
    - description: What the tool does
    - parameters: JSON Schema for the tool's input
    - handler: The Python function that implements the tool
    """

    def __init__(self, name: str, description: str,
                 parameters: dict[str, Any],
                 handler: Callable[..., dict[str, Any]]):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler

    def to_definition(self) -> dict[str, Any]:
        """Convert to OpenAI-compatible tool definition (used by LLM/ChatGPT)."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": list(self.parameters.keys()),
                },
            },
        }


class MCPServer:
    """
    MCP Server for the Knowledge Concierge.

    Exposes 8 tools covering article fetching, summarization, graph
    operations, and memory search. Agents discover and call these
    tools to interact with the outside world.

    In demo mode, tools return pre-loaded data for instant results.
    In live mode, tools make real API calls.
    """

    def __init__(self, memory_store: MemoryStore):
        self.memory = memory_store
        self._tools: dict[str, MCPTool] = {}
        self._register_all_tools()

    def _register_all_tools(self) -> None:
        """Register all available MCP tools."""
        self._register_tool(MCPTool(
            name="fetch_article",
            description="Fetch the full text content of an article from a URL.",
            parameters={
                "url": {
                    "type": "string",
                    "description": "The URL of the article to fetch.",
                },
            },
            handler=self._fetch_article,
        ))
        self._register_tool(MCPTool(
            name="search_arxiv",
            description="Search ArXiv for papers matching a keyword query.",
            parameters={
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'multi-agent reinforcement learning').",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 5).",
                },
            },
            handler=self._search_arxiv,
        ))
        self._register_tool(MCPTool(
            name="summarize_text",
            description="Generate a concise TL;DR and detailed summary of a text using the configured LLM.",
            parameters={
                "text": {
                    "type": "string",
                    "description": "The text content to summarize.",
                },
                "article_id": {
                    "type": "string",
                    "description": "Unique identifier for the article.",
                },
            },
            handler=self._summarize_text,
        ))
        self._register_tool(MCPTool(
            name="analyze_repo",
            description="Analyze a GitHub repository and generate a code walkthrough.",
            parameters={
                "repo_url": {
                    "type": "string",
                    "description": "GitHub repository URL to analyze.",
                },
            },
            handler=self._analyze_repo,
        ))
        self._register_tool(MCPTool(
            name="add_to_graph",
            description="Add nodes and edges to the knowledge graph.",
            parameters={
                "article_id": {
                    "type": "string",
                    "description": "Article ID to add as a node.",
                },
                "title": {
                    "type": "string",
                    "description": "Article title for the node label.",
                },
                "topics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Topic tags for this article.",
                },
                "related_articles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "IDs of related articles to create edges to.",
                },
            },
            handler=self._add_to_graph,
        ))
        self._register_tool(MCPTool(
            name="query_graph",
            description="Query the knowledge graph for nodes, edges, or neighborhood.",
            parameters={
                "query_type": {
                    "type": "string",
                    "enum": ["all", "node", "neighbors", "topics"],
                    "description": "Type of query to run.",
                },
                "node_id": {
                    "type": "string",
                    "description": "Node ID (required for 'node' and 'neighbors' queries).",
                },
            },
            handler=self._query_graph,
        ))
        self._register_tool(MCPTool(
            name="generate_mindmap",
            description="Generate a Mermaid.js mind map from the knowledge graph.",
            parameters={
                "central_topic": {
                    "type": "string",
                    "description": "The central topic for the mind map (e.g., 'AI Agents').",
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth of the mind map tree (default: 3).",
                },
            },
            handler=self._generate_mindmap,
        ))
        self._register_tool(MCPTool(
            name="search_memory",
            description="Search the reading history for articles matching a query.",
            parameters={
                "query": {
                    "type": "string",
                    "description": "Search query string.",
                },
            },
            handler=self._search_memory,
        ))
        self._register_tool(MCPTool(
            name="search_github_trending",
            description="Search GitHub trending repositories for a given topic.",
            parameters={
                "topic": {
                    "type": "string",
                    "description": "Topic or keyword to search for (e.g., 'AI agents', 'LLM').",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5).",
                },
            },
            handler=self._search_github_trending,
        ))
        self._register_tool(MCPTool(
            name="search_hacker_news",
            description="Search Hacker News for stories matching a query via Algolia HN API.",
            parameters={
                "query": {
                    "type": "string",
                    "description": "Search query for Hacker News.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5).",
                },
            },
            handler=self._search_hacker_news,
        ))
        self._register_tool(MCPTool(
            name="search_web",
            description="Search the web for articles matching a query (uses a free search API).",
            parameters={
                "query": {
                    "type": "string",
                    "description": "Search query string.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5).",
                },
            },
            handler=self._search_web,
        ))
        self._register_tool(MCPTool(
            name="recommend_sources",
            description="Recommend information sources based on user interests. "
                        "Returns both pre-defined sources and LLM/web-generated suggestions.",
            parameters={
                "interests": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "User's interest topics to base recommendations on.",
                },
                "recommendation_type": {
                    "type": "string",
                    "enum": ["llm", "web", "both"],
                    "description": "Whether to use LLM-based, web-query-based, or both types of recommendations.",
                },
            },
            handler=self._recommend_sources,
        ))

        self._register_tool(MCPTool(
            name="judge_articles",
            description="Use LLM-as-a-Judge to score and rank candidate articles "
                        "against user interests. Returns scored articles with "
                        "reasoning and verdict (relevant / not_relevant).",
            parameters={
                "articles": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "title": {"type": "string"},
                            "topics": {"type": "array", "items": {"type": "string"}},
                            "summary": {"type": "string"},
                            "source": {"type": "string"},
                        },
                    },
                    "description": "Candidate articles to judge (max ~20).",
                },
                "interests": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "User interests to judge relevance against.",
                },
            },
            handler=self._judge_articles,
        ))

    def _register_tool(self, tool: MCPTool) -> None:
        """Register a tool in the server."""
        self._tools[tool.name] = tool

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get all tool definitions (for passing to the LLM)."""
        return [t.to_definition() for t in self._tools.values()]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Call a tool by name with the given arguments.

        Args:
            name: Tool name (e.g., 'fetch_article').
            arguments: Dict of parameter values.

        Returns:
            Tool result dict with 'success' and 'data' keys.
        """
        tool = self._tools.get(name)
        if not tool:
            return {"success": False, "error": f"Unknown tool: {name}"}

        try:
            result = tool.handler(**arguments)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Tool Handlers ─────────────────────────────────────────────────────

    def _fetch_article(self, url: str) -> dict[str, Any]:
        """Fetch article content from a URL."""
        if Config.DEMO_MODE:
            # Return a demo article if the URL matches
            for article in DEMO_ARTICLES:
                if article["source_url"] in url or article["id"] in url:
                    return article
            # Return first article as fallback demo
            return DEMO_ARTICLES[0]

        # Live mode: actually fetch the URL
        import requests
        from bs4 import BeautifulSoup

        response = requests.get(url, timeout=10, headers={
            "User-Agent": "KnowledgeConcierge/1.0 (Hackathon Demo)"
        })
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # Extract main text (simple heuristic)
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return {
            "url": url,
            "content": text[:5000],  # Truncate for LLM context
            "content_length": len(text),
            "fetched_at": datetime.now().isoformat(),
        }

    def _search_arxiv(self, query: str, max_results: int = 5) -> dict[str, Any]:
        """Search ArXiv for papers."""
        if Config.DEMO_MODE:
            # Filter demo articles by query relevance
            query_lower = query.lower()
            results = []
            for article in DEMO_ARTICLES:
                if article["source"] == "ArXiv":
                    topics_str = " ".join(article["topics"]).lower()
                    if (query_lower in article["title"].lower() or
                            query_lower in topics_str):
                        results.append(article)
            return {
                "query": query,
                "results": results[:max_results],
                "total_found": len(results),
                "source": "demo_data",
            }

        # Live mode: call ArXiv API
        import requests
        import xml.etree.ElementTree as ET

        base_url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        response = requests.get(base_url, params=params, timeout=15)
        # Parse Atom XML response
        root = ET.fromstring(response.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        results = []
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            results.append({
                "title": title.text.strip() if title is not None else "Untitled",
                "summary": (summary.text or "")[:500] if summary is not None else "",
                "source": "ArXiv",
                "source_url": entry.find("atom:id", ns).text if entry.find("atom:id", ns) is not None else "",
            })

        return {
            "query": query,
            "results": results,
            "total_found": len(results),
            "source": "arxiv_api",
        }

    def _summarize_text(self, text: str, article_id: str) -> dict[str, Any]:
        """Summarize text content."""
        if Config.DEMO_MODE:
            # Return pre-loaded summary if available
            for article in DEMO_ARTICLES:
                if article["id"] == article_id:
                    return {
                        "article_id": article_id,
                        "tl_dr": article["tl_dr"],
                        "detailed_summary": article["full_summary"],
                        "word_count": len(text.split()) if text else 0,
                        "source": "demo_data",
                    }

        # Live mode: use LLM to summarize
        from utils.llm_client import LLMClient
        llm = LLMClient()
        tl_dr = llm.summarize(text, max_length=100)
        detailed = llm.generate(
            system_prompt=(
                "You are an expert at creating detailed, well-structured summaries. "
                "Write a comprehensive summary with the following structure:\n"
                "## Key Findings\n- Bullet points of main findings\n"
                "## Methods\n- Brief description of approach\n"
                "## Significance\n- Why this matters\n"
                "Use markdown formatting."
            ),
            user_message=f"Summarize this content:\n\n{text[:6000]}",
            max_tokens=800,
        )
        return {
            "article_id": article_id,
            "tl_dr": tl_dr,
            "detailed_summary": detailed,
            "word_count": len(text.split()) if text else 0,
            "source": "llm_api",
        }

    def _analyze_repo(self, repo_url: str) -> dict[str, Any]:
        """Analyze a GitHub repository."""
        if Config.DEMO_MODE:
            # Return a demo repo analysis
            for article in DEMO_ARTICLES:
                if article["source"] == "GitHub Trending" and \
                   repo_url in article.get("source_url", ""):
                    return {
                        "repo_url": repo_url,
                        "walkthrough": article["full_summary"],
                        "source": "demo_data",
                    }

        # Live mode would use GitHub API
        return {
            "repo_url": repo_url,
            "walkthrough": "Live repo analysis requires GitHub API integration. "
                          "Enable DEMO_MODE for pre-loaded walkthroughs.",
            "source": "stub",
        }

    def _add_to_graph(self, article_id: str, title: str,
                      topics: list[str], related_articles: list[str]) -> dict[str, Any]:
        """Add article and topics to the knowledge graph."""
        # Add article node
        self.memory.add_graph_node(
            node_id=article_id,
            label=title,
            node_type="article",
            group=topics[0] if topics else "default",
            metadata={"topics": topics},
        )

        # Add topic nodes and edges
        for topic in topics:
            topic_id = f"topic-{topic.lower().replace(' ', '-').replace('&', 'and')}"
            self.memory.add_graph_node(
                node_id=topic_id,
                label=topic,
                node_type="topic",
                group="core",
            )
            self.memory.upsert_graph_edge(article_id, topic_id, "about")

        # Add edges to related articles
        for related_id in related_articles:
            self.memory.upsert_graph_edge(article_id, related_id, "related_to")

        return {
            "added_nodes": 1 + len(topics),
            "added_edges": len(topics) + len(related_articles),
        }

    def _query_graph(self, query_type: str,
                     node_id: str = "") -> dict[str, Any]:
        """Query the knowledge graph."""
        graph = self.memory.get_graph()

        if query_type == "all":
            return graph

        if query_type == "node" and node_id:
            for node in graph["nodes"]:
                if node["id"] == node_id:
                    return {"node": node}

        if query_type == "neighbors" and node_id:
            neighbors = []
            for edge in graph["edges"]:
                if edge["source"] == node_id:
                    neighbors.append({"node": edge["target"], "relation": edge["relation"]})
                elif edge["target"] == node_id:
                    neighbors.append({"node": edge["source"], "relation": edge["relation"]})
            return {"node_id": node_id, "neighbors": neighbors}

        if query_type == "topics":
            topics = [
                node for node in graph["nodes"]
                if node.get("type") == "topic"
            ]
            return {"topics": topics}

        return {"error": f"Unknown query type: {query_type}"}

    def _generate_mindmap(self, central_topic: str,
                          max_depth: int = 3) -> dict[str, Any]:
        """
        Generate Mermaid.js mind map syntax from the knowledge graph.

        The mind map is a tree-structured visualization starting from
        a central topic and branching out to related articles and concepts.
        """
        graph = self.memory.get_graph()
        nodes = {n["id"]: n for n in graph["nodes"]}
        edges = graph["edges"]

        # Find the central topic node
        central_id = None
        for nid, node in nodes.items():
            if central_topic.lower() in node.get("label", "").lower():
                central_id = nid
                break

        if not central_id:
            # Use the first topic as center
            for nid, node in nodes.items():
                if node.get("type") == "topic":
                    central_id = nid
                    break

        if not central_id:
            return {"mindmap": "mindmap\n  root(No data available)"}

        # Build adjacency for BFS
        adj: dict[str, list[tuple[str, str]]] = {}
        for edge in edges:
            src, tgt, rel = edge["source"], edge["target"], edge["relation"]
            adj.setdefault(src, []).append((tgt, rel))
            adj.setdefault(tgt, []).append((src, rel))

        # BFS to build the mind map tree
        mermaid_lines = ["mindmap"]
        visited = {central_id}
        root_label = nodes[central_id]["label"].replace('"', "'")

        # Level 1: direct connections
        level1 = []
        for neighbor, rel in adj.get(central_id, []):
            if neighbor not in visited:
                visited.add(neighbor)
                label = nodes.get(neighbor, {}).get("label", neighbor).replace('"', "'")
                level1.append((neighbor, label, rel, 1))

        mermaid_lines.append(f"  {root_label}")

        # Build tree recursively
        def add_children(parent_indent: str, children: list,
                         current_depth: int) -> None:
            if current_depth > max_depth:
                return
            for child_id, child_label, child_rel, _ in children:
                mermaid_lines.append(f"{parent_indent}    {child_label}")
                # Get grandchildren
                grandchildren = []
                for neighbor, rel in adj.get(child_id, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        label = nodes.get(neighbor, {}).get("label", neighbor).replace('"', "'")
                        grandchildren.append((neighbor, label, rel, current_depth + 1))
                add_children(parent_indent + "    ", grandchildren, current_depth + 1)

        add_children("  ", level1, 1)

        return {
            "mindmap": "\n".join(mermaid_lines),
            "central_topic": central_topic,
            "total_nodes_visited": len(visited),
        }

    def _search_memory(self, query: str) -> dict[str, Any]:
        """Search the reading history."""
        results = self.memory.search_readings(query)
        return {
            "query": query,
            "results": results[:10],
            "total_found": len(results),
        }

    def _search_github_trending(self, topic: str, max_results: int = 5) -> dict[str, Any]:
        """Search GitHub trending repositories for a topic."""
        if Config.DEMO_MODE:
            # Return demo GitHub articles that match the topic
            results = []
            topic_lower = topic.lower()
            for article in DEMO_ARTICLES:
                if article["source"] == "GitHub Trending":
                    text = (article["title"] + " " + " ".join(article["topics"])).lower()
                    if any(tok in text for tok in topic_lower.split()):
                        results.append(article)
            return {
                "topic": topic,
                "results": results[:max_results],
                "total_found": len(results),
                "source": "demo_data",
            }

        # Live mode: call GitHub search API
        import requests
        try:
            resp = requests.get(
                "https://api.github.com/search/repositories",
                params={"q": topic, "sort": "stars", "order": "desc",
                        "per_page": max_results},
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "KnowledgeConcierge/1.0",
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("full_name", "Unknown repo"),
                    "summary": item.get("description", "") or "",
                    "source_url": item.get("html_url", ""),
                    "topics": item.get("topics", [topic]),
                    "date": item.get("updated_at", "")[:10],
                })
            return {
                "topic": topic,
                "results": results,
                "total_found": len(results),
                "source": "github_api",
            }
        except Exception as e:
            return {"topic": topic, "results": [], "total_found": 0,
                    "error": str(e), "source": "github_api"}

    def _search_hacker_news(self, query: str, max_results: int = 5) -> dict[str, Any]:
        """Search Hacker News via Algolia API."""
        if Config.DEMO_MODE:
            return {
                "query": query,
                "results": [],
                "total_found": 0,
                "source": "demo_data",
                "note": "Hacker News search is live-only. Enable live mode and add an API key.",
            }

        # Live mode: call HN Algolia API (free, no auth required)
        import requests
        try:
            resp = requests.get(
                "https://hn.algolia.com/api/v1/search",
                params={"query": query, "hitsPerPage": max_results,
                        "tags": "story"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("hits", []):
                results.append({
                    "title": item.get("title", "Untitled"),
                    "summary": (item.get("story_text") or item.get("comment_text", ""))[:300],
                    "source_url": item.get("url") or f"https://news.ycombinator.com/item?id={item.get('objectID')}",
                    "date": item.get("created_at", "")[:10],
                })
            return {
                "query": query,
                "results": results,
                "total_found": len(results),
                "source": "hn_algolia_api",
            }
        except Exception as e:
            return {"query": query, "results": [], "total_found": 0,
                    "error": str(e), "source": "hn_algolia_api"}

    def _search_web(self, query: str, max_results: int = 5) -> dict[str, Any]:
        """Search the web for articles matching a query."""
        if Config.DEMO_MODE:
            # In demo mode, filter demo articles by query
            results = []
            query_lower = query.lower()
            for article in DEMO_ARTICLES:
                text = (article["title"] + " " + " ".join(article["topics"])).lower()
                if any(tok in text for tok in query_lower.split()):
                    results.append(article)
            return {
                "query": query,
                "results": results[:max_results],
                "total_found": len(results),
                "source": "demo_data",
            }

        # Live mode: use a free web search (DuckDuckGo HTML, no API key needed)
        import requests
        try:
            resp = requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "KnowledgeConcierge/1.0"},
                timeout=10,
            )
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            results = []
            for r in soup.select(".result")[:max_results]:
                title_el = r.select_one(".result__title")
                snippet_el = r.select_one(".result__snippet")
                link_el = r.select_one(".result__url")
                if title_el:
                    results.append({
                        "title": title_el.get_text(strip=True),
                        "summary": snippet_el.get_text(strip=True) if snippet_el else "",
                        "source_url": link_el.get_text(strip=True) if link_el else "",
                    })
            return {
                "query": query,
                "results": results,
                "total_found": len(results),
                "source": "web_search",
            }
        except Exception as e:
            return {"query": query, "results": [], "total_found": 0,
                    "error": str(e), "source": "web_search"}

    def _judge_articles(self, articles: list[dict[str, Any]],
                        interests: list[str]) -> dict[str, Any]:
        """
        LLM-as-a-Judge: Score and rank candidate articles against user interests.

        Packages the articles + interests into a prompt, sends to the LLM,
        and parses the structured JSON response. Falls back to simple keyword
        scoring when the LLM is unavailable.
        """
        if not articles:
            return {"scored": [], "method": "empty"}

        # Try LLM judge
        if Config.is_live_mode():
            try:
                from utils.llm_client import LLMClient
                llm = LLMClient()
                if llm.is_available():
                    return self._llm_judge(llm, articles, interests)
            except Exception:
                pass

        # Fallback: simple keyword scoring
        return self._fallback_judge(articles, interests)

    def _llm_judge(self, llm, articles: list[dict[str, Any]],
                   interests: list[str]) -> dict[str, Any]:
        """Use LLM to judge article relevance."""
        # Build a compact candidate list for the prompt
        candidates_text = []
        for i, a in enumerate(articles):
            candidates_text.append(
                f"[{i}] id={a.get('id','')} | source={a.get('source','')}\n"
                f"    title: {a.get('title','')}\n"
                f"    topics: {', '.join(a.get('topics',[]))}\n"
                f"    summary: {(a.get('summary') or a.get('tl_dr') or '')[:200]}"
            )

        prompt = (
            f"You are a relevance judge for a personal knowledge concierge.\n\n"
            f"## User Interests\n{', '.join(interests)}\n\n"
            f"## Candidate Articles\n" + "\n".join(candidates_text) + "\n\n"
            f"## Task\n"
            f"For each article, decide if it's RELEVANT or NOT_RELEVANT to the user's interests.\n"
            f"Assign a relevance score from 0.0 to 1.0.\n"
            f"Provide a one-sentence reason for your verdict.\n\n"
            f"Output a JSON array with keys: id_index (int), verdict (relevant|not_relevant), "
            f"score (float 0-1), reason (string).\n"
            f"Only include articles that are at least somewhat relevant (score >= 0.15).\n"
            f"Sort by score descending.\n\n"
            f"IMPORTANT: Output valid JSON only. No markdown, no explanation."
        )

        try:
            response = llm.generate(
                system_prompt="You are an expert at judging content relevance. "
                              "Output valid JSON arrays only. No markdown.",
                user_message=prompt,
                max_tokens=1200,
                temperature=0.3,
            )
        except Exception:
            return self._fallback_judge(articles, interests)

        # Parse JSON from response
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if not json_match:
            return self._fallback_judge(articles, interests)

        try:
            judged = json.loads(json_match.group())
        except json.JSONDecodeError:
            return self._fallback_judge(articles, interests)

        # Map back to article IDs
        scored = []
        for entry in judged:
            idx = entry.get("id_index", -1)
            if 0 <= idx < len(articles):
                scored.append({
                    "id": articles[idx].get("id", ""),
                    "verdict": entry.get("verdict", "relevant"),
                    "score": round(entry.get("score", 0.5), 3),
                    "reason": entry.get("reason", ""),
                })

        return {"scored": scored, "method": "llm_judge"}

    @staticmethod
    def _fallback_judge(articles: list[dict[str, Any]],
                        interests: list[str]) -> dict[str, Any]:
        """Token-level keyword matching fallback when LLM is unavailable."""
        # Tokenize interests (reuse the same logic as the curator fallback)
        stop = {"a","an","the","for","and","of","in","on","to","with",
                "by","at","from","is","or","as","it","be","are","was",
                "were","been","its","that","this","these","those"}
        interest_tokens: set[str] = set()
        for i in interests:
            for t in re.findall(r"[a-zA-Z0-9]+", i.lower()):
                if len(t) > 1 and t not in stop:
                    interest_tokens.add(t)

        scored = []
        for a in articles:
            title = a.get("title", "").lower()
            topics_str = " ".join(a.get("topics", [])).lower()
            summary = (a.get("summary") or a.get("tl_dr") or "").lower()
            text = title + " " + topics_str + " " + summary

            # Token overlap
            text_tokens = set(re.findall(r"[a-zA-Z0-9]+", text))
            overlap = interest_tokens & text_tokens
            token_score = len(overlap) / max(1, len(interest_tokens))

            # Substring bonus
            substr_score = 0.0
            for interest in [i.lower() for i in interests]:
                if interest in title:
                    substr_score += 0.40
                elif interest in topics_str:
                    substr_score += 0.30
                elif any(w in text for w in interest.split() if len(w) > 3):
                    substr_score += 0.15

            score = min(1.0, token_score * 0.6 + substr_score * 0.4)
            verdict = "relevant" if score >= 0.15 else "not_relevant"

            scored.append({
                "id": a.get("id", ""),
                "verdict": verdict,
                "score": round(score, 3),
                "reason": f"Keyword match: {len(overlap)} token(s) — {', '.join(sorted(overlap)[:5])}",
            })

        scored.sort(key=lambda s: s["score"], reverse=True)
        return {"scored": scored, "method": "fallback_keyword"}

    def _recommend_sources(self, interests: list[str],
                          recommendation_type: str = "both") -> dict[str, Any]:
        """
        Recommend information sources based on user interests.

        Uses LLM-as-a-Judge: sends the 8 catalog sources + user interests
        to the LLM for ranking. Also provides web-query results (real-time
        search) and LLM-generated new-source suggestions.
        """
        # ── 1. Catalog sources (8 items, no complex scoring) ───────────
        catalog = [
            {"name": "ArXiv", "url": "https://arxiv.org",
             "description": "Pre-print research papers — deep technical topics"},
            {"name": "GitHub Trending", "url": "https://github.com/trending",
             "description": "Popular open-source repositories — code & tools"},
            {"name": "Hacker News", "url": "https://news.ycombinator.com",
             "description": "Tech community news & discussion — industry trends"},
            {"name": "Medium / Towards Data Science",
             "url": "https://medium.com/tag/artificial-intelligence",
             "description": "Blog platform — tutorials & explainers"},
            {"name": "Papers With Code", "url": "https://paperswithcode.com",
             "description": "Research papers with implementations — ML/AI"},
            {"name": "Semantic Scholar", "url": "https://www.semanticscholar.org",
             "description": "AI-powered academic search — literature review"},
            {"name": "Reddit r/MachineLearning",
             "url": "https://reddit.com/r/MachineLearning",
             "description": "Community discussions — ML/AI pulse"},
            {"name": "arXiv Sanity Preserver",
             "url": "https://arxiv-sanity-lite.com",
             "description": "Personalized ArXiv recommender — staying current"},
        ]

        # Use LLM-as-judge to rank catalog sources by interest relevance
        scored_predefined = self._judge_sources_with_llm(catalog, interests)

        result: dict[str, Any] = {
            "interests": interests,
            "predefined_sources": scored_predefined,
            "llm_recommendations": [],
            "web_recommendations": [],
        }

        # ── 2. LLM-generated new-source suggestions ───────────────────
        if recommendation_type in ("llm", "both"):
            result["llm_recommendations"] = self._llm_suggest_sources(interests)

        # ── 3. Web-query discovery ────────────────────────────────────
        if recommendation_type in ("web", "both"):
            result["web_recommendations"] = self._web_discover_sources(interests)

        return result

    def _judge_sources_with_llm(self, catalog: list[dict[str, Any]],
                                interests: list[str]) -> list[dict[str, Any]]:
        """LLM-as-Judge: rank catalog sources by relevance to interests."""
        # Try LLM
        if Config.is_live_mode():
            try:
                from utils.llm_client import LLMClient
                llm = LLMClient()
                if llm.is_available():
                    src_list = "\n".join(
                        f"[{i}] {s['name']} — {s['description']}"
                        for i, s in enumerate(catalog)
                    )
                    prompt = (
                        f"User interests: {', '.join(interests)}\n\n"
                        f"Information sources:\n{src_list}\n\n"
                        f"Rank these sources by relevance to the user's interests. "
                        f"For each source, assign a score 0.0-1.0 and a 1-sentence reason.\n"
                        f"Output JSON array: [{{\"index\": int, \"score\": float, \"reason\": str}}]\n"
                        f"Sort by score descending. Output valid JSON only, no markdown."
                    )
                    resp = llm.generate(
                        system_prompt="You are a research librarian. Output valid JSON only.",
                        user_message=prompt, max_tokens=600, temperature=0.3,
                    )
                    json_match = re.search(r'\[.*\]', resp, re.DOTALL)
                    if json_match:
                        judged = json.loads(json_match.group())
                        scored = []
                        for entry in judged:
                            idx = entry.get("index", -1)
                            if 0 <= idx < len(catalog):
                                scored.append({
                                    **catalog[idx],
                                    "relevance_score": round(entry.get("score", 0.5), 2),
                                    "judge_reason": entry.get("reason", ""),
                                    "type": "predefined",
                                })
                        if scored:
                            return sorted(scored,
                                         key=lambda s: s["relevance_score"], reverse=True)
            except Exception:
                pass

        # Fallback: simple interest-word match
        interests_flat = " ".join(interests).lower()
        for s in catalog:
            score = 0.3
            for word in interests_flat.split():
                if len(word) > 3 and (word in s["name"].lower()
                                       or word in s["description"].lower()):
                    score += 0.2
            s["relevance_score"] = round(min(1.0, score), 2)
            s["type"] = "predefined"
        return sorted(catalog, key=lambda s: s["relevance_score"], reverse=True)

    def _llm_suggest_sources(self, interests: list[str]) -> list[dict[str, Any]]:
        """LLM generates new source suggestions beyond the catalog."""
        has_key = bool(Config.API_KEY and
                      Config.API_KEY not in ("", "sk-your-api-key"))
        if not has_key:
            return [{"name": "Set a valid API_KEY in .env",
                     "type": "info",
                     "description": "LLM-based source suggestions require a valid API key."}]

        try:
            from utils.llm_client import LLMClient
            llm = LLMClient()
            if not llm.is_available():
                return [{"name": "LLM unavailable", "type": "info",
                         "description": "Check API_KEY configuration."}]

            prompt = (
                f"User interests: {', '.join(interests)}\n\n"
                f"Recommend 5 specific, niche information sources (websites, newsletters, "
                f"journals, podcasts, blogs, data providers). For each: name, url (if known), "
                f"type, and a one-sentence relevance reason.\n"
                f"Output JSON: [{{\"name\": str, \"url\": str, \"type\": str, \"description\": str}}]"
            )
            resp = llm.generate(
                system_prompt="You are an expert research librarian. Output valid JSON only.",
                user_message=prompt, max_tokens=600, temperature=0.5,
            )
            json_match = re.search(r'\[.*\]', resp, re.DOTALL)
            if json_match:
                sources = json.loads(json_match.group())
                for s in sources:
                    s["type"] = "llm_recommended"
                    s["relevance_score"] = 0.9
                return sources
            return [{"name": "LLM response", "type": "llm_raw",
                     "description": resp[:300]}]
        except Exception as e:
            return [{"name": "LLM error", "type": "error", "description": str(e)}]

    def _web_discover_sources(self, interests: list[str]) -> list[dict[str, Any]]:
        """Web search for relevant sources (free, no API key needed)."""
        try:
            query = f"best information sources for {interests[0] if interests else 'AI'}"
            import requests as _requests
            resp = _requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "KnowledgeConcierge/1.0"},
                timeout=10,
            )
            from bs4 import BeautifulSoup as _BS
            soup = _BS(resp.text, "html.parser")
            web_recs = []
            for r in soup.select(".result")[:5]:
                title_el = r.select_one(".result__title")
                snippet_el = r.select_one(".result__snippet")
                link_el = r.select_one(".result__url")
                if title_el:
                    web_recs.append({
                        "name": title_el.get_text(strip=True)[:100],
                        "url": link_el.get_text(strip=True) if link_el else "",
                        "description": snippet_el.get_text(strip=True)[:200] if snippet_el else "",
                        "type": "web_recommended", "relevance_score": 0.7,
                    })
            if web_recs:
                return web_recs
        except Exception:
            pass
        # Fallback
        return self._build_fallback_web_recs(interests)

    @staticmethod
    def _build_fallback_web_recs(interests: list[str]) -> list[dict[str, Any]]:
        """Build smart fallback web recommendations when DuckDuckGo is unreachable."""
        interest_str = " ".join(interests).lower()
        recs: list[dict[str, Any]] = []

        # Map common topics to well-known sources.
        # Each entry: (keywords_tuple, sources_list)
        source_map: list[tuple[tuple[str, ...], list[tuple[str, str, str]]]] = [
            (("AI", "ml", "machine learning", "deep learning"),
             [("ArXiv AI", "https://arxiv.org/list/cs.AI/recent", "Latest AI research papers"),
              ("Papers With Code", "https://paperswithcode.com", "ML papers with implementations"),
              ("Hugging Face Daily Papers", "https://huggingface.co/papers", "Community-curated ML papers"),
              ("The Gradient", "https://thegradient.pub", "Long-form AI essays & analysis"),
              ("Import AI", "https://importai.substack.com", "Weekly AI newsletter by Jack Clark")]),
            (("agent", "agents"),
             [("Agent AI Newsletter", "https://agent.ai", "Agent-focused news and resources"),
              ("LangChain Blog", "https://blog.langchain.dev", "Agent framework tutorials & updates"),
              ("CrewAI Blog", "https://blog.crewai.com", "Multi-agent system patterns")]),
            (("finance", "trading", "quantitative", "quant"),
             [("Quantocracy", "https://quantocracy.com", "Daily quant finance aggregator"),
              ("QuantStart", "https://www.quantstart.com", "Quantitative trading tutorials"),
              ("SSRN Quantitative Finance", "https://ssrn.com/en/index.cfm/quantitative-finance", "Pre-print quant finance papers"),
              ("Quantopian Lectures", "https://www.quantopian.com/lectures", "Quant finance education")]),
            (("data science", "datascience", "data engineering"),
             [("Towards Data Science", "https://towardsdatascience.com", "Data science blog"),
              ("Data Elixir", "https://dataelixir.com", "Weekly data science newsletter"),
              ("KDnuggets", "https://www.kdnuggets.com", "Data science news & tutorials")]),
            (("llm", "language model", "gpt", "transformer"),
             [("The Batch (DeepLearning.AI)", "https://www.deeplearning.ai/the-batch", "Weekly AI newsletter by Andrew Ng"),
              ("Lil'Log", "https://lilianweng.github.io", "Deep technical ML/AI posts"),
              ("Sebastian Raschka Blog", "https://sebastianraschka.com/blog.html", "ML research explained")]),
            (("python", "code", "programming"),
             [("PyCoder's Weekly", "https://pycoders.com", "Weekly Python newsletter"),
              ("Real Python", "https://realpython.com", "Python tutorials"),
              ("GitHub Trending", "https://github.com/trending/python", "Trending Python repos")]),
        ]

        matched_sources: dict[str, dict[str, Any]] = {}
        for keywords, sources in source_map:
            if any(kw in interest_str for kw in keywords):
                for name, url, desc in sources:
                    if name not in matched_sources:
                        matched_sources[name] = {
                            "name": name, "url": url, "description": desc,
                            "type": "web_recommended", "relevance_score": 0.75,
                        }

        recs = list(matched_sources.values())

        # Always add a few general high-quality sources
        if len(recs) < 3:
            general = [
                ("Google Scholar Alerts", "https://scholar.google.com",
                 "Set alerts for your topics to get email updates on new papers"),
                ("Substack", "https://substack.com/search",
                 f"Search Substack for newsletters about {interests[0] if interests else 'your topic'}"),
                ("Reddit", f"https://reddit.com/search/?q={'+'.join(interests[:2])}",
                 "Community discussions on your interests"),
            ]
            for name, url, desc in general:
                if name not in matched_sources:
                    recs.append({
                        "name": name, "url": url, "description": desc,
                        "type": "web_recommended", "relevance_score": 0.5,
                    })

        return recs[:6]


def create_mcp_server(memory_store: MemoryStore = None) -> MCPServer:
    """
    Factory function to create a configured MCP server.

    Args:
        memory_store: MemoryStore instance. Creates a new one if not provided.

    Returns:
        Configured MCPServer instance.
    """
    if memory_store is None:
        memory_store = MemoryStore()
    return MCPServer(memory_store)
