"""
Agents Package — Personal Knowledge Concierge
==============================================
Multi-agent system implementing the ADK (Agent Development Kit) pattern.

Agents:
    - CoordinatorAgent: Orchestrates the pipeline, dispatches sub-agents
    - CuratorAgent: Fetches and scores articles from configured sources
    - SummarizerAgent: Generates TL;DR and detailed summaries
    - GraphBuilderAgent: Maintains the knowledge graph in memory

This package demonstrates the "Agent / Multi-agent System" course concept
with a coordinator + specialized sub-agent architecture.
"""

from .coordinator import CoordinatorAgent
from .curator import CuratorAgent
from .summarizer import SummarizerAgent
from .graph_builder import GraphBuilderAgent

__all__ = [
    "CoordinatorAgent",
    "CuratorAgent",
    "SummarizerAgent",
    "GraphBuilderAgent",
]
