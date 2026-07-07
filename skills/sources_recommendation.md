# Skill: Source Discovery & Recommendation

**Agent Skill — Personal Knowledge Concierge**

## Description
Discover and recommend high-quality, trusted information sources for any
given topic or set of keywords. The skill uses two complementary strategies:
(1) LLM-based recommendation — draw on the model's training knowledge of
popular, well-regarded sources across domains; (2) Web search-based
recommendation — search general websites and evaluate results for topic
match, authority, and freshness.

This skill ensures the Knowledge Concierge can expand beyond its default
sources (ArXiv, GitHub Trending) and suggest domain-specific venues the
user might not know about.

## When to Use
- User sets up new interests and needs source suggestions
- Agent needs to broaden its curation beyond configured sources
- User asks "where should I look for content about X?"
- Periodic source refresh — discover new publications, blogs, or databases
- Building a customized source list for a research project

## Required Tools (MCP)
- `search_arxiv` — Search ArXiv for academic sources on a topic (existing)
- `search_memory` — Check reading history for previously used sources (existing)
- `fetch_article` — Verify that a recommended source is accessible (existing)

Recommended new MCP tools:
- `recommend_sources_llm` — Query the LLM directly for source recommendations
  based on its training knowledge of domain publications, conferences,
  journals, blogs, newsletters, and communities.
- `search_web_sources` — Search general websites (via Bing/Google API) for
  sources matching a topic, then filter and rank by: domain authority,
  topic relevance, update frequency, and credibility signals.

## Two Recommendation Strategies

### Strategy A: LLM-Based Recommendation
```
Ask the LLM: "For someone deeply interested in {topics}, what are the
5-10 most respected and useful sources of ongoing content? Consider:
- Academic: key conferences, journals, arXiv categories, lab blogs
- Industry: company engineering blogs, tech reports, whitepapers
- Community: newsletters, podcasts, influential practitioners, forums
- Open Source: active GitHub organizations, project websites, RFC repos
- News: specialized news sites, aggregators, curated link blogs

For each source, provide:
- Name and URL
- Type (academic / industry / community / open-source / news)
- Why it's relevant to the user's interests
- Approximate content frequency (daily / weekly / monthly)
- Trust signal (peer-reviewed / established org / respected individual / community-vetted)"
```

### Strategy B: Web Search-Based Recommendation
```
For each interest keyword:
1. Search: "{keyword} best sources" + "{keyword} research papers" +
   "{keyword} blog" + "{keyword} newsletter"
2. Fetch top 5-8 results per query
3. Evaluate each result:
   - Domain authority: established institution, known expert, or well-cited
   - Topic match: how specifically does this cover the interest?
   - Freshness: is content being actively published?
   - Signal-to-noise: is the source focused, or a firehose?
4. Deduplicate across queries
5. Return top N ranked by composite score
```

## Prompt Template
```
You are an expert research librarian and knowledge curator. Your job is
to help someone build a personalized, high-quality information diet.

For the given topics, recommend the best sources of ongoing content.
Optimize for:
- **Depth over breadth**: Sources that go deep on the topic, not general news
- **Signal over noise**: Sources where most content is worth reading
- **Diversity of perspective**: Mix of academic, industry, and community
- **Accessibility**: Prefer open-access and freely available sources

For each source, explain WHY it's good for this specific user — connect
it directly to their stated interests. If you're uncertain about a source's
current status, note that limitation.

Format your response as a structured list with clear categories.
```

## Output Schema
```json
{
  "recommended_sources": [
    {
      "name": "string (source name)",
      "url": "string (homepage or RSS feed URL)",
      "type": "academic | industry | community | open_source | news",
      "description": "string (1-2 sentences about the source)",
      "relevance": "string (why this matches the user's interests)",
      "frequency": "daily | weekly | monthly",
      "trust_signal": "peer_reviewed | established_org | respected_individual | community_vetted | self_published",
      "recommendation_method": "llm_knowledge | web_search | user_configured"
    }
  ],
  "discovery_method": "llm | web_search | hybrid",
  "total_sources_found": "integer",
  "new_sources_added": "integer"
}
```

## Example Output
```json
{
  "recommended_sources": [
    {
      "name": "ArXiv cs.MA (Multi-Agent Systems)",
      "url": "https://arxiv.org/list/cs.MA/recent",
      "type": "academic",
      "description": "Latest preprints on multi-agent systems, coordination, and distributed AI.",
      "relevance": "Directly covers multi-agent architecture and coordination — core interests.",
      "frequency": "daily",
      "trust_signal": "peer_reviewed",
      "recommendation_method": "llm_knowledge"
    },
    {
      "name": "Anthropic Engineering Blog",
      "url": "https://www.anthropic.com/engineering",
      "type": "industry",
      "description": "Deep technical posts on LLM systems, agent design, and AI safety from Claude's creators.",
      "relevance": "Covers MCP, agent architecture, and LLM reliability — directly relevant.",
      "frequency": "weekly",
      "trust_signal": "established_org",
      "recommendation_method": "llm_knowledge"
    },
    {
      "name": "MCP Awesome List",
      "url": "https://github.com/modelcontextprotocol/awesome-mcp",
      "type": "community",
      "description": "Curated list of MCP servers, clients, and community resources.",
      "relevance": "Central resource for MCP ecosystem — tools and integrations.",
      "frequency": "weekly",
      "trust_signal": "community_vetted",
      "recommendation_method": "web_search"
    }
  ],
  "discovery_method": "hybrid",
  "total_sources_found": 12,
  "new_sources_added": 5
}
```

## Integration with the Curator Agent

When the Curator runs and finds that configured sources return too few
results for a given interest:

1. Curator calls `recommend_sources_llm` with the underrepresented interest
2. If LLM recommendations are insufficient or uncertain, fall back to
   `search_web_sources` for web-based discovery
3. New sources are presented to the user as suggestions: "We found 3 new
   sources for Quantum Computing — would you like to add them?"
4. User-approved sources are persisted to preferences alongside ArXiv
   and GitHub Trending
5. On the next curation run, the expanded source list is used

## Tips
- Cache LLM-based source recommendations per topic (they change slowly)
- Re-verify web-search results monthly — URLs and content quality evolve
- Prefer sources with RSS/Atom feeds for reliable programmatic access
- Rate the signal-to-noise ratio after a few curation runs and prune
- Let users mark sources as "tried and dropped" to avoid re-recommending
