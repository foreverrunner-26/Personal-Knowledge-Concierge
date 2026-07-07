# 🧠 Personal Knowledge Concierge

**A privacy-first, multi-agent system that curates, digests, and maps daily reading.**

> **Submission for:** Kaggle 5-Day AI Agents: Intensive Vibe Coding Capstone Project <br>
> **Track:** Concierge Agents

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.58+-red)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

---

## 📖 Table of Contents
- [The Pitch](#the-pitch)
- [System Architecture](#system-architecture)
- [Core Features](#core-features)
- [Course Concepts Demonstrated](#course-concepts-demonstrated)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)

---

## The Pitch

### Problem
Knowledge workers face an unsustainable volume of information. Hundreds of papers, repositories, and articles are published daily. **Information overload** becomes a major issue: hours wasted filtering noise, fragmented reading histories, and missed connections between critical concepts.

### Solution
**Personal Knowledge Concierge** is a privacy-first AI agent acting as your personal research assistant. It solves this by operating in four autonomous stages:
1. **Curate:** Monitors specified sources (ArXiv, GitHub...) for your exact interests.
2. **Digest:** Generates structural summaries and actionable walkthroughs of complex content.
3. **Map:** Logs processed materials into a persistent local memory base.
4. **Synthesize:** Transforms reading history into queryable knowledge graphs.

### Why Agents?

Traditional RSS readers only fetch links. An agentic system uniquely solves this problem by **reasoning** about an article's true relevance, **synthesizing** context across multiple sources, and autonomously **structuring** the output into an evolving knowledge graph.

---

## System Architecture

The system utilizes a multi-agent topology orchestrated by a central Coordinator.

```text
┌──────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                    │
│    (Sidebar navigation · Live log monitor · Dark UI)     │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│                 Coordinator Agent (ADK)                  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │   Curator   │─▶│  Summarizer  │─▶│  Graph Builder  │ │
│  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘ │
└─────────┼────────────────┼───────────────────┼───────────┘
          │                │                   │
┌─────────▼────────────────▼───────────────────▼───────────┐
│                    MCP Server (8 Tools)                  │
│ [fetch_article] [search_arxiv] [summarize] [build_graph] │
│ [analyze_repo] [query_graph] [generate_mindmap]          │
│ [search_memory] [recommend_sources]                      │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│                     Data Layer                           │
│  [Local JSON Memory]  [Mermaid.js Mind Maps]             │
│  [vis.js Knowledge Graph]  [Agent Workflow Logs]         │
└──────────────────────────────────────────────────────────┘
```

---

## Core Features

- 🎛️ **Dynamic Interest Configuration:** Track customized topics across multiple trusted data sources. Add, remove, and save interests and source preferences from the sidebar.
- 📰 **Automated Daily Briefings:** One-click pipeline runs Curator → Summarizer → Graph Builder. Master-detail layout shows article cards with inline TL;DR on the left, full digest on the right.
- 🗺️ **Interactive Knowledge Graph:** Explore connections across your reading history in three views — interactive vis.js network graph (drag, zoom, freeze physics), zoomable Mermaid mind maps, and graph statistics. Export as JSON.
- 📚 **Searchable Reading History:** Full-text search across all processed articles with source filtering. Expand any entry to see complete digest in-place.
- 🔍 **Source Discovery:** Built-in `sources_recommendation` skill lets agents discover new trusted sources for any topic — via LLM knowledge or web search — and suggest them to the user.
- 🟢 **Real-Time Agent Monitor:** Live log panel in the sidebar shows every pipeline stage, LLM API call, MCP tool invocation, and error in real time — color-coded by type (LLM, TOOL, INFO, ERROR).
- 🛡️ **Privacy-First Storage:** Reading histories and graphs are stored locally. Demo and live modes use separate memory files to prevent data cross-contamination.
- 🧭 **Unified Sidebar Navigation:** All pages (Interests, Daily Briefing, Knowledge Graph, History, About) accessible from a single sidebar with active-state highlighting and compact memory stats.

---

## Course Concepts Demonstrated

This project explicitly implements key requirements from the Kaggle AI Agents course:

1. **Agent / Multi-agent System (ADK):** Implements a pipeline pattern. The `CoordinatorAgent` orchestrates three specialized sub-agents (`Curator`, `Summarizer`, `GraphBuilder`), enforcing single-responsibility principles. Each stage's progress is streamed to the live log panel.
2. **MCP Server:** A centralized Model Context Protocol server exposes 8 standardized tools for external data fetching and memory writing, strictly validated via JSON schemas. Agents discover and call tools at runtime.
3. **Agent Skills:** Four composable `SKILL.md` files grant agents isolated capabilities with defined system prompts and expected schemas:
   - `summarize.md` — Article summarization with TL;DR and detailed digests
   - `code_walkthrough.md` — GitHub repository analysis and architecture walkthroughs
   - `mindmap.md` — Knowledge graph visualization with Mermaid.js
   - `sources_recommendation.md` — Source discovery via LLM knowledge or web search
4. **Vibe Coding:** Developed using Claude Code as the primary agentic IDE, enabling rapid prototyping, TDD cycles, and seamless architectural iteration.
5. **Security Features:** Implements pre-commit secret scanning, strict environment variable isolation, and JSON schema validation for all agent tool inputs.
6. **Deployability:** Fully containerized with a production-ready `Dockerfile`, configured for immediate deployment to Google Cloud Run or local execution.

---

## Quick Start

### 1. Local Demo Mode (No API Keys Required)

Bash

```
git clone <your-repo-url>
cd 5_day_AI_agents
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.template .env
streamlit run app.py
```

Open **http://localhost:8501**. The app opens on the **Interests** page — configure your topics, then navigate to **Daily Briefing** from the sidebar and click **"Generate Briefing"** to see the full agent pipeline run with pre-loaded demo data about the LLM agent ecosystem.

### 2. Live Mode & Docker

To use live endpoints, add your LLM API key to the `.env` file and set `DEMO_MODE=false`.

**Deploy via Docker:**

Bash

```
docker build -t knowledge-concierge .
docker run -p 8501:8501 --env-file .env knowledge-concierge
```

---

## Project Structure

```
5_day_AI_agents/
├── app.py                    # Streamlit frontend (sidebar nav + live logs)
├── requirements.txt          # Python dependencies
├── Dockerfile                # Cloud Run deployment
├── .env.template             # Env var reference (safe to commit)
├── .pre-commit-config.yaml   # Git hook for secret scanning
│
├── agents/                   # Multi-Agent System
│   ├── coordinator.py        # Pipeline orchestrator
│   ├── curator.py            # Stage 1: fetch & score articles
│   ├── summarizer.py         # Stage 2: generate digests
│   └── graph_builder.py      # Stage 3: knowledge graph & mind maps
│
├── mcp_server/               # MCP Server
│   └── server.py             # 8 standardized tools with JSON Schema
│
├── skills/                   # Agent Skills (4 skills)
│   ├── summarize.md          # Article summarization
│   ├── code_walkthrough.md   # Repository analysis
│   ├── mindmap.md            # Knowledge graph visualization
│   └── sources_recommendation.md  # Source discovery & recommendation
│
├── memory/
│   ├── memory_store.py       # JSON-based persistence layer
│   ├── memory_demo.json      # Demo mode memory (auto-generated)
│   └── memory_live.json      # Live mode memory (auto-generated)
│
├── utils/
│   ├── config.py             # Environment config (demo/live memory paths)
│   ├── llm_client.py         # LLM API (OpenAI SDK, provider-agnostic)
│   └── demo_data.py          # Pre-loaded demo articles & graph
│
└── security/
    └── scan_secrets.py       # Pre-commit credential scanner
```
