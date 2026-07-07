"""
Personal Knowledge Concierge — Streamlit Frontend (v4 — OLED Dark & Containerized)
===============================================================================
A multi-agent system that curates, digests, and maps your daily reading.
"""

import base64
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from agents.coordinator import CoordinatorAgent
from memory.memory_store import MemoryStore
from utils.config import Config
from utils.demo_data import (
    DEMO_ARTICLES,
    DEMO_GRAPH_EDGES,
    DEMO_GRAPH_NODES,
    DEMO_PREFERENCES,
)

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Knowledge Concierge",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
# LIVE LOG INFRASTRUCTURE
# ═══════════════════════════════════════════════════════════════════════════════

class LogCapture(logging.Handler):
    MAX_ENTRIES = 200

    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.entries: list[dict[str, Any]] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.entries.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "level": record.levelname,
            "name": record.name,
            "message": self.format(record),
        })
        if len(self.entries) > self.MAX_ENTRIES:
            self.entries = self.entries[-self.MAX_ENTRIES:]

    def get_recent(self, count: int = 50) -> list[dict[str, Any]]:
        return self.entries[-count:]

    def clear(self) -> None:
        self.entries.clear()


def setup_agent_logging() -> LogCapture:
    capture = LogCapture()
    capture.setFormatter(logging.Formatter("%(message)s"))

    for name in ["agents", "mcp_server", "memory", "utils.llm_client"]:
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(capture)
        logger.propagate = True

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(capture)

    return capture


def log_agent_event(message: str, level: str = "INFO") -> None:
    logger = logging.getLogger("agents.coordinator")
    if level == "ERROR":
        logger.error(message)
    elif level == "WARNING":
        logger.warning(message)
    else:
        logger.info(message)


# ═══════════════════════════════════════════════════════════════════════════════
# CSS (Stripped down, OLED Dark, Minimalist)
# ═══════════════════════════════════════════════════════════════════════════════

st.html("""
<style>
/* ── Base Tokens (Warm Light Mode) ─────────────────────────────────── */
:root {
  --bg-deep: #F9F9F8;
  --bg-card: #FFFFFF;
  --border: #E4E4E7;
  --border-hover: #D4D4D8;
  --text-primary: #18181B;
  --text-secondary: #52525B;
  --text-muted: #A1A1AA;
  --accent: #3B82F6;
  --accent-soft: #3B82F615;
  --radius-sm: 6px;
  --radius: 8px;
}

/* Ensure the app and sidebar use the new background colors */
.stApp { background-color: var(--bg-deep); }
.stSidebar { background-color: #F0F0EE !important; border-right: 1px solid var(--border); }

/* ── HEADER BANNER (Flat & Clean) ──────────────────────────────────── */
.kc-header {
  padding: 12px 0 20px 0; 
  margin-bottom: 24px;
  border-bottom: 1px solid var(--border);
}
.kc-title {
  font-size: 1.4rem; font-weight: 700; letter-spacing: -0.02em;
  color: var(--text-primary); margin: 0 0 4px;
}
.kc-subtitle {
  font-size: 0.85rem; color: var(--text-secondary); margin: 0;
}

/* ── SOURCE BADGES ─────────────────────────────────────────────────── */
.src-badge {
  display: inline-block; padding: 2px 8px; border-radius: 4px;
  font-size: 0.65rem; font-weight: 600; text-transform: uppercase;
  background: #F4F4F5; color: var(--text-secondary); border: 1px solid var(--border);
}

/* ── RELEVANCE PILL ────────────────────────────────────────────────── */
.score-pill {
  display: inline-block; padding: 2px 8px; border-radius: 4px;
  font-size: 0.65rem; font-weight: 600;
  background: #EFF6FF; color: #2563EB; border: 1px solid #BFDBFE;
}

/* ── INTEREST CHIPS ────────────────────────────────────────────────── */
.chip {
  display: inline-block; padding: 4px 12px; border-radius: var(--radius-sm);
  margin: 3px 6px 3px 0; font-size: 0.75rem; font-weight: 500;
  background: #FFFFFF; border: 1px solid #D4D4D8; color: #3F3F46;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

/* ── TL;DR CALLOUT ─────────────────────────────────────────────────── */
.tldr {
  border-left: 2px solid var(--accent);
  padding: 12px 16px; margin: 12px 0;
  background: #F4F4F5; color: #3F3F46; font-size: 0.85rem; line-height: 1.6;
}
.tldr strong { color: var(--text-primary); font-weight: 600; }

/* ── ARTICLE CARD ──────────────────────────────────────────────────── */
.article-card {
  background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 16px; margin-bottom: 12px;
  cursor: pointer; transition: all 0.15s ease;
}
.article-card:hover { border-color: var(--border-hover); background: #FAFAFA; }
.article-card.selected { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }
.article-card-title {
  font-size: 0.9rem; font-weight: 600; color: var(--text-primary); margin-bottom: 8px;
}
.article-card-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.article-card-tldr { font-size: 0.75rem; color: var(--text-secondary); line-height: 1.5; margin-top: 8px; }

/* ── META LINE ─────────────────────────────────────────────────────── */
.article-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 16px;}
.meta-sep { color: var(--border-hover); font-size: 0.8rem; }

/* ── STAT ROW ──────────────────────────────────────────────────────── */
.stat-row { display: flex; gap: 40px; margin: 8px 0 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }
.stat-item { text-align: left; }
.stat-value { font-size: 1.5rem; font-weight: 700; color: var(--text-primary); font-family: 'JetBrains Mono', monospace; }
.stat-label { font-size: 0.65rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; }

/* ── STATUS DOT ────────────────────────────────────────────────────── */
.dot      { display: inline-block; width: 6px; height: 6px; border-radius: 50%; margin-right: 6px; }
.dot-live { background: #10B981; }
.dot-demo { background: #F59E0B; }
.dot-off  { background: #EF4444; }

/* ── LOG PANEL (True Terminal Look) ────────────────────────────────── */
.log-panel {
  background: #000000; border: 1px solid #27272A; border-radius: var(--radius-sm);
  padding: 12px; margin-top: 8px;
  max-height: 260px; overflow-y: auto;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.65rem; line-height: 1.6;
}
.log-panel::-webkit-scrollbar { width: 4px; }
.log-panel::-webkit-scrollbar-thumb { background: #3F3F46; border-radius: 2px; }
.log-entry { margin-bottom: 4px; white-space: pre-wrap; word-break: break-all; color: #A1A1AA; }
.log-time { color: #52525B; margin-right: 8px; }
.log-tag  { display: inline-block; font-size: 0.55rem; padding: 0 4px; border-radius: 2px; margin-right: 8px; font-weight: 600; text-transform: uppercase; background: #18181B; border: 1px solid #27272A;}
.log-tag-info  { color: #3B82F6; }
.log-tag-warn  { color: #F59E0B; }
.log-tag-error { color: #EF4444; }
.log-tag-llm   { color: #8B5CF6; }
.log-tag-tool  { color: #10B981; }

/* ── SOURCE-SPECIFIC BADGES ──────────────────────────────────────────── */
.src-arxiv  { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }
.src-github { background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; }

/* ── BRAND (Sidebar) ────────────────────────────────────────────────── */
.brand { font-size: 0.95rem; font-weight: 700; color: #18181B; margin-bottom: 2px; }
.brand-sub { font-size: 0.7rem; color: #71717A; margin-bottom: 16px; }

/* ── EMPTY STATE ─────────────────────────────────────────────────────── */
.empty-state {
  text-align: center; padding: 40px 20px;
  border: 1px dashed var(--border); border-radius: var(--radius);
  color: #71717A; font-size: 0.88rem; line-height: 1.6;
}

/* ── SECTION HEADER ──────────────────────────────────────────────────── */
.section-header {
  display: flex; align-items: baseline; justify-content: space-between;
  margin-bottom: 12px;
}
.section-title { font-size: 0.95rem; font-weight: 600; color: #18181B; }
.section-count { font-size: 0.75rem; color: #71717A; }

/* ── SCROLLABLE CONTENT ──────────────────────────────────────────────── */
.content-panel {
  max-height: 680px; overflow-y: auto;
  padding-right: 8px;
}
.content-panel::-webkit-scrollbar { width: 4px; }
.content-panel::-webkit-scrollbar-track { background: transparent; }
.content-panel::-webkit-scrollbar-thumb { background: #D4D4D8; border-radius: 2px; }

/* ── CONCEPT CARD ────────────────────────────────────────────────────── */
.concept-card {
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 15px 18px; height: 100%;
  transition: border-color 0.2s;
}
.concept-card:hover { border-color: var(--border-hover); }
.concept-icon  { font-size: 1.5rem; margin-bottom: 7px; display: block; }
.concept-title { font-size: 0.84rem; font-weight: 600; color: #18181B; margin-bottom: 5px; }
.concept-desc  { font-size: 0.74rem; color: #71717A; line-height: 1.55; }

/* ── RELATED PILLS ───────────────────────────────────────────────────── */
.related-pill {
  display: inline-block; background: #F4F4F5; border: 1px solid #E4E4E7;
  border-radius: 20px; padding: 2px 13px; font-size: 0.72rem;
  color: #52525B; margin: 2px 4px;
}

/* ── ZOOM HINT ───────────────────────────────────────────────────────── */
.zoom-hint {
  font-size: 0.7rem; color: #52525B; text-align: center; margin-top: 4px;
  letter-spacing: 0.02em;
}

/* ── IFRAME & DIVIDER POLISH ─────────────────────────────────────────── */
iframe { border-radius: 10px !important; border: 1px solid var(--border) !important; }
hr { border-color: var(--border) !important; margin: 14px 0 !important; }

/* ── NAV ACTIVE ──────────────────────────────────────────────────────── */
.nav-active {
  background: #3B82F618; border: 1px solid #3B82F644; border-radius: 8px;
  padding: 8px 12px; margin: 2px 0;
  color: #18181B; font-weight: 600; font-size: 0.85rem;
}
</style>
""")

# ═══════════════════════════════════════════════════════════════════════════════
# VISUALIZATION HELPERS — using st.iframe(data URI) for JS-dependent content
# ═══════════════════════════════════════════════════════════════════════════════

def render_mermaid_zoomable(diagram: str, height: int = 500) -> None:
    """Render Mermaid.js diagram in an iframe with zoom & pan support."""
    safe = diagram.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
    srcdoc = f"""<!DOCTYPE html><html><head>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 0; background: #F9F9F8; overflow: hidden; font-family: sans-serif; }}
  #wrap {{ width: 100%; height: {height}px; position: relative; }}
  .mermaid {{ display: flex; justify-content: center; padding-top: 8px; }}
  .mermaid svg {{ max-width: none !important; }}
  .ztb {{
    position: absolute; bottom: 10px; right: 10px; display: flex; gap: 5px; z-index: 200;
  }}
  .zbtn {{
    background: #FFFFFF; border: 1px solid #D4D4D8; color: #52525B;
    border-radius: 7px; padding: 5px 13px; font-size: 13px;
    cursor: pointer; user-select: none; transition: background 0.15s;
  }}
  .zbtn:hover {{ background: #F4F4F5; color: #18181B; }}
  .hint {{
    position: absolute; bottom: 12px; left: 12px;
    font-size: 10px; color: #52525B; pointer-events: none;
  }}
</style>
</head><body>
<div id="wrap">
  <div class="mermaid" id="diag">{safe}</div>
  <div class="ztb">
    <button class="zbtn" id="zin" title="Zoom in">＋</button>
    <button class="zbtn" id="zout" title="Zoom out">－</button>
    <button class="zbtn" id="zfit" title="Fit to screen">↺ Fit</button>
  </div>
  <div class="hint">Scroll to zoom · Drag to pan</div>
</div>
<script>
var pz = null;
mermaid.initialize({{
  startOnLoad: false, theme: 'neutral',
  themeVariables: {{
    primaryColor: '#EFF6FF', primaryTextColor: '#18181B',
    secondaryColor: '#FFFFFF', tertiaryColor: '#F9F9F8',
    lineColor: '#A1A1AA', fontSize: '13px',
    edgeLabelBackground: '#FFFFFF',
  }}
}});
document.addEventListener('DOMContentLoaded', function() {{
  mermaid.run({{
    querySelector: '#diag',
    postRenderCallback: function() {{
      var svg = document.querySelector('#diag svg');
      if (!svg) return;
      svg.setAttribute('width', '100%');
      svg.style.height = '{height - 40}px';
      try {{
        pz = svgPanZoom(svg, {{
          zoomEnabled: true, panEnabled: true, controlIconsEnabled: false,
          fit: true, center: true, minZoom: 0.05, maxZoom: 30,
          mouseWheelZoomEnabled: true, preventMouseEventsDefault: false,
        }});
      }} catch(e) {{ console.warn('svg-pan-zoom init failed:', e); }}
    }}
  }});
}});
document.getElementById('zin').onclick  = function() {{ pz && pz.zoomIn(); }};
document.getElementById('zout').onclick = function() {{ pz && pz.zoomOut(); }};
document.getElementById('zfit').onclick = function() {{ if (pz) {{ pz.fit(); pz.center(); }} }};
</script>
</body></html>"""
    data_uri = "data:text/html;base64," + base64.b64encode(srcdoc.encode()).decode()
    st.iframe(src=data_uri, height=height)


def render_knowledge_graph_vis(graph_data: dict, height: int = 640) -> None:
    """Render interactive knowledge graph using vis.js Network in an iframe."""
    nodes_raw = graph_data.get("nodes", [])
    edges_raw = graph_data.get("edges", [])

    NODE_STYLES = {
        "topic": {
            "color": {"background": "#E0E7FF", "border": "#818CF8",
                      "highlight": {"background": "#C7D2FE", "border": "#6366F1"},
                      "hover": {"background": "#C7D2FE", "border": "#6366F1"}},
            "shape": "ellipse", "mass": 2.5,
        },
        "article": {
            "color": {"background": "#D1FAE5", "border": "#6EE7B7",
                      "highlight": {"background": "#A7F3D0", "border": "#34D399"},
                      "hover": {"background": "#A7F3D0", "border": "#34D399"}},
            "shape": "box", "mass": 1,
        },
        "concept": {
            "color": {"background": "#FEE2E2", "border": "#FCA5A5",
                      "highlight": {"background": "#FECACA", "border": "#F87171"},
                      "hover": {"background": "#FECACA", "border": "#F87171"}},
            "shape": "diamond", "mass": 1,
        },
    }
    DEFAULT_STYLE = NODE_STYLES["concept"]

    vis_nodes = []
    for n in nodes_raw:
        ntype = n.get("type", "concept")
        style = NODE_STYLES.get(ntype, DEFAULT_STYLE)
        vis_nodes.append({
            "id": n["id"], "label": n["label"],
            "title": f"<b>{n['label']}</b><br><small>{ntype}</small>",
            "color": style["color"], "shape": style["shape"], "mass": style["mass"],
            "font": {"color": "#18181B", "size": 13, "face": "Inter, sans-serif"},
            "borderWidth": 2, "margin": 10,
        })

    vis_edges = []
    for e in edges_raw:
        vis_edges.append({
            "from": e["source"], "to": e["target"],
            "label": e.get("relation", ""),
            "color": {"color": "#D4D4D8", "highlight": "#3B82F6", "hover": "#6090FF"},
            "font": {"color": "#71717A", "size": 9, "face": "Inter, sans-serif",
                     "background": "#FFFFFF"},
            "arrows": {"to": {"enabled": True, "scaleFactor": 0.55}},
            "smooth": {"type": "dynamic"}, "width": 1.5,
        })

    nodes_json = json.dumps(vis_nodes)
    edges_json = json.dumps(vis_edges)

    srcdoc = f"""<!DOCTYPE html><html><head>
<script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.9/dist/vis-network.min.js"></script>
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/vis-network@9.1.9/dist/dist/vis-network.min.css">
<style>
  * {{ box-sizing: border-box; font-family: Inter, sans-serif; }}
  body {{ margin: 0; background: #F9F9F8; }}
  #net {{
    width: 100%; height: {height}px;
    border: 1px solid #E4E4E7; border-radius: 10px; background: #FFFFFF;
  }}
  .tb {{
    position: absolute; top: 10px; right: 10px;
    display: flex; gap: 5px; z-index: 100;
  }}
  .tbtn {{
    background: #FFFFFF; border: 1px solid #D4D4D8; color: #52525B;
    border-radius: 7px; padding: 5px 12px; font-size: 11px;
    cursor: pointer; user-select: none; transition: background 0.15s;
  }}
  .tbtn:hover {{ background: #F4F4F5; color: #18181B; }}
  .legend {{
    position: absolute; bottom: 10px; left: 10px; z-index: 100;
    background: #FFFFFFee; border: 1px solid #E4E4E7;
    border-radius: 8px; padding: 10px 14px;
    font-size: 11px; color: #52525B; line-height: 2;
  }}
  .ldot {{
    display: inline-block; width: 10px; height: 10px;
    border-radius: 50%; margin-right: 6px; vertical-align: middle;
  }}
  .ldia {{
    display: inline-block; width: 10px; height: 10px;
    transform: rotate(45deg); margin-right: 8px; vertical-align: middle;
  }}
  .hint {{
    position: absolute; top: 12px; left: 12px;
    font-size: 10px; color: #3F3F46; pointer-events: none;
  }}
</style>
</head><body>
<div style="position: relative;">
  <div id="net"></div>
  <div class="tb">
    <button class="tbtn" id="fitBtn">⤢ Fit all</button>
    <button class="tbtn" id="zinBtn">＋</button>
    <button class="tbtn" id="zoutBtn">－</button>
    <button class="tbtn" id="physBtn">⏸ Freeze</button>
  </div>
  <div class="legend">
    <span class="ldot" style="background:#5A4FCC;"></span>Topic<br>
    <span class="ldot" style="background:#0A7A48; border-radius:2px;"></span>Article<br>
    <span class="ldia" style="background:#8B3520;"></span>Concept
  </div>
  <div class="hint">Scroll to zoom · Drag background to pan · Drag nodes to rearrange</div>
</div>
<script>
var nodes   = new vis.DataSet({nodes_json});
var edges   = new vis.DataSet({edges_json});
var options = {{
  physics: {{
    enabled: true,
    barnesHut: {{
      gravitationalConstant: -4500, centralGravity: 0.2,
      springLength: 160, springConstant: 0.04, damping: 0.12,
    }},
    stabilization: {{ iterations: 250, updateInterval: 30 }},
  }},
  interaction: {{
    hover: true, tooltipDelay: 120,
    zoomView: true, dragView: true, dragNodes: true,
    multiselect: false, navigationButtons: false,
    keyboard: {{ enabled: true, speed: {{x: 10, y: 10, zoom: 0.02}} }},
  }},
  layout: {{ improvedLayout: true }},
}};
var net = new vis.Network(document.getElementById('net'), {{ nodes, edges }}, options);
var physOn = true;
document.getElementById('fitBtn').onclick = function() {{
  net.fit({{ animation: {{ duration: 600, easingFunction: 'easeInOutQuad' }} }});
}};
document.getElementById('zinBtn').onclick = function() {{
  net.moveTo({{ scale: net.getScale() * 1.35,
               animation: {{ duration: 300, easingFunction: 'easeInOutQuad' }} }});
}};
document.getElementById('zoutBtn').onclick = function() {{
  net.moveTo({{ scale: net.getScale() * 0.75,
               animation: {{ duration: 300, easingFunction: 'easeInOutQuad' }} }});
}};
document.getElementById('physBtn').onclick = function() {{
  physOn = !physOn;
  net.setOptions({{ physics: {{ enabled: physOn }} }});
  this.textContent = physOn ? '⏸ Freeze' : '▶ Unfreeze';
}};
</script>
</body></html>"""
    data_uri = "data:text/html;base64," + base64.b64encode(srcdoc.encode()).decode()
    st.iframe(src=data_uri, height=height + 10)


# ── Badge / chip helpers ──────────────────────────────────────────────────────

SRC_CLASS = {
    "ArXiv": "src-arxiv",
    "GitHub Trending": "src-github",
}
# ── Badge / chip helpers (Light Theme) ───────────────────────────

def source_badge(source: str) -> str:
    return (
        f'<span class="src-badge" style="'
        f'background:#F4F4F5; border:1px solid #E4E4E7; color:#52525B;'
        f'">{source}</span>'
    )


def score_pill(score: float) -> str:
    return (
        f'<span class="score-pill" style="'
        f'background:#EFF6FF; border:1px solid #BFDBFE; color:#2563EB;'
        f'">{score:.0%} match</span>'
    )


def interest_chips(interests: list[str]) -> str:
    parts = []
    for topic in interests:
        parts.append(
            f'<span class="chip" style="'
            f'background:#FFFFFF; border:1px solid #D4D4D8; color:#3F3F46;'
            f'box-shadow: 0 1px 2px rgba(0,0,0,0.05);'
            f'">{topic}</span>'
        )
    return "".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICES & SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def init_services():
    memory = MemoryStore()
    if Config.DEMO_MODE:
        stats = memory.get_stats()
        if stats["total_readings"] == 0:
            memory.save_preferences(DEMO_PREFERENCES)
            for node in DEMO_GRAPH_NODES:
                memory.add_graph_node(node["id"], node["label"], node["type"], node.get("group", "default"))
            for src, tgt, rel in DEMO_GRAPH_EDGES:
                memory.upsert_graph_edge(src, tgt, rel)
            for article in DEMO_ARTICLES:
                memory.add_reading({
                    "id": article["id"], "title": article["title"],
                    "source": article["source"], "topics": article["topics"],
                    "tl_dr": article["tl_dr"], "date": article["date"],
                    "source_url": article["source_url"],
                })
    coordinator = CoordinatorAgent(memory_store=memory)
    return coordinator, memory

coordinator, memory = init_services()

if "log_capture" not in st.session_state:
    st.session_state.log_capture = setup_agent_logging()

log_cap: LogCapture = st.session_state.log_capture

_defaults = {
    "briefing_result": None,
    "pipeline_running": False,
    "selected_article": None,
    "mindmap_topic": "Agent Architecture",
    "nav_page": "Interests",
    "selected_briefing_id": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Cleaned up
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### Personal Knowledge Concierge")
    
    # Minimal status
    if Config.DEMO_MODE:
        st.html('<div style="font-size: 0.75rem; color: #A1A1AA; margin-bottom: 24px;"><span class="dot dot-demo"></span>Demo Mode</div>')
    elif Config.API_KEY:
        st.html(f'<div style="font-size: 0.75rem; color: #A1A1AA; margin-bottom: 24px;"><span class="dot dot-live"></span>Live: {Config.MODEL}</div>')
    else:
        st.html('<div style="font-size: 0.75rem; color: #A1A1AA; margin-bottom: 24px;"><span class="dot dot-off"></span>No API Key</div>')

    nav_items = {
        "⚙️ Configuration": "Interests",
        "📰 Daily Briefing": "Daily Briefing",
        "🗺️ Knowledge Graph": "Knowledge Graph",
        "📚 Memory Base": "History",
        "ℹ️ About": "About",
    }

    for label, page_id in nav_items.items():
        if st.button(label, key=f"nav_{page_id}", type="primary" if st.session_state.nav_page == page_id else "secondary", use_container_width=True):
            st.session_state.nav_page = page_id
            st.rerun()

    st.divider()

    # ── Live Log Panel ──────────────────────────────────────────────────────
    st.markdown("**Agent Log**", help="Real-time MCP and LLM execution logs")
    
    # Render log entries
    entries = log_cap.get_recent(60)
    log_html = '<div class="log-panel" id="log-panel">'
    if not entries:
        log_html += '<span>Awaiting execution...</span>'
    else:
        for entry in entries:
            level = entry["level"]
            tag_text, tag_class = "SYS", "log-tag-info"
            msg_lower = entry["message"].lower()
            if any(kw in msg_lower for kw in ["llm", "api call", "token"]):
                tag_text, tag_class = "LLM", "log-tag-llm"
            elif any(kw in msg_lower for kw in ["tool", "mcp", "fetch", "search"]):
                tag_text, tag_class = "MCP", "log-tag-tool"
            elif level == "ERROR":
                tag_text, tag_class = "ERR", "log-tag-error"
            elif level == "WARNING":
                tag_text, tag_class = "WRN", "log-tag-warn"

            log_html += (
                f'<div class="log-entry">'
                f'<span class="log-time">{entry["time"]}</span>'
                f'<span class="log-tag {tag_class}">{tag_text}</span>'
                f'{entry["message"]}</div>'
            )
    log_html += '</div>'
    st.html(log_html)

    if st.button("Clear Logs", key="clear_logs", use_container_width=True):
        log_cap.clear()
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN HEADER
# ═══════════════════════════════════════════════════════════════════════════════

st.html("""
<div class="kc-header">
  <h1 class="kc-title">🧠 Personal Knowledge Concierge</h1>
  <p class="kc-subtitle">Autonomous agent pipeline for reading curation and knowledge synthesis.</p>
</div>
""")

page = st.session_state.nav_page

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: INTERESTS (Using explicit containers)
# ═══════════════════════════════════════════════════════════════════════════════

if page == "Interests":
    # ── Curated example topics for the demo domain ────────────────────────────────
    EXAMPLE_TOPICS = [
        "Agent Architecture", "MCP Protocol", "Multi-Agent Systems",
        "RAG & Memory", "Tool Integration", "Design Patterns",
        "Evaluation", "Reliability", "Code Generation",
        "Web Automation", "Reasoning & Debate", "LLM Security",
    ]

    left, right = st.columns([3, 2], gap="large")

    with left:
        with st.container(border=True):
            st.markdown("#### 🎯 Reading Interests")
            st.caption("Keywords used by the Curator Agent to score articles.")

            prefs = memory.get_preferences() or DEMO_PREFERENCES
            current: list[str] = list(prefs.get("interests", []))

            # ── 1) Add custom topic ──────────────────────────────────────────
            ac1, ac2 = st.columns([4, 1])
            with ac1:
                new = st.text_input(
                    "Add Topic", placeholder="e.g. Agent Architecture, MCP...",
                    label_visibility="collapsed", key="interest_input",
                )
            with ac2:
                add_btn = st.button("Add", type="secondary", use_container_width=True)

            if add_btn and new and new.strip() not in current:
                current.append(new.strip())
                memory.save_preferences({"interests": current})
                log_agent_event(f"Added interest: {new.strip()}")
                st.rerun()

            # ── 2) Quick-pick from examples ──────────────────────────────────
            st.caption("or pick from these examples:")
            cols_per_row = 3
            for i in range(0, len(EXAMPLE_TOPICS), cols_per_row):
                ex_cols = st.columns(cols_per_row)
                for j, topic in enumerate(EXAMPLE_TOPICS[i:i + cols_per_row]):
                    with ex_cols[j]:
                        already = topic in current
                        label = f"✓ {topic}" if already else topic
                        if st.button(
                            label, key=f"ex_{topic}",
                            type="tertiary",
                            disabled=already,
                            use_container_width=True,
                        ):
                            if topic not in current:
                                current.append(topic)
                                memory.save_preferences({"interests": current})
                                log_agent_event(f"Added interest: {topic}")
                                st.rerun()

            # ── 3) Currently selected topics (with per-chip ✕ delete) ────────
            st.divider()
            st.caption(
                f"**Selected topics/keywords**  ({len(current)} selected)"
                if current else
                "**Selected topics/keywords**  (_none yet — add above or pick from examples_)"
            )
            for idx, topic in enumerate(current):
                cc1, cc2 = st.columns([14, 1])
                with cc1:
                    st.html(interest_chips([topic]))
                with cc2:
                    if st.button("✕", key=f"del_{idx}_{topic}", type="tertiary",
                                 help=f"Remove '{topic}'"):
                        current.remove(topic)
                        memory.save_preferences({"interests": current})
                        log_agent_event(f"Removed interest: {topic}")
                        st.rerun()

    with right:
        with st.container(border=True):
            st.markdown("#### 📡 Data Sources")
            sources_current = prefs.get("sources", ["ArXiv", "GitHub Trending"])

            src_col1, src_col2 = st.columns(2)
            with src_col1:
                arxiv = st.checkbox("ArXiv", value="ArXiv" in sources_current)
            with src_col2:
                github = st.checkbox("GitHub Trending", value="GitHub Trending" in sources_current)

            st.divider()
            max_n = st.slider("Max articles per run", 3, 20, prefs.get("max_articles", 10))

            c_save = st.columns([1, 1])
            with c_save[0]:
                if st.button("💾 Save Configuration", type="secondary", use_container_width=True):
                    srcs = []
                    if arxiv: srcs.append("ArXiv")
                    if github: srcs.append("GitHub Trending")
                    memory.save_preferences({"interests": current, "sources": srcs, "max_articles": max_n})
                    st.toast("Configuration saved ✅")
                    st.rerun()

        # Discover Sources Expander — default open
        with st.expander("🔍 Discover New Sources via MCP", expanded=True):
            st.caption("Let the agent discover new sources based on your configuration.")
            rec_type = st.radio("Method", ["Pre-defined catalog", "Web search", "LLM suggestions"], label_visibility="collapsed")
            if st.button("Run Discovery Agent"):
                 st.info("Discovery agent execution triggered (Demo logic here)")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DAILY BRIEFING
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Daily Briefing":
    
    header_col, action_col = st.columns([3, 1], vertical_alignment="bottom")
    with header_col:
        st.markdown("#### Agent Pipeline Execution")
    with action_col:
        if st.button("▶ Run Pipeline", type="primary", use_container_width=True, disabled=st.session_state.pipeline_running):
            st.session_state.pipeline_running = True
            st.session_state.briefing_result = None
            st.session_state.selected_briefing_id = None
            st.rerun()

    # ── Pipeline running ──────────────────────────────────────────────────────
    if st.session_state.pipeline_running:
        prefs = memory.get_preferences() or DEMO_PREFERENCES
        st.divider()

        bar = st.progress(0, "Initialising pipeline...")
        stat = st.empty()

        s1col, s2col, s3col = st.columns(3)
        with s1col:
            stage1 = st.empty()
            stage1.info("🔍 Curator — searching sources...")
        with s2col:
            stage2 = st.empty()
            stage2.info("📝 Summarizer — waiting...")
        with s3col:
            stage3 = st.empty()
            stage3.info("🗺️ Graph Builder — waiting...")

        stat.caption("Stage 1 / 3 · Curator Agent")
        bar.progress(10)
        log_agent_event("Stage 1: Curator fetching articles...")

        result = coordinator.run_pipeline(
            interests=prefs.get("interests"),
            sources=prefs.get("sources"),
            max_articles=prefs.get("max_articles", 10),
        )
        stages = result.get("pipeline_stages", {})

        # Stage 1
        s1_ok = stages.get("curation", {}).get("status") == "completed"
        if s1_ok:
            n_found = stages["curation"]["articles_found"]
            stage1.success(f"✅ Curator — {n_found} articles")
            log_agent_event(f"Stage 1 complete: {n_found} articles found")
        else:
            stage1.error("❌ Curator failed")
            log_agent_event("Stage 1 FAILED", "ERROR")

        bar.progress(40)
        stat.caption("Stage 2 / 3 · Summarizer Agent")
        stage2.info("📝 Summarizer — digesting articles...")
        log_agent_event("Stage 2: Summarizer digesting articles...")

        s2_ok = stages.get("summarization", {}).get("status") == "completed"
        if s2_ok:
            n_dig = stages["summarization"]["articles_digested"]
            stage2.success(f"✅ Summarizer — {n_dig} digested")
            log_agent_event(f"Stage 2 complete: {n_dig} articles digested")
        else:
            stage2.error("❌ Summarizer failed")
            log_agent_event("Stage 2 FAILED", "ERROR")

        bar.progress(70)
        stat.caption("Stage 3 / 3 · Graph Builder Agent")
        stage3.info("🗺️ Graph Builder — mapping connections...")
        log_agent_event("Stage 3: Graph Builder mapping connections...")

        s3_ok = stages.get("graph_building", {}).get("status") == "completed"
        if s3_ok:
            n_nodes = stages["graph_building"]["graph_nodes"]
            stage3.success(f"✅ Graph Builder — {n_nodes} nodes")
            log_agent_event(f"Stage 3 complete: {n_nodes} graph nodes")
        else:
            stage3.error("❌ Graph Builder failed")
            log_agent_event("Stage 3 FAILED", "ERROR")

        bar.progress(100)
        stat.empty()
        log_agent_event("Pipeline finished successfully")
        st.toast("Briefing ready ✅")

        st.session_state.briefing_result = result
        st.session_state.pipeline_running = False
        st.rerun()

    # ── Show results ──────────────────────────────────────────────────────────
    if st.session_state.briefing_result is None:
        st.html(
            '<div class="empty-state">'
            'No briefing generated yet.<br>'
            'Click <b>▶ Run Pipeline</b> to run the agent pipeline '
            'and discover articles tailored to your interests.'
            '</div>'
        )
    else:
        result = st.session_state.briefing_result
        digested = result.get("digested", [])

        st.divider()

        topics_found: set[str] = set()
        for a in digested:
            for t in a.get("topics", []):
                topics_found.add(t)

        st.html(
            f'<div class="stat-row">'
            f'<div class="stat-item"><div class="stat-value">{len(digested)}</div>'
            f'<div class="stat-label">Articles</div></div>'
            f'<div class="stat-item"><div class="stat-value">{len(topics_found)}</div>'
            f'<div class="stat-label">Topics</div></div>'
            f'<div class="stat-item"><div class="stat-value">'
            f'{result.get("graph", {}).get("total_nodes", 0)}</div>'
            f'<div class="stat-label">Graph Nodes</div></div>'
            f'</div>'
        )

        st.divider()

        # Master-Detail Layout
        list_col, detail_col = st.columns([1, 2], gap="medium")

        with list_col:
            st.html('<div class="section-header">'
                    '<span class="section-title">Curated Articles</span>'
                    f'<span class="section-count">{len(digested)} found</span>'
                    '</div>')

            if not st.session_state.selected_briefing_id and digested:
                st.session_state.selected_briefing_id = digested[0].get("id", "")

            for i, article in enumerate(digested):
                aid = article.get("id", article.get("title", ""))
                title = article.get("title", "Untitled")
                src = article.get("source", "")
                score = article.get("relevance_score", 0)
                tl_dr = article.get("tl_dr", "")
                selected = st.session_state.selected_briefing_id == aid

                card_class = "article-card selected" if selected else "article-card"

                card_html = (
                    f'<div class="{card_class}">'
                    f'<div class="article-card-title">{title}</div>'
                    f'<div class="article-card-meta">'
                    f'{source_badge(src)} {score_pill(score)}'
                    f'</div>'
                )
                if tl_dr:
                    card_html += (
                        f'<div class="article-card-tldr">'
                        f'<strong>TL;DR</strong> {tl_dr[:180]}{"..." if len(tl_dr) > 180 else ""}'
                        f'</div>'
                    )
                card_html += '</div>'
                st.html(card_html)

                if st.button(
                    "Read full digest →", key=f"briefing_select_{i}_{aid}",
                    type="secondary", use_container_width=True,
                ):
                    st.session_state.selected_briefing_id = aid
                    st.rerun()

        with detail_col:
            selected_article = None
            for a in digested:
                a_id = a.get("id", a.get("title", ""))
                if a_id == st.session_state.selected_briefing_id:
                    selected_article = a
                    break

            if selected_article is None:
                st.info("Select an article from the list to read its full digest.")
            else:
                title = selected_article.get("title", "Untitled")
                src = selected_article.get("source", "")
                score = selected_article.get("relevance_score", 0)
                date = selected_article.get("date", "")
                topics = ", ".join(selected_article.get("topics", []))
                url = selected_article.get("source_url", "")

                st.html(
                    f'<div style="margin-bottom:8px;">'
                    f'<div class="article-meta">'
                    f'{source_badge(src)} {score_pill(score)}'
                    f'<span class="meta-sep">·</span>'
                    f'<span style="color:#71717A;font-size:0.78rem;">{date}</span>'
                    f'<span class="meta-sep">·</span>'
                    f'<span style="color:#71717A;font-size:0.78rem;">{topics}</span>'
                    f'</div></div>'
                )

                if url:
                    st.markdown(f"[↗ Open original source]({url})")

                tl_dr = selected_article.get("tl_dr", "")
                if tl_dr:
                    st.html(f'<div class="tldr"><strong>TL;DR</strong> — {tl_dr}</div>')

                full = selected_article.get("full_summary", "")
                if full:
                    st.markdown("### Full Digest")
                    st.html('<div class="content-panel">')
                    st.markdown(full)
                    st.html('</div>')

                related = selected_article.get("related_to", [])
                if related:
                    labels = [
                        da["title"] for rid in related
                        for da in DEMO_ARTICLES if da["id"] == rid
                    ]
                    if labels:
                        st.divider()
                        st.caption("Related reading")
                        pills = "".join(
                            f'<span class="related-pill">{lbl}</span>' for lbl in labels
                        )
                        st.html(pills)

        errors = result.get("errors", [])
        if errors:
            st.divider()
            for e in errors:
                st.warning(e)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: KNOWLEDGE GRAPH
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Knowledge Graph":
    st.subheader("Knowledge Graph")
    st.caption("Explore how concepts and articles interconnect across your reading history.")

    ctrl, viz = st.columns([1, 3], gap="large")

    with ctrl:
        graph = memory.get_graph()
        topics = sorted([
            n["label"] for n in graph.get("nodes", []) if n.get("type") == "topic"
        ])
        if not topics:
            topics = [
                "Agent Architecture", "Agent Protocols", "Multi-Agent Systems",
                "Agent Applications", "Agent Memory",
            ]

        st.markdown("**Central Topic**")
        selected_topic = st.selectbox(
            "Focus", topics, key="mindmap_topic", label_visibility="collapsed"
        )

        st.markdown("**View Mode**")
        view_mode = st.radio(
            "Layout",
            ["Network Graph", "Mind Map", "Statistics"],
            key="view_mode",
            label_visibility="collapsed",
        )

        st.divider()
        st.caption("🟣 Topic &nbsp; 🟢 Article &nbsp; 🔴 Concept")

        st.divider()
        st.markdown("**Relationship types**")
        for rel in ["about", "builds_on", "extends", "enables",
                    "complements", "applies", "contextualizes", "evaluates"]:
            st.caption(f"`{rel}`")

    with viz:
        graph = memory.get_graph()

        if view_mode == "Network Graph":
            render_knowledge_graph_vis(graph, height=640)
            st.html('<div class="zoom-hint">Drag nodes · Scroll to zoom · ⤢ Fit all to reset</div>')

        elif view_mode == "Mind Map":
            mm = coordinator.get_mindmap(selected_topic)
            if not mm or not mm.startswith("mindmap"):
                mm = f"mindmap\n  root(({selected_topic}))\n    (No data yet — generate a briefing first)"
            render_mermaid_zoomable(mm, height=620)
            st.html('<div class="zoom-hint">Scroll to zoom · Drag to pan · ↺ Fit to reset</div>')

        else:  # Statistics
            g = memory.get_graph()
            all_nodes = g.get("nodes", [])
            all_edges = g.get("edges", [])

            n1, n2 = st.columns(2)
            n1.metric("Total Nodes", len(all_nodes))
            n2.metric("Total Edges", len(all_edges))
            n1.metric("Topic Nodes", sum(1 for n in all_nodes if n.get("type") == "topic"))
            n2.metric("Article Nodes", sum(1 for n in all_nodes if n.get("type") == "article"))

            st.divider()
            st.markdown("**Node distribution by category**")
            groups: dict[str, int] = {}
            for n in all_nodes:
                gid = n.get("group", "other")
                groups[gid] = groups.get(gid, 0) + 1
            for gid, cnt in sorted(groups.items(), key=lambda x: -x[1]):
                st.caption(f"{gid}: {cnt}")

    st.divider()
    st.download_button(
        "⬇  Export Graph JSON",
        data=json.dumps(graph, indent=2),
        file_name="knowledge_graph.json",
        mime="application/json",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: HISTORY
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "History":
    st.subheader("Reading History")
    st.caption("Every article the Concierge has processed — searchable and filterable.")

    filter_col, results_col = st.columns([1, 3], gap="medium")

    with filter_col:
        query = st.text_input(
            "Search",
            placeholder="Search articles...",
            key="search_history",
            label_visibility="collapsed",
        )
        all_sources = ["All"] + sorted(
            {r.get("source", "") for r in memory.get_all_readings()}
        )
        src_filter = st.selectbox(
            "Source", all_sources, key="filter_source", label_visibility="collapsed"
        )

        readings = memory.search_readings(query) if query else memory.get_all_readings()
        if src_filter != "All":
            readings = [r for r in readings if r.get("source") == src_filter]

        all_topics: set[str] = set()
        for r in readings:
            for t in r.get("topics", []):
                all_topics.add(t)

        st.divider()
        st.html(
            f'<div class="stat-row" style="flex-direction:column;gap:10px;">'
            f'<div class="stat-item"><div class="stat-value">{len(readings)}</div>'
            f'<div class="stat-label">Articles</div></div>'
            f'<div class="stat-item"><div class="stat-value">'
            f'{len({r.get("source", "") for r in readings})}</div>'
            f'<div class="stat-label">Sources</div></div>'
            f'<div class="stat-item"><div class="stat-value">{len(all_topics)}</div>'
            f'<div class="stat-label">Topics</div></div>'
            f'</div>'
        )

        if query:
            st.caption(f"{len(readings)} result(s) for &ldquo;{query}&rdquo;")

    with results_col:
        readings = memory.search_readings(query) if query else memory.get_all_readings()
        if src_filter != "All":
            readings = [r for r in readings if r.get("source") == src_filter]

        if not readings:
            st.html(
                '<div class="empty-state">'
                'No reading history yet.<br>'
                'Generate a briefing to start building your knowledge base.'
                '</div>'
            )
        else:
            for i, reading in enumerate(readings):
                rid = reading.get("id", "")
                with st.container(border=True):
                    r1, r2 = st.columns([6, 1])
                    with r1:
                        st.markdown(f"**{reading.get('title', 'Untitled')}**")
                        st.caption(
                            f"{reading.get('date', reading.get('processed_at', ''))} · "
                            f"{reading.get('source', '')} · "
                            f"{', '.join(reading.get('topics', []))}"
                        )
                        tl = reading.get("tl_dr", "")
                        if tl:
                            st.markdown(f"*{tl[:220]}{'...' if len(tl) > 220 else ''}*")
                    with r2:
                        if st.button("Expand", key=f"hist_view_{i}_{rid}"):
                            st.session_state.selected_article = reading
                            st.rerun()

                    if (
                        st.session_state.selected_article
                        and st.session_state.selected_article.get("id") == rid
                    ):
                        sel = st.session_state.selected_article
                        st.divider()
                        st.markdown(f"### {sel.get('title', '')}")
                        st.caption(f"Source: {sel.get('source_url', sel.get('source', ''))}")
                        st.html(f'<div class="tldr"><strong>TL;DR</strong> — {sel.get("tl_dr", "No summary available.")}</div>')
                        st.markdown("**Topics:** " + ", ".join(sel.get("topics", [])))
                        st.markdown(sel.get("full_summary", ""))
                        if st.button("Close", key=f"hist_close_{i}_{rid}"):
                            st.session_state.selected_article = None
                            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ABOUT
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "About":
    st.subheader("About This Project")
    st.markdown(
        "**Personal Knowledge Concierge** is a Kaggle 5-Day AI Agents capstone submission "
        "under the **Concierge Agents** track. It demonstrates how a multi-agent system "
        "can automate the end-to-end workflow of content curation, digestion, and "
        "knowledge synthesis — all stored locally for full privacy."
    )

    st.divider()

    st.subheader("Course Concepts Demonstrated")
    st.caption("All 6 key concepts from the course are implemented in code or shown in the demo video.")

    concepts = [
        ("🤖", "Agent / Multi-agent (ADK)",
         "Coordinator orchestrates Curator → Summarizer → GraphBuilder in a strict pipeline. See `agents/`."),
        ("🔧", "MCP Server",
         "8 tools with JSON Schema validation, strict input contracts. See `mcp_server/server.py`."),
        ("📋", "Agent Skills (8 tools)",
         "Fetch, search, summarize, analyze, graph, mindmap, recommend, memory. See `mcp_server/server.py`."),
        ("🛡️", "Security Features",
         "Pre-commit secret scanning, `.env` isolation, STRIDE threat model. See `security/`."),
        ("🔍", "Source Discovery",
         "LLM-based and web-search-based source recommendation for any topic. See `server.py` → `recommend_sources`."),
        ("💡", "Vibe Coding",
         "Built iteratively with Claude Code as the primary agentic IDE across TDD cycles."),
    ]

    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(concepts):
        with cols[i % 3]:
            st.html(
                f'<div class="concept-card">'
                f'<span class="concept-icon">{icon}</span>'
                f'<div class="concept-title">{title}</div>'
                f'<div class="concept-desc">{desc}</div>'
                f'</div>'
            )
        if i % 3 == 2:
            st.write("")

    st.divider()

    # Architecture diagram — static text matching README
    st.subheader("System Architecture")
    st.caption("Coordinator → Curator → Summarizer → Graph Builder, connected through an MCP tool server.")

    arch_text = """\
┌──────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                    │
│    (Sidebar navigation · Live log monitor · Dark UI)     │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│                 Coordinator Agent (ADK)                  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │   Curator   │─▶│  Summarizer  │─▶│  Graph Builder   │ │
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
└──────────────────────────────────────────────────────────┘"""

    st.code(arch_text, language=None)


# ── Footer ────────────────────────────────────────────────────────────────────

st.divider()
f1, f2 = st.columns(2)
f1.caption(f"Mode: {'Demo 🟡' if Config.DEMO_MODE else 'Live 🟢'} · LLM: {Config.MODEL}")
f2.caption("Kaggle 5-Day AI Agents Capstone Project · Concierge Agents")