# Skill: Article Summarization

**Agent Skill — Personal Knowledge Concierge**

## Description
Summarize technical articles, research papers, and blog posts into
concise, structured summaries optimized for quick consumption.

## When to Use
- User requests a "TL;DR" or summary of an article
- Agent needs to digest content before adding it to the knowledge graph
- Building the daily briefing digest

## Required Tools (MCP)
- `fetch_article` — Retrieve article content by URL
- `summarize_text` — Generate a summary using the configured LLM

## Prompt Template
```
You are an expert technical summarizer. For the given content, produce:

1. **TL;DR** (1-2 sentences): The single most important takeaway.
2. **Key Findings** (3-5 bullets): Core discoveries or arguments.
3. **Methods/Approach**: Brief description of how they did it.
4. **Relevance**: Why this matters to the reader's interests.

Be specific. Avoid filler words. Use concrete numbers when available.
```

## Output Schema
```json
{
  "tl_dr": "string (max 150 chars)",
  "key_findings": ["string", "..."],
  "methods": "string",
  "relevance": "string",
  "topic_tags": ["string", "..."]
}
```

## Example Output
```json
{
  "tl_dr": "ADK framework enables 40% better task completion via coordinator-agent topology.",
  "key_findings": [
    "Declarative agent topology reduces setup time",
    "Shared context bus eliminates orchestrator bottleneck",
    "Tool-gated safety prevents prompt injection"
  ],
  "methods": "Evaluated on HotpotQA, HumanEval+, and WebArena benchmarks",
  "relevance": "Directly applicable to building multi-agent systems",
  "topic_tags": ["AI Agents", "Multi-Agent Systems", "Framework"]
}
```
