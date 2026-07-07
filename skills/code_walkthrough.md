# Skill: Code Repository Walkthrough

**Agent Skill — Personal Knowledge Concierge**

## Description
Analyze a GitHub repository and generate a structured walkthrough
explaining the architecture, key components, and how to get started.
Optimized for technical readers who want to understand a codebase
without cloning and reading every file.

## When to Use
- User encounters a GitHub trending repo and wants an overview
- Agent needs to explain a codebase's architecture
- Building educational walkthroughs from open-source projects

## Required Tools (MCP)
- `analyze_repo` — Fetch repo structure and README via GitHub API
- `summarize_text` — Generate human-readable explanations

## Prompt Template
```
You are an expert code reviewer and technical educator. For the given
repository structure and README, produce a walkthrough:

1. **What It Does** (1-2 sentences): High-level purpose.
2. **Architecture** (ASCII diagram): How components connect.
3. **Key Components** (list): What each directory/module does.
4. **Getting Started** (code block): Minimal setup commands.
5. **Interesting Patterns**: Notable design patterns or techniques used.

Focus on clarity. Assume the reader is technically proficient but
unfamiliar with this specific codebase.
```

## Output Schema
```json
{
  "what_it_does": "string",
  "architecture_diagram": "string (ASCII art or Mermaid)",
  "key_components": [
    {"path": "string", "purpose": "string"}
  ],
  "getting_started": "string (code block)",
  "interesting_patterns": ["string", "..."]
}
```

## Example Output
```json
{
  "what_it_does": "A multi-agent quantitative trading system using LangChain agents.",
  "architecture_diagram": "Market Data Agent → Technical Analysis Agent → Signal Generator → Portfolio Agent → Orders",
  "key_components": [
    {"path": "agents/market_data/", "purpose": "WebSocket feeds from Alpaca/Yahoo, normalized to internal event bus"},
    {"path": "agents/technical/", "purpose": "20+ indicators producing scored signal vectors"}
  ],
  "getting_started": "docker-compose up -d\npython examples/quickstart.py",
  "interesting_patterns": [
    "Event-driven agent communication via internal pub/sub",
    "Weighted ensemble for signal combination with risk constraints"
  ]
}
```
