"""
MCP Server Package — Personal Knowledge Concierge
==================================================
Implements the Model Context Protocol (MCP) server that exposes tools
for the agent system. This is one of the key course concepts demonstrated.

Tools exposed:
    - fetch_article: Retrieve article content from a URL
    - search_arxiv: Query ArXiv API by keyword
    - summarize_text: Generate summaries using the configured LLM
    - analyze_repo: Analyze a GitHub repository
    - add_to_graph: Add nodes/edges to the knowledge graph
    - query_graph: Query the knowledge graph
    - generate_mindmap: Generate Mermaid.js mind map syntax
    - search_memory: Search the reading history
"""

from .server import MCPServer, create_mcp_server

__all__ = ["MCPServer", "create_mcp_server"]
