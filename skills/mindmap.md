# Skill: Knowledge Graph Mind Map Generation

**Agent Skill — Personal Knowledge Concierge**

## Description
Transform the agent's reading history and knowledge graph into a
visual Mermaid.js mind map. The mind map shows how concepts connect
across readings, revealing the evolution of the user's understanding
over time.

## When to Use
- User wants to "see the big picture" of their knowledge base
- Agent needs to visualize topic relationships
- Generating the weekly/monthly knowledge synthesis

## Required Tools (MCP)
- `query_graph` — Retrieve graph nodes and edges
- `generate_mindmap` — Produce Mermaid.js syntax

## Prompt Template
```
You are an expert at knowledge visualization. Given a set of topics,
articles, and their relationships, generate a Mermaid.js mindmap that:

1. Places the most connected topic at the center.
2. Branches out to subtopics and related articles.
3. Uses clear, concise labels (max 40 chars per node).
4. Groups related concepts visually.

The mind map should tell a story about how the user's knowledge
has grown and connected over time.
```

## Output Schema
```json
{
  "mermaid_syntax": "string (valid Mermaid.js mindmap)",
  "central_topic": "string",
  "total_nodes": "integer",
  "max_depth": "integer"
}
```

## Mermaid.js Mindmap Syntax Reference
```
mindmap
  root(Central Topic)
    Subtopic A
      Article 1
      Article 2
    Subtopic B
      Article 3
        Concept B.1
      Article 4
    Subtopic C
```

## Tips
- Keep depth to 3-4 levels for readability
- Use emoji sparingly in labels (rendering compatibility)
- Article nodes should appear as leaves under their primary topic
- Cross-references can be shown as secondary connections
