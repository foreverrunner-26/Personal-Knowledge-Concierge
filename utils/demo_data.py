"""
Demo Data Module
================
Pre-loaded realistic data for hackathon demos. When DEMO_MODE is enabled,
the agent pipeline returns these polished results instantly instead of
waiting for live API calls.

This ensures a smooth, impressive demo experience regardless of network
conditions or API key availability.

Data focuses on the LLM Agent ecosystem — frameworks, architectures,
protocols, and real-world applications — showcasing the Knowledge
Concierge as a specialist that deeply understands the agent landscape.
    - Agent Architecture & Design Patterns
    - Agent Protocols (MCP, A2A)
    - Agent Frameworks & Tooling
    - Agent Applications (code, browser, research)
    - Multi-Agent Systems & Coordination
    - Agent Memory & Knowledge Management
"""

from datetime import datetime, timedelta

# ── Demo Articles ────────────────────────────────────────────────────────────

DEMO_ARTICLES = [
    {
        "id": "demo-001",
        "title": "Building Reliable LLM Agents: Patterns for Error Recovery and Self-Correction",
        "source": "ArXiv",
        "source_url": "https://arxiv.org/abs/2501.12345",
        "topics": ["Agent Architecture", "Reliability", "Error Recovery"],
        "relevance_score": 0.96,
        "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        "tl_dr": (
            "A systematic study of failure modes in LLM agents and a catalog of "
            "recovery patterns: self-reflection loops, tool-call retry with feedback, "
            "decomposition-and-verify, and human-in-the-loop escalation. Agents using "
            "these patterns recover from 78% of errors autonomously."
        ),
        "full_summary": (
            "## Key Contribution\n\n"
            "LLM agents fail in predictable ways: tool misuse, context confusion, "
            "premature task completion, and reasoning collapse on long trajectories. "
            "This paper catalogs 14 failure modes and 9 recovery patterns for production environments.\n\n"
            "### Core Recovery Patterns\n\n"
            "1. **Self-Reflection Loop**: After each major step, the agent queries "
            "a structured checklist to verify task completion. This deterministic check "
            "intercepts 34% of hallucinations before they compound.\n\n"
            "2. **Tool-Call Retry with Structured Feedback**: When a tool returns an "
            "error, the agent receives the tool's JSON Schema and the failed payload "
            "for reformulation. This mechanism improves tool-use success rates from 71% to 94%.\n\n"
            "3. **Decomposition-and-Verify**: Complex tasks are partitioned into "
            "verifiable subtasks with binary pass/fail constraints. Failures isolate "
            "retries to the specific subtask rather than the entire execution chain.\n\n"
            "4. **Contextual Escalation**: Following exhaustion of retry limits, execution "
            "halts and escalates to human oversight with a structured state dump, reducing "
            "human intervention time by 60% compared to raw log analysis.\n\n"
            "### Architectural Implementation\n"
            "```text\n"
            "Request → Planner → Executor → Verifier\n"
            "                  ↑          ↓\n"
            "                  └── Recoverer ←┘ (on failure)\n"
            "                       ↓ (threshold reached)\n"
            "                  Human Handoff\n"
            "```\n"
        ),
        "related_to": ["demo-007", "demo-008"],
        "relation_type": "builds_on",
    },
    {
        "id": "demo-002",
        "title": "MCP: The Model Context Protocol — A Universal Interface for LLM Tools",
        "source": "ArXiv",
        "source_url": "https://arxiv.org/abs/2502.67890",
        "topics": ["Agent Protocol", "MCP", "Tool Integration"],
        "relevance_score": 0.95,
        "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
        "tl_dr": (
            "The Model Context Protocol (MCP) defines a standardized JSON-RPC interface "
            "for LLMs to discover and call external tools. It acts as a universal adapter "
            "layer, formalizing protocol interactions and demonstrating 8 reference server implementations."
        ),
        "full_summary": (
            "## Protocol Overview\n\n"
            "Historically, integrating LLMs with external data required bespoke middleware "
            "for every model-service pairing. MCP abstracts this via a standardized protocol, "
            "fostering an ecosystem of highly reusable tool servers.\n\n"
            "### System Architecture\n\n"
            "MCP relies on a client-server architecture layered over JSON-RPC 2.0:\n\n"
            "1. **Dynamic Tool Discovery**: Servers broadcast available tools along with "
            "their JSON Schema input contracts. Host clients dynamically map these at connection "
            "time, eliminating hardcoded integration paths.\n\n"
            "2. **Abstract Resource Access**: MCP servers expose discrete resources "
            "(files, databases, API streams) via URI templates, allowing the LLM to query "
            "underlying data states without knowledge of the storage infrastructure.\n\n"
            "3. **Prompt Templates**: Servers supply native prompt templates optimized "
            "for their exposed tools, significantly improving model adherence to specific API structures.\n\n"
            "4. **Transport Agnosticism**: The protocol natively supports stdio (local execution), "
            "HTTP/SSE, and WebSockets, ensuring uniform server code across deployment environments.\n\n"
            "### Reference Implementations\n\n"
            "The publication details 8 production-grade MCP servers including PostgreSQL, "
            "GitHub API, vector memory stores, and secure code executors, proving the protocol's "
            "versatility across both read-heavy and write-heavy workloads."
        ),
        "related_to": ["demo-004", "demo-005"],
        "relation_type": "enables",
    },
    {
        "id": "demo-003",
        "title": "Agent2Agent: Google's Open Protocol for Direct Inter-Agent Communication",
        "source": "GitHub Trending",
        "source_url": "https://github.com/google/A2A",
        "topics": ["Agent Protocol", "Multi-Agent Systems", "Interoperability"],
        "relevance_score": 0.94,
        "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        "tl_dr": (
            "Google's Agent-to-Agent (A2A) protocol enables autonomous agents to discover "
            "peers, negotiate capabilities, and delegate task loads without centralized orchestration. "
            "It leverages JSON-RPC alongside 'agent cards' and asynchronous task streaming."
        ),
        "full_summary": (
            "## Decentralized Orchestration\n\n"
            "Conventional multi-agent frameworks suffer from tight coupling, requiring centralized "
            "orchestrators to map all agent capabilities upfront. A2A shifts to a decentralized "
            "discovery model tailored for complex, multi-modal environments.\n\n"
            "### Core Protocol Mechanics\n\n"
            "1. **Agent Cards**: Agents emit structured JSON manifests detailing their identities, "
            "capabilities (via JSON Schema), and endpoint URIs. These are indexed via registry services "
            "or discovered across local meshes.\n\n"
            "2. **Asynchronous Task Lifecycle**: Tasks traverse strict states: `submitted → "
            "processing → streaming → completed/failed`. The streaming capability provides real-time "
            "telemetry, essential for long-horizon planning and execution.\n\n"
            "3. **Capability Negotiation**: Prior to delegation, Agent A transmits a sample workload "
            "to Agent B. Agent B returns a confidence score and resource estimate, optimizing workload "
            "distribution across the agent mesh.\n\n"
            "4. **Event-Driven Delivery**: Eradicates polling via webhook-based push notifications, "
            "incorporating exponential backoff for network resilience.\n\n"
            "### Relationship to Integration Protocols\n\n"
            "While protocols like MCP handle agent-to-environment interactions, A2A strictly governs "
            "agent-to-agent dynamics. In advanced deployments (e.g., quantitative research frameworks), "
            "an agent might utilize MCP to query financial datasets while leveraging A2A to delegate "
            "predictive modeling to a specialized peer."
        ),
        "related_to": ["demo-002", "demo-004"],
        "relation_type": "complements",
    },
    {
        "id": "demo-004",
        "title": "Agent Skills: Composable, Reusable Capability Modules for AI Agents",
        "source": "GitHub Trending",
        "source_url": "https://github.com/example/agent-skills",
        "topics": ["Agent Architecture", "Skills", "Composability"],
        "relevance_score": 0.93,
        "date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
        "tl_dr": (
            "The Agent Skills framework introduces modular capability definitions using "
            "declarative Markdown files. By encapsulating tool bindings, prompt templates, "
            "and schemas, it enables dynamic capability injection into agent runtimes."
        ),
        "full_summary": (
            "## Declarative Capability Models\n\n"
            "Modifying core agent logic to introduce new capabilities scales poorly. The Agent "
            "Skills framework addresses this by abstracting capabilities into declarative files "
            "that the execution environment can load, parse, and activate on demand.\n\n"
            "### Structural Anatomy\n\n"
            "Skills are defined via Markdown utilizing YAML frontmatter for configuration:\n\n"
            "```yaml\n"
            "---\n"
            "name: data_pipeline_audit\n"
            "description: Review data processing scripts for edge cases and type safety\n"
            "triggers:\n"
            "  - 'audit this pipeline'\n"
            "  - 'check data integrity'\n"
            "tools_required:\n"
            "  - mcp:filesystem\n"
            "  - mcp:linter\n"
            "output_schema:\n"
            "  type: object\n"
            "  properties:\n"
            "    anomalies: {type: array}\n"
            "    confidence_score: {type: number}\n"
            "---\n"
            "```\n\n"
            "1. **Semantic Triggering**: Runtimes utilize vector embeddings to match user "
            "intent against available skill triggers, dynamically activating the appropriate context.\n\n"
            "2. **Strict Tool Binding**: Required protocols (e.g., MCP modules) are verified "
            "prior to skill activation, ensuring runtime stability.\n\n"
            "3. **Prompt Composition**: The skill's Markdown body acts as a highly specialized "
            "system prompt, temporarily overriding or appending to the agent's base instruction set."
        ),
        "related_to": ["demo-002", "demo-003"],
        "relation_type": "utilizes",
    },
    {
        "id": "demo-005",
        "title": "Agent Memory Systems: RAG, Vector Search, and Long-Term Knowledge Retention",
        "source": "ArXiv",
        "source_url": "https://arxiv.org/abs/2503.11111",
        "topics": ["Agent Architecture", "Memory", "RAG"],
        "relevance_score": 0.92,
        "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
        "tl_dr": (
            "An architectural survey of memory systems for LLM agents, outlining working, "
            "episodic, semantic, and procedural memory tiers. Multi-tiered memory frameworks "
            "demonstrate a 40% performance increase on long-horizon reasoning tasks."
        ),
        "full_summary": (
            "## Hierarchical Memory Architectures\n\n"
            "Stateless LLMs require external scaffolding to persist context, user preferences, "
            "and learned strategies across sessions. This paper standardizes a four-tier memory model.\n\n"
            "### The Four Tiers\n\n"
            "1. **Working Memory** (Context Window): The agent's immediate processing layer. "
            "Optimizations focus on sliding-window attention and importance-weighted token retention "
            "to maximize efficiency within 128K+ token limits.\n\n"
            "2. **Episodic Memory** (RAG): Historical interactions embedded within vector databases. "
            "Advanced implementations utilize dual-index retrieval combining semantic similarity "
            "with temporal decay ('what is the most recent relevant data?').\n\n"
            "3. **Semantic Memory** (Knowledge Graphs): Relational data and facts stored as structured "
            "triples (Nodes/Edges). Crucial for multi-hop reasoning tasks where vector search "
            "fails to capture topological relationships.\n\n"
            "4. **Procedural Memory** (Skills): Autonomous extraction of successful strategies into "
            "executable modules. As the agent encounters recurring problems, it compiles optimized "
            "prompt-and-tool sequences for future reuse."
        ),
        "related_to": ["demo-004", "demo-008"],
        "relation_type": "supports",
    },
    {
        "id": "demo-006",
        "title": "Browser Agents: Teaching LLMs to Navigate, Fill Forms, and Extract Web Data",
        "source": "GitHub Trending",
        "source_url": "https://github.com/example/browser-agent",
        "topics": ["Agent Applications", "Web Automation", "Computer Use"],
        "relevance_score": 0.91,
        "date": (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d"),
        "tl_dr": (
            "A framework for translating natural language into complex web interactions. By parsing "
            "accessibility trees instead of relying on vision models, the system achieves 82% task "
            "completion on the WebArena benchmark with significantly lower latency."
        ),
        "full_summary": (
            "## Deterministic Web Automation\n\n"
            "Navigating dynamic JavaScript environments and unstructured layouts remains a core "
            "challenge for autonomous agents. This paper details a shift from pixel-based evaluation "
            "to structured DOM analysis.\n\n"
            "### Core Methodologies\n\n"
            "1. **Accessibility Tree Parsing**: The agent processes the browser's accessibility tree—a "
            "cleaner, semantic representation of interactive elements. This reduces token overhead by 50x "
            "and eliminates the hallucination risks associated with visual-language models (VLMs).\n\n"
            "2. **Action Primitives**: Execution is constrained to discrete actions (click, input, select, "
            "scroll) with enforced state-validation post-execution to ensure deterministic outcomes.\n\n"
            "3. **State Tracking**: A local graph maps visited URLs and extracted payloads, enabling "
            "intelligent backtracking during multi-step data extraction (e.g., scraping financial reports "
            "across multiple paginated sub-domains).\n\n"
            "### Enterprise Applications\n\n"
            "- **Quantitative Research**: Automated extraction of unstructured alternative datasets.\n"
            "- **Market Surveillance**: Monitoring competitor pricing and compliance updates.\n"
            "- **Quality Assurance**: Autonomous generation and execution of end-to-end testing flows."
        ),
        "related_to": ["demo-001", "demo-009"],
        "relation_type": "applies",
    },
    {
        "id": "demo-007",
        "title": "Multi-Agent Debate: How Competing LLM Agents Improve Reasoning Accuracy",
        "source": "ArXiv",
        "source_url": "https://arxiv.org/abs/2502.99999",
        "topics": ["Agent Architecture", "Multi-Agent", "Reasoning"],
        "relevance_score": 0.94,
        "date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
        "tl_dr": (
            "Multi-agent debate protocols leverage adversarial collaboration to enhance output. "
            "By forcing models to critique and revise reasoning chains, accuracy on complex "
            "mathematical and factual benchmarks improves by 15-34% over single-agent baselines."
        ),
        "full_summary": (
            "## Adversarial Reasoning Protocols\n\n"
            "LLMs exhibit a distinct asymmetry: they are substantially better at critiquing flawed "
            "logic than generating flawless logic. Multi-agent debate exploits this trait.\n\n"
            "### Protocol Mechanics\n\n"
            "1. **Generation Round**: Multiple agents (isolated by temperature or prompt variations) "
            "independently formulate solutions and reasoning trajectories for a given prompt.\n\n"
            "2. **Critique Round**: Agents ingest peer proposals and generate structured critiques, "
            "explicitly identifying logical fallacies, missing variables, or factual errors.\n\n"
            "3. **Revision Round**: Agents integrate valid critiques to revise their initial proposals. "
            "The system records the delta between iterations to track convergence.\n\n"
            "4. **Resolution**: The loop terminates when consensus is reached or a maximum round limit "
            "is hit, yielding a heavily vetted final output.\n\n"
            "### Benchmark Improvements\n\n"
            "- **GSM8K (Math)**: Baseline 89.2% → Debate Protocol 96.1%\n"
            "- **TruthfulQA (Factuality)**: Baseline 72.3% → Debate Protocol 91.8%\n"
            "- **BigBench Hard**: Baseline 64.1% → Debate Protocol 78.9%\n\n"
            "The results indicate that deploying multiple smaller models in a debate topology can "
            "frequently outperform a single massive model in zero-shot scenarios."
        ),
        "related_to": ["demo-001", "demo-008"],
        "relation_type": "enhances",
    },
    {
        "id": "demo-008",
        "title": "The Coordinator Pattern: Designing Agent Topologies That Scale",
        "source": "ArXiv",
        "source_url": "https://arxiv.org/abs/2503.22222",
        "topics": ["Agent Architecture", "Design Patterns", "Scalability"],
        "relevance_score": 0.90,
        "date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
        "tl_dr": (
            "An architectural analysis of 6 multi-agent topologies, evaluating latency, "
            "fault tolerance, and deployment cost. The Coordinator pattern is identified "
            "as the optimal architecture for highly deterministic, pipeline-driven workflows."
        ),
        "full_summary": (
            "## Topological Design in Multi-Agent Systems\n\n"
            "System topology dictates how agents route information and delegate execution. "
            "This paper provides a rigorous taxonomy of standard patterns.\n\n"
            "### Architectural Taxonomies\n\n"
            "1. **Coordinator**: A central agent manages state and routes tasks to specialized "
            "sub-agents. Highly predictable and easily debuggable, making it ideal for sequential "
            "data processing pipelines (e.g., ETL jobs, curation workflows).\n\n"
            "2. **Peer-to-Peer**: Decentralized delegation. Scales infinitely but suffers from "
            "non-deterministic execution paths and highly variable token costs.\n\n"
            "3. **Hierarchical**: Tree-based delegation. Effective for massive workloads but "
            "introduces severe latency penalties at deep network depths.\n\n"
            "4. **Blackboard**: Agents asynchronously read/write to a shared memory state. "
            "Excellent for emergent problem solving but prone to race conditions and stale data reads.\n\n"
            "5. **Market-Based**: Agents bid for computational tasks using confidence heuristics. "
            "Optimal for resource allocation but introduces heavy bidding overhead.\n\n"
            "### Selection Criteria\n\n"
            "For systems requiring strict data governance and deterministic execution (such as "
            "financial modeling pipelines or knowledge curation), the **Coordinator** pattern minimizes "
            "system entropy while maintaining clear audit trails for LLM decisions."
        ),
        "related_to": ["demo-001", "demo-003", "demo-007"],
        "relation_type": "contextualizes",
    },
    {
        "id": "demo-009",
        "title": "Code Agents: LLMs That Write, Test, Debug, and Deploy Software Autonomously",
        "source": "GitHub Trending",
        "source_url": "https://github.com/example/code-agent",
        "topics": ["Agent Applications", "Code Generation", "DevTools"],
        "relevance_score": 0.93,
        "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
        "tl_dr": (
            "A technical overview of autonomous coding agents capable of resolving GitHub issues "
            "end-to-end. By combining LLM logic with strict deterministic guardrails (compilers, linters), "
            "these agents achieve a 35% resolution rate on SWE-bench."
        ),
        "full_summary": (
            "## Autonomous Software Engineering\n\n"
            "Code agents represent the most mature application of autonomous LLMs, largely due to "
            "the existence of deterministic verification environments (compilers, test suites).\n\n"
            "### Execution Paradigms\n\n"
            "1. **Conversational Scaffolding**: Systems maintain context across multiple files, "
            "allowing for complex refactoring. Success relies heavily on dynamic context management—"
            "loading only the abstract syntax trees (AST) relevant to the current scope.\n\n"
            "2. **Task-Driven Autonomy**: The agent ingests an issue ticket, clones the repository, "
            "and enters an execution loop. It reads dependencies, drafts implementations, and triggers "
            "local CI pipelines.\n\n"
            "3. **The Validation Loop**: The critical differentiator in modern code agents is the "
            "speed of the feedback loop. `Generate → Compile → Parse Traceback → Revise`. Because "
            "the compiler provides ground-truth feedback, the agent can self-correct hallucinations "
            "without human intervention.\n\n"
            "### Architectural Requirements\n\n"
            "Deploying these agents requires secure, ephemeral execution environments (e.g., containerized "
            "sandboxes) to safely execute untrusted AI-generated code while retaining network access "
            "for dependency resolution."
        ),
        "related_to": ["demo-001", "demo-006"],
        "relation_type": "shares_patterns",
    },
    {
        "id": "demo-010",
        "title": "Agent Evaluation: How Do We Know If an Agent Is Actually Good?",
        "source": "ArXiv",
        "source_url": "https://arxiv.org/abs/2501.54321",
        "topics": ["Agent Architecture", "Evaluation", "Benchmarks"],
        "relevance_score": 0.91,
        "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        "tl_dr": (
            "Standard benchmarks fail to capture the complexity of multi-step agent workflows. "
            "This paper introduces a multidimensional evaluation matrix scoring task success, "
            "trajectory efficiency, token economics, and behavioral safety."
        ),
        "full_summary": (
            "## Multidimensional Evaluation Frameworks\n\n"
            "Evaluating an agent purely on final task success masks severe inefficiencies in "
            "execution. A comprehensive evaluation must audit the entire behavioral trajectory.\n\n"
            "### The Four Pillars of Agent Evaluation\n\n"
            "1. **Task Success**: Validated via deterministic assertions rather than LLM-as-a-judge "
            "mechanisms, which exhibit measurable bias toward their own model families.\n\n"
            "2. **Trajectory Quality**: Measures the elegance of the execution path. Metrics include "
            "tool-call precision (were unnecessary API calls made?), state-space exploration (did it "
            "get stuck in a loop?), and recovery resilience.\n\n"
            "3. **Cost Efficiency**: Tracks total token expenditure alongside API latency and "
            "compute overhead, normalizing the score against the baseline complexity of the task.\n\n"
            "4. **Safety & Alignment**: Stress-tests against catastrophic tool usage (e.g., executing "
            "`rm -rf`, exposing environment variables) and prompt injection vulnerabilities.\n\n"
            "### The Contamination Problem\n\n"
            "The authors highlight that 40% of standard agent benchmark data is present in modern "
            "pre-training corpora, necessitating the continuous generation of novel, programmatic "
            "evaluations to accurately measure true generalization capability."
        ),
        "related_to": ["demo-001", "demo-007", "demo-008"],
        "relation_type": "measures",
    },
]

# ── Demo Knowledge Graph ─────────────────────────────────────────────────────
# Nodes and edges pre-built for the demo's graph visualization.

DEMO_GRAPH_NODES = [
    # Topic nodes — the agent landscape
    {"id": "topic-arch", "label": "Agent Architecture", "type": "topic", "group": "core"},
    {"id": "topic-protocol", "label": "Agent Protocols", "type": "topic", "group": "core"},
    {"id": "topic-apps", "label": "Agent Applications", "type": "topic", "group": "core"},
    {"id": "topic-multi", "label": "Multi-Agent Systems", "type": "topic", "group": "core"},
    {"id": "topic-mcp", "label": "Model Context Protocol", "type": "topic", "group": "protocols"},
    {"id": "topic-a2a", "label": "Agent-to-Agent (A2A)", "type": "topic", "group": "protocols"},
    {"id": "topic-memory", "label": "Agent Memory", "type": "topic", "group": "architecture"},
    {"id": "topic-skills", "label": "Agent Skills", "type": "topic", "group": "architecture"},
    {"id": "topic-reliability", "label": "Reliability & Recovery", "type": "topic", "group": "architecture"},
    {"id": "topic-reasoning", "label": "Reasoning & Debate", "type": "topic", "group": "architecture"},
    {"id": "topic-eval", "label": "Evaluation & Benchmarks", "type": "topic", "group": "architecture"},
    {"id": "topic-code", "label": "Code Agents", "type": "topic", "group": "applications"},
    {"id": "topic-browser", "label": "Browser Agents", "type": "topic", "group": "applications"},
    {"id": "topic-tools", "label": "Tool Integration", "type": "topic", "group": "protocols"},
    {"id": "topic-design", "label": "Design Patterns", "type": "topic", "group": "architecture"},
    # Article nodes
    {"id": "demo-001", "label": "Reliable LLM Agents", "type": "article", "group": "architecture"},
    {"id": "demo-002", "label": "MCP Protocol", "type": "article", "group": "protocols"},
    {"id": "demo-003", "label": "Agent2Agent Protocol", "type": "article", "group": "protocols"},
    {"id": "demo-004", "label": "Agent Skills Framework", "type": "article", "group": "architecture"},
    {"id": "demo-005", "label": "Agent Memory Systems", "type": "article", "group": "architecture"},
    {"id": "demo-006", "label": "Browser Agents", "type": "article", "group": "applications"},
    {"id": "demo-007", "label": "Multi-Agent Debate", "type": "article", "group": "architecture"},
    {"id": "demo-008", "label": "Coordinator Pattern", "type": "article", "group": "architecture"},
    {"id": "demo-009", "label": "Code Agents Survey", "type": "article", "group": "applications"},
    {"id": "demo-010", "label": "Agent Evaluation Framework", "type": "article", "group": "architecture"},
]

DEMO_GRAPH_EDGES = [
    # Article → Topic relationships
    ("demo-001", "topic-arch", "explores"),
    ("demo-001", "topic-reliability", "defines"),
    ("demo-002", "topic-protocol", "specifies"),
    ("demo-002", "topic-mcp", "introduces"),
    ("demo-002", "topic-tools", "standardizes"),
    ("demo-003", "topic-protocol", "specifies"),
    ("demo-003", "topic-a2a", "introduces"),
    ("demo-003", "topic-multi", "enables"),
    ("demo-004", "topic-arch", "explores"),
    ("demo-004", "topic-skills", "defines"),
    ("demo-005", "topic-arch", "explores"),
    ("demo-005", "topic-memory", "categorizes"),
    ("demo-006", "topic-apps", "exemplifies"),
    ("demo-006", "topic-browser", "defines"),
    ("demo-007", "topic-multi", "utilizes"),
    ("demo-007", "topic-reasoning", "improves"),
    ("demo-008", "topic-arch", "analyzes"),
    ("demo-008", "topic-design", "categorizes"),
    ("demo-008", "topic-multi", "structures"),
    ("demo-009", "topic-apps", "exemplifies"),
    ("demo-009", "topic-code", "surveys"),
    ("demo-010", "topic-eval", "formalizes"),
    ("demo-010", "topic-arch", "audits"),
    
    # Cross-topic relationships
    ("topic-arch", "topic-design", "encompasses"),
    ("topic-arch", "topic-reliability", "requires"),
    ("topic-arch", "topic-memory", "incorporates"),
    ("topic-arch", "topic-skills", "utilizes"),
    ("topic-arch", "topic-reasoning", "facilitates"),
    ("topic-arch", "topic-eval", "validated_by"),
    ("topic-protocol", "topic-mcp", "includes"),
    ("topic-protocol", "topic-a2a", "includes"),
    ("topic-protocol", "topic-tools", "abstracts"),
    ("topic-multi", "topic-reasoning", "enhances"),
    ("topic-multi", "topic-design", "dictates"),
    ("topic-multi", "topic-a2a", "requires"),
    ("topic-apps", "topic-code", "includes"),
    ("topic-apps", "topic-browser", "includes"),
    ("topic-memory", "topic-skills", "persists"),
    ("topic-tools", "topic-mcp", "interfaced_via"),
    
    # Article → Article semantic relationships
    ("demo-001", "demo-007", "complements"),      # Reliability + Debate
    ("demo-001", "demo-008", "informs"),          # Reliability limits inform Design
    ("demo-002", "demo-003", "parallels"),        # MCP parallels A2A
    ("demo-002", "demo-004", "enables"),          # MCP enables modular Skills
    ("demo-003", "demo-008", "necessitates"),     # A2A requires structured Topologies
    ("demo-004", "demo-005", "utilizes"),         # Skills utilize Memory
    ("demo-005", "demo-008", "constrains"),       # Memory patterns constrain Topologies
    ("demo-006", "demo-001", "requires"),         # Browser agents require Reliability
    ("demo-007", "demo-008", "informs"),          # Debate patterns inform topologies
    ("demo-009", "demo-001", "incorporates"),     # Code agents incorporate Error Recovery
    ("demo-009", "demo-006", "parallels"),        # Code agents parallel Browser Agents
    ("demo-010", "demo-001", "quantifies"),       # Eval quantifies Reliability
    ("demo-010", "demo-007", "measures"),         # Eval measures Debate efficacy
    ("demo-004", "demo-001", "enhances"),         # Modular skills enhance Reliability
]

# ── Demo Preferences ──────────────────────────────────────────────────────────

DEMO_PREFERENCES = {
    "interests": [],
    "sources": ["ArXiv", "GitHub Trending"],
    "briefing_frequency": "daily",
    "max_articles": 10,
}

# ── Demo Reading History ──────────────────────────────────────────────────────

DEMO_READING_HISTORY = []
for i, article in enumerate(DEMO_ARTICLES):
    DEMO_READING_HISTORY.append({
        "article_id": article["id"],
        "title": article["title"],
        "read_date": article["date"],
        "rating": min(5, max(1, int(article["relevance_score"] * 5))),
        "notes": "",
    })