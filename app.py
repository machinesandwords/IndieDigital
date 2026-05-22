import streamlit as st
import anthropic
import json
import time
import csv
import io
import concurrent.futures
from datetime import datetime

st.set_page_config(
    page_title="Indie Digital",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&family=Source+Sans+3:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Source Sans 3', sans-serif; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1100px; }

/* ── Buttons ── */
.stButton > button {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    font-weight: 500;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    border: none;
    padding: 0.55rem 1.6rem;
    transition: all 0.2s;
    cursor: pointer;
}
.stButton > button:hover { opacity: 0.85; }

/* ── Module cards ── */
.module-card {
    border-radius: 8px;
    padding: 1.6rem;
    height: 220px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
}
.card-unlocked {
    background: #faf8f5;
    border: 1.5px solid #e8d8c8;
}
.card-locked {
    background: #f5f5f5;
    border: 1.5px solid #ddd;
}
.card-coming {
    background: #f0f4f8;
    border: 1.5px dashed #c5d5e8;
}
.card-icon { font-size: 1.8rem; margin-bottom: 0.4rem; }
.card-title {
    font-family: 'Lora', serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: #2d2418;
    margin-bottom: 0.3rem;
}
.card-title-locked { color: #888; }
.card-desc { font-size: 0.83rem; color: #6b5c50; line-height: 1.5; }
.card-desc-locked { font-size: 0.83rem; color: #999; line-height: 1.5; }
.card-desc-coming { font-size: 0.83rem; color: #7a90a8; line-height: 1.5; font-style: italic; }
.lock-badge {
    position: absolute;
    top: 1rem; right: 1rem;
    font-size: 1rem;
    color: #bbb;
}

/* ── Verdict ── */
.verdict-green { background:#f0faf0; border:2px solid #27ae60; border-radius:6px; padding:1.2rem 1.5rem; margin-bottom:1rem; }
.verdict-yellow { background:#fffbf0; border:2px solid #e67e22; border-radius:6px; padding:1.2rem 1.5rem; margin-bottom:1rem; }
.verdict-red { background:#fdf5f5; border:2px solid #c0392b; border-radius:6px; padding:1.2rem 1.5rem; margin-bottom:1rem; }
.signal-green { color:#27ae60; font-weight:700; }
.signal-yellow { color:#e67e22; font-weight:700; }
.signal-red { color:#c0392b; font-weight:700; }
.conf-high { color:#27ae60; font-family:'IBM Plex Mono',monospace; font-size:0.78rem; }
.conf-medium { color:#e67e22; font-family:'IBM Plex Mono',monospace; font-size:0.78rem; }
.conf-low { color:#c0392b; font-family:'IBM Plex Mono',monospace; font-size:0.78rem; }
.dim-summary { font-size:0.9rem; color:#4a3f35; line-height:1.6; margin-top:0.4rem; }
.evidence-item { font-size:0.82rem; color:#6b5c50; font-family:'IBM Plex Mono',monospace; border-left:2px solid #e8d8c8; padding-left:0.75rem; margin-bottom:0.4rem; line-height:1.5; }
.overall-verdict { font-family:'Lora',serif; font-size:1.5rem; font-weight:600; color:#2d2418; }
.overall-sub { font-size:0.88rem; color:#6b5c50; margin-top:0.3rem; line-height:1.5; }
.idea-chip { background:#f5ede0; border-radius:4px; padding:0.7rem 1.1rem; font-size:0.82rem; color:#4a3f35; margin-bottom:1.2rem; font-family:'IBM Plex Mono',monospace; }

/* ── Scanner/Detector ── */
.badge { display:inline-block; padding:2px 10px; border-radius:3px; font-size:0.73rem; font-weight:600; letter-spacing:0.06em; margin-right:6px; }
.badge-high { background:#1a3328; color:#22c55e; }
.badge-medium { background:#2d2006; color:#f59e0b; }
.badge-low { background:#1c1c1c; color:#6e7681; }
.badge-product { background:#1c2a3d; color:#388bfd; }
.badge-direct { background:#2d0a0a; color:#f85149; }
.badge-adjacent { background:#2d2006; color:#f59e0b; }
.badge-reference { background:#1c1c1c; color:#6e7681; }
.source-label { color:#8b949e; font-size:0.8rem; }
.reason-text { color:#6e7681; font-size:0.82rem; margin-top:0.3rem; }
.summary-text { color:#6b5c50; font-size:0.83rem; margin:0.5rem 0; line-height:1.5; }
.stat-number { font-size:1.8rem; font-weight:700; font-family:'Lora',serif; }
.stat-label { font-size:0.7rem; color:#9e8e80; letter-spacing:0.1em; font-family:'IBM Plex Mono',monospace; }
.stale-warning { background:#1a1200; border:1px solid #3d2e00; border-left:3px solid #f59e0b; padding:6px 12px; font-size:0.78rem; color:#f59e0b; margin-bottom:8px; border-radius:3px; }

/* ── Audience Mapper ── */
.sub-row { background:#faf8f5; border:1px solid #e8d8c8; border-radius:4px; padding:0.6rem 1rem; margin-bottom:0.4rem; display:flex; align-items:center; justify-content:space-between; }
.sub-name { font-family:'IBM Plex Mono',monospace; font-size:0.85rem; color:#2d2418; font-weight:500; }
.sub-score { font-family:'IBM Plex Mono',monospace; font-size:0.75rem; color:#9e8e80; }
.sub-bar-wrap { flex:1; margin:0 1rem; background:#f0ebe4; border-radius:2px; height:6px; }
.sub-bar { background:#b94a3a; border-radius:2px; height:6px; }
.psycho-block { background:#faf8f5; border-left:3px solid #b94a3a; padding:1rem 1.2rem; margin-bottom:1rem; font-size:0.88rem; color:#4a3f35; line-height:1.7; }
.angle-card { background:#fff; border:1px solid #e8d8c8; border-radius:6px; padding:0.9rem 1.1rem; margin-bottom:0.6rem; }
.angle-title { font-family:'Lora',serif; font-size:0.95rem; font-weight:600; color:#2d2418; margin-bottom:0.2rem; }
.angle-rationale { font-size:0.82rem; color:#6b5c50; line-height:1.5; }
.product-idea-card { background:#f5ede0; border-radius:6px; padding:1rem 1.2rem; margin-bottom:0.7rem; }
.product-idea-name { font-family:'Lora',serif; font-size:1rem; font-weight:600; color:#2d2418; margin-bottom:0.2rem; }
.product-idea-desc { font-size:0.85rem; color:#4a3f35; line-height:1.5; margin-bottom:0.3rem; }
.product-idea-rationale { font-size:0.78rem; color:#9e8e80; font-family:'IBM Plex Mono',monospace; line-height:1.5; }

/* ── Unlock card ── */
.unlock-card { background:#faf8f5; border:1.5px solid #e8d8c8; border-radius:8px; padding:2rem; max-width:520px; margin:2rem auto; text-align:center; }
.unlock-title { font-family:'Lora',serif; font-size:1.4rem; font-weight:600; color:#2d2418; margin-bottom:0.5rem; }
.unlock-desc { font-size:0.9rem; color:#6b5c50; line-height:1.6; margin-bottom:1.5rem; }
.unlock-price { font-family:'IBM Plex Mono',monospace; font-size:0.85rem; color:#b94a3a; font-weight:600; margin-bottom:1.2rem; }

/* ── Back button ── */
.back-btn { font-family:'IBM Plex Mono',monospace; font-size:0.78rem; color:#9e8e80; cursor:pointer; margin-bottom:1.5rem; display:inline-block; letter-spacing:0.06em; }
.mono-label { font-family:'IBM Plex Mono',monospace; font-size:0.72rem; color:#9e8e80; letter-spacing:0.12em; text-transform:uppercase; margin-bottom:0.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Unlock codes ───────────────────────────────────────────────────────────────
UNLOCK_CODES = {
    "VALIDATOR-8K4P-2X9M": "validator",
    "DETECTOR-3N7Q-5R1W": "detector",
    "SCANNER-6T2L-4V8J": "scanner",
    "MAPPER-2P9K-7W4X": "mapper",
    "BUNDLE-ALL-9Y5H-7C3D": "bundle",
}

GUMROAD_URLS = {
    "validator": "https://indiedigital.gumroad.com/l/business-validator",
    "detector": "https://indiedigital.gumroad.com/l/competitor-detector",
    "scanner": "https://indiedigital.gumroad.com/l/community-scanner",
    "mapper": "https://indiedigital.gumroad.com/l/audience-mapper",
    "bundle": "https://indiedigital.gumroad.com/l/citizen-dev-bundle",
}

STALE_INDICATORS = [
    "2024","2023","2022","2021","2020",
    "2 years","3 years","4 years","5 years",
    "1 year ago","2 years ago","3 years ago","last year",
]



DEFAULT_QUERIES = """[your problem] frustrated can't find solution 2026
[your problem] help discussion forum 2026
[your problem] software tool management 2026
[your problem] tracking organization 2026
[your problem] overwhelmed need system 2026"""

def is_stale(post):
    combined = (post.get("age","") + " " + post.get("title","") + " " + post.get("summary","")).lower()
    return any(i in combined for i in STALE_INDICATORS)

# ── Session state ──────────────────────────────────────────────────────────────
defaults = {
    "current_module": "home",
    "unlocked_validator": False,
    "unlocked_detector": False,
    "unlocked_scanner": False,
    "unlocked_mapper": False,
    # Validator
    "v_problem": "", "v_market": "", "v_price": "", "v_format": "Digital download (PDF/guide)", "v_geo": "Global",
    "validator_results": None,
    # Detector
    "det_name": "", "det_desc": "", "det_buyer": "", "det_url": "", "det_niche": "",
    "competitor_products": [], "competitor_last_run": None,
    # Scanner
    "scan_name": "", "scan_desc": "", "scan_buyer": "", "scan_url": "",
    "scan_queries": DEFAULT_QUERIES,
    "community_posts": [], "community_last_run": None,
    # Mapper
    "map_subreddit": "",
    "mapper_results": None, "mapper_last_run": None,
    # Activity log
    "activity_log": [],
    # Unlock inputs
    "unlock_input_detector": "",
    "unlock_input_scanner": "",
    "unlock_input_mapper": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── API ────────────────────────────────────────────────────────────────────────
def get_client():
    api_key = st.secrets.get("ANTHROPIC_API_KEY","")
    if not api_key:
        st.error("ANTHROPIC_API_KEY not found in Streamlit secrets.")
        st.stop()
    return anthropic.Anthropic(api_key=api_key)



# ── Unlock logic ───────────────────────────────────────────────────────────────
def attempt_unlock(code, module_context):
    code = code.strip().upper()
    if code in UNLOCK_CODES:
        unlocked = UNLOCK_CODES[code]
        if unlocked == "bundle":
            st.session_state.unlocked_validator = True
            st.session_state.unlocked_detector = True
            st.session_state.unlocked_scanner = True
            st.session_state.unlocked_mapper = True
            return True, "All modules unlocked."
        elif unlocked == module_context:
            st.session_state[f"unlocked_{module_context}"] = True
            return True, "Unlocked."
        else:
            return False, f"This code unlocks a different module. Check your purchase email."
    return False, "Code not recognized. Check for typos or contact support@indiedigital.dev"

# ── Validator functions ────────────────────────────────────────────────────────
def validator_context(idea):
    return f"""Product idea:
- Problem: {idea['problem']}
- Market: {idea['market']}
- Price: {idea['price']}
- Format: {idea['format']}
- Geography: {idea['geography']}"""

def run_dim1(client, idea):
    try:
        r = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=1200,
            system=validator_context(idea)+"""
Search Reddit, forums, Quora for evidence people experience this problem.
Return JSON only:
{"signal":"green/yellow/red","confidence":"High/Medium/Low","confidence_score":1-10,
"summary":"2-3 sentences","evidence":["up to 4 concrete examples"],"reasoning":"one sentence"}
green=clear repeated demand, yellow=thin, red=little evidence. ONLY valid JSON.""",
            messages=[{"role":"user","content":f"Search demand: {idea['problem']} for {idea['market']}"}],
            tools=[{"type":"web_search_20250305","name":"web_search"}],
        )
        text="".join(b.text for b in r.content if hasattr(b,"text"))
        s,e=text.find("{"),text.rfind("}")+1
        if s>=0 and e>s: return json.loads(text[s:e])
    except Exception as ex:
        return {"signal":"yellow","confidence":"Low","confidence_score":1,"summary":f"Error: {ex}","evidence":[],"reasoning":"Search failed."}

def run_dim2(client, idea):
    try:
        r = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=1200,
            system=validator_context(idea)+"""
Search Etsy, Gumroad, GitHub, Product Hunt for competing products and communities.
Return JSON only:
{"signal":"green/yellow/red","confidence":"High/Medium/Low","confidence_score":1-10,
"summary":"2-3 sentences","competitors":["up to 4 named"],"communities":["up to 3"],"reasoning":"one sentence"}
green=clear market, yellow=some signals, red=no market. ONLY valid JSON.""",
            messages=[{"role":"user","content":f"Search market: {idea['problem']} {idea['market']} {idea['price']} {idea['format']}"}],
            tools=[{"type":"web_search_20250305","name":"web_search"}],
        )
        text="".join(b.text for b in r.content if hasattr(b,"text"))
        s,e=text.find("{"),text.rfind("}")+1
        if s>=0 and e>s: return json.loads(text[s:e])
    except Exception as ex:
        return {"signal":"yellow","confidence":"Low","confidence_score":1,"summary":f"Error: {ex}","competitors":[],"communities":[],"reasoning":"Search failed."}

def run_dim3(client, idea, competitors):
    comp_names=", ".join(competitors) if competitors else "existing products"
    try:
        r = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=1200,
            system=validator_context(idea)+f"""
Known competitors: {comp_names}
Search G2, Capterra, Trustpilot, Gumroad reviews, Reddit for complaints and unmet needs.
Return JSON only:
{{"signal":"green/yellow/red","confidence":"High/Medium/Low","confidence_score":1-10,
"summary":"2-3 sentences","gaps":["up to 4 specific unmet needs"],"reasoning":"one sentence"}}
green=clear gaps, yellow=mild complaints, red=buyers satisfied. ONLY valid JSON.""",
            messages=[{"role":"user","content":f"Search gaps: {idea['problem']}"}],
            tools=[{"type":"web_search_20250305","name":"web_search"}],
        )
        text="".join(b.text for b in r.content if hasattr(b,"text"))
        s,e=text.find("{"),text.rfind("}")+1
        if s>=0 and e>s: return json.loads(text[s:e])
    except Exception as ex:
        return {"signal":"yellow","confidence":"Low","confidence_score":1,"summary":f"Error: {ex}","gaps":[],"reasoning":"Search failed."}

def overall_verdict(d1,d2,d3):
    sc={"green":3,"yellow":2,"red":1}
    total=sc.get(d1["signal"],2)+sc.get(d2["signal"],2)+sc.get(d3["signal"],2)
    avg=(d1.get("confidence_score",5)+d2.get("confidence_score",5)+d3.get("confidence_score",5))/3
    if total>=8: v,h,s="green","This idea has legs.","Strong signals across all three dimensions."
    elif total>=6: v,h,s="yellow","Proceed with caution.","Mixed signals. Some dimensions need more investigation."
    else: v,h,s="red","Significant headwinds.","Weak signals across multiple dimensions."
    if avg<4: s+=" Note: low confidence — limited data found."
    return v,h,s

def signal_html(sig):
    icons={"green":"🟢","yellow":"🟡","red":"🔴"}
    labels={"green":"GO","yellow":"CAUTION","red":"STOP"}
    classes={"green":"signal-green","yellow":"signal-yellow","red":"signal-red"}
    return f'<span class="{classes.get(sig,"signal-yellow")}">{icons.get(sig,"🟡")} {labels.get(sig,"CAUTION")}</span>'

def conf_html(conf,score):
    cls={"High":"conf-high","Medium":"conf-medium","Low":"conf-low"}.get(conf,"conf-medium")
    return f'<span class="{cls}">Confidence: {conf} ({score}/10)</span>'

# ── Scanner/Detector functions ─────────────────────────────────────────────────
def community_prompt():
    return f"""You are helping market {st.session_state.scan_name}, a product for {st.session_state.scan_buyer}.
Product: {st.session_state.scan_desc}
URL: {st.session_state.scan_url}
Rules: Write like a knowledgeable peer. Solve the problem first. Only mention the product if it directly helps.
If you mention it: "I put something together for this — {st.session_state.scan_name} ({st.session_state.scan_url})"
Always include the URL. Match forum tone — direct, practical, human."""

def competitor_prompt():
    return f"""Competitive intelligence for {st.session_state.det_name}.
Product: {st.session_state.det_desc}
Buyer: {st.session_state.det_buyer}"""

def search_community_posts(client, query):
    try:
        r=client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=1000,
            system="""Search Reddit and online communities for relevant posts.
Return JSON array of up to 3:
[{"title":"","source":"","url":"","summary":"2-3 sentences","age":"e.g. 2 days ago"}]
Prioritize last 48 hours. ONLY valid JSON array.""",
            messages=[{"role":"user","content":f"Search: {query}"}],
            tools=[{"type":"web_search_20250305","name":"web_search"}],
        )
        text="".join(b.text for b in r.content if hasattr(b,"text"))
        s,e=text.find("["),text.rfind("]")+1
        if s>=0 and e>s: return json.loads(text[s:e])
    except: pass
    return []

def score_post(client, post):
    try:
        r=client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=1000,
            system=community_prompt()+"""
Return JSON only:
{"opportunity":"High/Medium/Low","reason":"one sentence","productFit":true/false,
"draft":"complete reply, peer voice"}
ONLY valid JSON.""",
            messages=[{"role":"user","content":f'Post: "{post["title"]}"\nSource: {post.get("source","")}\nContext: {post["summary"]}'}],
        )
        text="".join(b.text for b in r.content if hasattr(b,"text"))
        s,e=text.find("{"),text.rfind("}")+1
        if s>=0 and e>s: return json.loads(text[s:e])
    except: pass
    return {"opportunity":"Low","reason":"Could not analyze.","productFit":False,"draft":""}

def search_competitors(client, query):
    try:
        r=client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=1000,
            system="""Search Etsy, Gumroad, GitHub, Product Hunt for competing products.
Return JSON array of up to 3:
[{"name":"","platform":"","url":"","description":"2-3 sentences","price":"","seller":""}]
ONLY valid JSON array.""",
            messages=[{"role":"user","content":f"Search: {query}"}],
            tools=[{"type":"web_search_20250305","name":"web_search"}],
        )
        text="".join(b.text for b in r.content if hasattr(b,"text"))
        s,e=text.find("["),text.rfind("]")+1
        if s>=0 and e>s: return json.loads(text[s:e])
    except: pass
    return []

def analyze_competitor(client, product):
    try:
        r=client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=1000,
            system=competitor_prompt()+"""
Return JSON only:
{"threat":"Direct/Adjacent/Reference","price":"","platform":"",
"gaps":["up to 3"],"strengths":["up to 3"],"notes":"one sentence"}
ONLY valid JSON.""",
            messages=[{"role":"user","content":f'Product: "{product["name"]}"\nPlatform: {product.get("platform","")}\nDescription: {product["description"]}\nPrice: {product.get("price","?")}'}],
        )
        text="".join(b.text for b in r.content if hasattr(b,"text"))
        s,e=text.find("{"),text.rfind("}")+1
        if s>=0 and e>s: return json.loads(text[s:e])
    except: pass
    return {"threat":"Reference","gaps":[],"strengths":[],"notes":"Could not analyze."}

def get_scan_queries():
    return [q.strip() for q in st.session_state.scan_queries.strip().split("\n") if q.strip()]

def get_competitor_queries():
    niche = st.session_state.get("det_niche", "").strip()
    desc = st.session_state.det_desc[:60] if st.session_state.det_desc else "management tool"
    name = st.session_state.det_name or "product"
    anchor = niche if niche else desc[:40]
    return [
        f"{anchor} software tool 2026",
        f"{anchor} management app Etsy",
        f"{anchor} tracker template Gumroad",
        f"{anchor} open source GitHub",
        f"{anchor} business tool Product Hunt 2026",
        f"{anchor} spreadsheet template download",
        f"{name} alternative {anchor} competitor",
        f"{anchor} order tracking inventory 2026",
    ]

# ── Audience Mapper functions ──────────────────────────────────────────────────

MAPPER_SEARCH_ANGLES = [
    "which subreddits do r/{sub} members also post in cross-community",
    "r/{sub} users also active in subreddit community overlap",
    "r/{sub} related communities adjacent subreddits members discuss",
    "r/{sub} what tools products software does community use recommend",
    "r/{sub} recurring problems frustrations members complain about",
    "r/{sub} member demographics identity who are these people",
    "r/{sub} hobbies interests outside niche mentioned community",
    "r/{sub} income money work side hustle financial goals discussion",
]

def run_mapper_searches(client, subreddit_name):
    """Run structured web searches to surface community patterns for a subreddit."""
    pb = st.progress(0, text="Searching community patterns...")
    all_findings = []

    queries = [a.format(sub=subreddit_name) for a in MAPPER_SEARCH_ANGLES]

    for i, query in enumerate(queries):
        pb.progress(int(((i+1)/len(queries))*80), text=f"Searching angle {i+1} of {len(queries)}...")
        try:
            r = client.messages.create(
                model="claude-sonnet-4-20250514", max_tokens=600,
                system=f"""You are researching the Reddit community r/{subreddit_name}.
Search the web for the query provided and extract specific, concrete findings relevant to understanding this community's cross-platform presence, identity, and behavior.
Return JSON only:
{{"findings": ["up to 5 specific concrete observations — name actual subreddits, tools, topics, or patterns found"]}}
If no relevant results found, return {{"findings": []}}
ONLY valid JSON.""",
                messages=[{"role":"user","content":f"Search: {query}"}],
                tools=[{"type":"web_search_20250305","name":"web_search"}],
            )
            text = "".join(b.text for b in r.content if hasattr(b,"text"))
            s, e = text.find("{"), text.rfind("}")+1
            if s >= 0 and e > s:
                data = json.loads(text[s:e])
                all_findings.extend(data.get("findings", []))
        except Exception:
            pass
        time.sleep(0.2)

    pb.progress(85, text="Running AI synthesis...")
    return all_findings

def run_mapper_synthesis(client, subreddit_name, findings):
    """Claude synthesis from web search findings: overlap signals, psychographic summary, marketing angles, product ideas."""
    findings_text = "\n".join([f"- {f}" for f in findings]) if findings else "No specific findings retrieved."

    try:
        r = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=2500,
            system=f"""You are analyzing publicly available information about the Reddit community r/{subreddit_name}.
The findings below were gathered by searching for community patterns, cross-sub activity, tools used, recurring topics, and identity signals.

RESEARCH FINDINGS:
{findings_text}

Produce four outputs from this data.

Return JSON only, with this exact structure:
{{
  "overlap_signals": [
    {{"community": "community or topic name", "strength": "Strong/Moderate/Weak", "reason": "one sentence explaining the signal"}},
    ... up to 12 entries, ranked Strong first
  ],
  "psychographic_summary": "2-3 paragraphs written as a briefing for a product strategist who has never encountered this audience before. Cover identity, motivations, values, and behavior patterns visible in the research.",
  "marketing_angles": [
    {{"angle": "short angle title", "rationale": "one sentence explaining why this angle fits based on the research"}},
    {{"angle": "...", "rationale": "..."}},
    {{"angle": "...", "rationale": "..."}},
    {{"angle": "...", "rationale": "..."}}
  ],
  "product_ideas": [
    {{"name": "product name", "description": "one sentence describing what it does", "rationale": "one sentence tying this idea back to the audience research"}},
    {{"name": "...", "description": "...", "rationale": "..."}},
    {{"name": "...", "description": "...", "rationale": "..."}},
    {{"name": "...", "description": "...", "rationale": "..."}},
    {{"name": "...", "description": "...", "rationale": "..."}}
  ]
}}
ONLY valid JSON. No preamble.""",
            messages=[{"role":"user","content":f"Synthesize the audience profile for r/{subreddit_name}."}],
        )
        text = "".join(b.text for b in r.content if hasattr(b,"text"))
        s, e = text.find("{"), text.rfind("}")+1
        if s >= 0 and e > s:
            return json.loads(text[s:e])
    except Exception as ex:
        return {"overlap_signals": [], "psychographic_summary": f"Synthesis error: {ex}", "marketing_angles": [], "product_ideas": []}

# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def go_home():
    st.session_state.current_module = "home"
    st.rerun()

def go_module(name):
    st.session_state.current_module = name
    st.rerun()

def back_button():
    if st.button("← Back to Indie Digital", key="back_btn"):
        go_home()

# ══════════════════════════════════════════════════════════════════════════════
# LOCKED SCREEN
# ══════════════════════════════════════════════════════════════════════════════
def locked_screen(module_key, title, icon, description, price, gumroad_url):
    back_button()
    st.markdown(f"""
    <div class="unlock-card">
        <div class="card-icon">{icon}</div>
        <div class="unlock-title">{title}</div>
        <div class="unlock-desc">{description}</div>
        <div class="unlock-price">{price}</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.link_button("🔓 Unlock Now →", gumroad_url, use_container_width=True)
        st.write("")
        st.markdown('<div class="mono-label" style="text-align:center">Already purchased? Enter your code:</div>', unsafe_allow_html=True)
        code_input = st.text_input("Unlock code", placeholder=f"e.g. {title.upper().replace(' ','-')[:8]}-XXXX-XXXX", key=f"unlock_input_{module_key}", label_visibility="collapsed")
        if st.button("Apply Code", key=f"apply_{module_key}", use_container_width=True):
            if code_input:
                success, msg = attempt_unlock(code_input, module_key)
                if success:
                    st.success(msg)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("Enter your unlock code from the purchase email.")
        st.caption("Questions? support@indiedigital.dev")

# ══════════════════════════════════════════════════════════════════════════════
# HOME SCREEN
# ══════════════════════════════════════════════════════════════════════════════
def show_home():
    st.markdown('<h2 style="font-family:\'Lora\',serif;color:#2d2418;margin-bottom:0.1rem">💡 Indie Digital</h2>', unsafe_allow_html=True)
    st.markdown('<div class="mono-label">Your digital product toolkit</div>', unsafe_allow_html=True)
    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    modules = [
        {
            "col": col1, "key": "validator", "icon": "🔦", "title": "Business Validator",
            "desc_unlocked": "Red/green verdict on whether your idea is worth building. Three dimensions, two minutes.",
            "desc_locked": "Should you build this? Get a red/green viability verdict across demand, market, and gaps.",
            "price": "$9",
        },
        {
            "col": col2, "key": "detector", "icon": "🔍", "title": "Competitor Detector",
            "desc_unlocked": "Scan Etsy, Gumroad, GitHub, and the web for products competing in your space.",
            "desc_locked": "Know who's in your space before you launch. Find gaps in their products — your positioning, handed to you.",
            "price": "$9",
        },
        {
            "col": col3, "key": "scanner", "icon": "📡", "title": "Community Scanner",
            "desc_unlocked": "Find online conversations where your product belongs. Draft your reply. Post it yourself.",
            "desc_locked": "Find people describing your problem online. Get a draft reply — helpful first, product mention only when earned.",
            "price": "$9",
        },
        {
            "col": col4, "key": "mapper", "icon": "🗺️", "title": "Audience Mapper",
            "desc_unlocked": "Map where your Reddit audience spends time. Uncover messaging angles and product ideas from the overlap.",
            "desc_locked": "Discover where your audience lives beyond one subreddit. Shapes your marketing, roadmap, and next product idea.",
            "price": "$9",
        },
    ]

    for m in modules:
        with m["col"]:
            unlocked = st.session_state.get(f"unlocked_{m['key']}", False)
            if unlocked:
                st.markdown(f"""
                <div class="module-card card-unlocked">
                    <div>
                        <div class="card-icon">{m['icon']}</div>
                        <div class="card-title">{m['title']}</div>
                        <div class="card-desc">{m['desc_unlocked']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Open {m['title']}", key=f"open_{m['key']}", use_container_width=True):
                    go_module(m['key'])
            else:
                st.markdown(f"""
                <div class="module-card card-locked">
                    <div class="lock-badge">🔒</div>
                    <div>
                        <div class="card-icon" style="opacity:0.4">{m['icon']}</div>
                        <div class="card-title card-title-locked">{m['title']}</div>
                        <div class="card-desc-locked">{m['desc_locked']}</div>
                    </div>
                    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.8rem;color:#b94a3a;font-weight:600">{m['price']}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Unlock {m['title']}", key=f"unlock_{m['key']}", use_container_width=True):
                    go_module(m['key'])

    st.divider()
    st.caption("Indie Digital · support@indiedigital.dev")

# ══════════════════════════════════════════════════════════════════════════════
# BUSINESS VALIDATOR MODULE
# ══════════════════════════════════════════════════════════════════════════════
def show_validator():
    if not st.session_state.unlocked_validator:
        locked_screen(
            "validator", "Business Validator", "🔦",
            "Enter your idea. Get a red/green viability verdict across three dimensions: demand, market, and gaps in existing products. About two minutes.",
            "$9 — one-time purchase", GUMROAD_URLS["validator"]
        )
        return

    back_button()
    st.markdown('<h3 style="font-family:\'Lora\',serif;color:#2d2418">🔦 Business Validator</h3>', unsafe_allow_html=True)
    st.markdown("**Should you build this? Red/green verdict across three dimensions.**")
    st.write("")

    with st.expander("📋 Your Idea", expanded=st.session_state.validator_results is None):
        c1,c2=st.columns(2)
        with c1:
            v_problem=st.text_area("Problem it solves", value=st.session_state.v_problem, placeholder="Describe the pain from your customer's perspective.", height=100, key="v_problem_input")
            v_market=st.text_input("Intended market", value=st.session_state.v_market, placeholder="e.g. Small 3D print farm operators, 1-20 printers", key="v_market_input")
            v_price=st.text_input("Target price range", value=st.session_state.v_price, placeholder="e.g. $9-15 one-time purchase", key="v_price_input")
        with c2:
            v_format=st.selectbox("Product format", ["Digital download (PDF/guide)","Spreadsheet/template","Web app (hosted)","Mobile app","Software download","Physical product","Service/consulting"], key="v_format_input")
            v_geo=st.selectbox("Geography", ["Global","United States","North America","Europe","UK","Australia/NZ","Other"], key="v_geo_input")
            st.write("")
            validate_btn=st.button("🔦 VALIDATE THIS IDEA", key="validate_btn", use_container_width=True)

    if validate_btn:
        st.session_state.v_problem=v_problem
        st.session_state.v_market=v_market
        st.session_state.v_price=v_price
        if not v_problem or not v_market:
            st.warning("Please describe the problem and intended market.")
        else:
            idea={"problem":v_problem,"market":v_market,"price":v_price or "unknown","format":v_format,"geography":v_geo}
            client=get_client()
            with st.spinner("Searching demand signals and market landscape..."):
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
                    f1=ex.submit(run_dim1,client,idea)
                    f2=ex.submit(run_dim2,client,idea)
                    d1=f1.result(); d2=f2.result()
            with st.spinner("Analyzing gaps in existing products..."):
                d3=run_dim3(client,idea,d2.get("competitors",[]))
            v,h,s=overall_verdict(d1,d2,d3)
            st.session_state.validator_results={"d1":d1,"d2":d2,"d3":d3,"verdict":v,"headline":h,"sub":s,"idea":idea}
            st.rerun()

    if st.session_state.validator_results:
        res=st.session_state.validator_results
        d1,d2,d3=res["d1"],res["d2"],res["d3"]
        idea=res["idea"]
        st.markdown(f'<div class="idea-chip">{idea["problem"][:100]}{"..." if len(idea["problem"])>100 else ""} · {idea["market"]} · {idea["price"]}</div>', unsafe_allow_html=True)
        vc=f"verdict-{res['verdict']}"
        vi={"green":"🟢","yellow":"🟡","red":"🔴"}.get(res["verdict"],"🟡")
        st.markdown(f'<div class="{vc}"><div class="mono-label">Overall Verdict</div><div class="overall-verdict">{vi} {res["headline"]}</div><div class="overall-sub">{res["sub"]}</div></div>', unsafe_allow_html=True)
        st.divider()

        for dim,title,question,ekey,elabel in [
            (d1,"📣 Demand Exists","Are people describing this problem online?","evidence","Evidence found"),
            (d2,"🏪 Market is Proven","Do competitors and communities exist?",None,None),
            (d3,"🕳️ Gaps Exist","Are buyers frustrated with existing options?","gaps","Gaps identified"),
        ]:
            with st.expander(f"{title} — {dim.get('summary','')[:70]}...", expanded=True):
                ca,cb=st.columns([3,1])
                with ca:
                    st.markdown(f'<div style="font-family:Lora,serif;font-weight:600;color:#2d2418">{question}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="dim-summary">{dim.get("summary","")}</div>', unsafe_allow_html=True)
                with cb:
                    st.markdown(signal_html(dim.get("signal","yellow")), unsafe_allow_html=True)
                    st.markdown(conf_html(dim.get("confidence","Medium"),dim.get("confidence_score",5)), unsafe_allow_html=True)
                if dim is d2:
                    cc,cd=st.columns(2)
                    with cc:
                        comps=dim.get("competitors",[])
                        if comps:
                            st.markdown('<div class="mono-label">Competitors</div>', unsafe_allow_html=True)
                            for c in comps: st.markdown(f'<div class="evidence-item">{c}</div>', unsafe_allow_html=True)
                    with cd:
                        comms=dim.get("communities",[])
                        if comms:
                            st.markdown('<div class="mono-label">Communities</div>', unsafe_allow_html=True)
                            for c in comms: st.markdown(f'<div class="evidence-item">{c}</div>', unsafe_allow_html=True)
                elif ekey:
                    items=dim.get(ekey,[])
                    if items:
                        st.write("")
                        st.markdown(f'<div class="mono-label">{elabel}</div>', unsafe_allow_html=True)
                        for item in items: st.markdown(f'<div class="evidence-item">{item}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:0.78rem;color:#9e8e80;margin-top:0.8rem;font-style:italic">{dim.get("reasoning","")}</div>', unsafe_allow_html=True)

        if st.button("🔄 Validate a Different Idea"):
            st.session_state.validator_results=None
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# COMPETITOR DETECTOR MODULE
# ══════════════════════════════════════════════════════════════════════════════
def show_detector():
    if not st.session_state.unlocked_detector:
        locked_screen(
            "detector", "Competitor Detector", "🔍",
            "Scan Etsy, Gumroad, GitHub, and the web for products competing in your space. Know who's there, what they charge, and where their customers are frustrated — before you launch.",
            "$9 — one-time purchase", GUMROAD_URLS["detector"]
        )
        return

    back_button()
    st.markdown('<h3 style="font-family:\'Lora\',serif;color:#2d2418">🔍 Competitor Detector</h3>', unsafe_allow_html=True)
    st.markdown("**Find competing and adjacent products. Know the landscape.**")
    st.write("")

    with st.expander("⚙️ Your Product", expanded=not st.session_state.det_name):
        c1,c2=st.columns(2)
        with c1:
            det_name=st.text_input("Product name", value=st.session_state.det_name, placeholder="e.g. Offset3D", key="det_name_input")
            det_buyer=st.text_input("Who it's for", value=st.session_state.det_buyer, placeholder="e.g. 3D print farm operators, 1-20 printers", key="det_buyer_input")
            det_niche=st.text_input("Industry or niche", value=st.session_state.det_niche, placeholder="e.g. 3D printing, sourdough baking, indie game dev", key="det_niche_input", help="This is the most important field. Be specific about your niche, not your product type.")
        with c2:
            det_url=st.text_input("Your URL", value=st.session_state.det_url, placeholder="e.g. offsetos.com/offset3D", key="det_url_input")
            det_desc=st.text_area("What it does", value=st.session_state.det_desc, placeholder="2-3 sentences.", height=100, key="det_desc_input")

        c1,c2=st.columns([2,1])
        with c1:
            if st.button("Copy product details to Community Scanner", key="copy_det_to_scan"):
                st.session_state.scan_name=st.session_state.det_name
                st.session_state.scan_desc=st.session_state.det_desc
                st.session_state.scan_buyer=st.session_state.det_buyer
                st.session_state.scan_url=st.session_state.det_url
                st.success("Copied to Community Scanner.")
                st.rerun()

    c1,c2=st.columns([4,1])
    with c2: run_comp=st.button("▶ RUN SCAN", key="run_comp", use_container_width=True)

    if run_comp:
        if not st.session_state.det_name:
            st.warning("Save your product details before scanning.")
        else:
            client=get_client()
            all_products,seen=[],set()
            queries=get_competitor_queries()
            pb=st.progress(0,text="Scanning for competitors...")
            for i,query in enumerate(queries):
                pb.progress(int((i/len(queries))*50),text=f"Searching... ({i+1}/{len(queries)})")
                for p in search_competitors(client,query):
                    k=p.get("name","").lower().strip()
                    if k and k not in seen:
                        seen.add(k); all_products.append(p)
                time.sleep(0.3)
            if not all_products:
                pb.empty(); st.warning("No competing products found. Try again in a few minutes.")
            else:
                analyzed=[]
                for i,product in enumerate(all_products):
                    pb.progress(50+int((i/len(all_products))*50),text=f"Analyzing... ({i+1}/{len(all_products)})")
                    a=analyze_competitor(client,product)
                    analyzed.append({**product,**a,"id":i})
                    time.sleep(0.2)
                analyzed.sort(key=lambda x:{"Direct":0,"Adjacent":1,"Reference":2}.get(x.get("threat","Reference"),2))
                st.session_state.competitor_products=analyzed
                st.session_state.competitor_last_run=time.strftime("%B %d, %Y at %I:%M %p")
                pb.empty(); st.rerun()

    if st.session_state.competitor_products:
        prods=st.session_state.competitor_products
        direct=[p for p in prods if p.get("threat")=="Direct"]
        adjacent=[p for p in prods if p.get("threat")=="Adjacent"]
        ref=[p for p in prods if p.get("threat")=="Reference"]
        c1,c2,c3,c4=st.columns(4)
        with c1: st.markdown(f'<div class="stat-number">{len(prods)}</div><div class="stat-label">FOUND</div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-number" style="color:#c0392b">{len(direct)}</div><div class="stat-label">DIRECT</div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-number" style="color:#e67e22">{len(adjacent)}</div><div class="stat-label">ADJACENT</div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="stat-number" style="color:#9e8e80">{len(ref)}</div><div class="stat-label">REFERENCE</div>', unsafe_allow_html=True)
        if st.session_state.competitor_last_run: st.caption(f"Last run: {st.session_state.competitor_last_run}")
        st.divider()
        filt=st.radio("Filter:",["All","Direct","Adjacent","Reference"],horizontal=True,label_visibility="collapsed",key="comp_filt")
        display=prods if filt=="All" else [p for p in prods if p.get("threat")==filt]
        for prod in display:
            threat=prod.get("threat","Reference")
            tbadge={"Direct":"🔴 Direct","Adjacent":"🟡 Adjacent","Reference":"⚪ Reference"}.get(threat,threat)
            bcls={"Direct":"badge-direct","Adjacent":"badge-adjacent","Reference":"badge-reference"}.get(threat,"badge-reference")
            with st.expander(f"{prod.get('name','Unknown')} — {prod.get('platform','')} — {prod.get('price','')}", expanded=False):
                st.markdown(f'<span class="badge {bcls}">{tbadge}</span><span class="source-label">{prod.get("platform","")} · {prod.get("seller","")}</span>', unsafe_allow_html=True)
                st.markdown(f'<div class="summary-text">{prod.get("description","")}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="reason-text">{prod.get("notes","")}</div>', unsafe_allow_html=True)
                url=prod.get("url","")
                if url: st.markdown(f"[→ View listing]({url})")
                cg,cs=st.columns(2)
                with cg:
                    gaps=prod.get("gaps",[])
                    if gaps:
                        st.markdown("**Their gaps:**")
                        for g in gaps: st.markdown(f"- {g}")
                with cs:
                    strs=prod.get("strengths",[])
                    if strs:
                        st.markdown("**Their strengths:**")
                        for s in strs: st.markdown(f"- {s}")
    else:
        st.markdown('<div style="text-align:center;padding:3rem 2rem;color:#9e8e80"><div style="font-size:2rem;margin-bottom:1rem">🔍</div><div style="font-size:0.9rem;color:#4a3f35;margin-bottom:0.4rem">No competitors loaded yet</div><div style="font-size:0.82rem">Save your product details and hit RUN SCAN</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# COMMUNITY SCANNER MODULE
# ══════════════════════════════════════════════════════════════════════════════
def show_scanner():
    if not st.session_state.unlocked_scanner:
        locked_screen(
            "scanner", "Community Scanner", "📡",
            "Find people describing your problem in online communities. Get a draft reply for each — helpful first, product mention only when it's genuinely earned. Your daily 15-minute distribution routine.",
            "$9 — one-time purchase", GUMROAD_URLS["scanner"]
        )
        return

    back_button()
    st.markdown('<h3 style="font-family:\'Lora\',serif;color:#2d2418">📡 Community Scanner</h3>', unsafe_allow_html=True)
    st.markdown("**Find posts where you can add value and mention your product organically.**")
    st.write("")

    with st.expander("⚙️ Your Product", expanded=not st.session_state.scan_name):
        c1,c2=st.columns(2)
        with c1:
            scan_name=st.text_input("Product name", value=st.session_state.scan_name, placeholder="e.g. Offset3D", key="scan_name_input")
            scan_buyer=st.text_input("Who it's for", value=st.session_state.scan_buyer, placeholder="e.g. 3D print farm operators, 1-20 printers", key="scan_buyer_input")
        with c2:
            scan_url=st.text_input("Your URL", value=st.session_state.scan_url, placeholder="e.g. offsetos.com/offset3D", key="scan_url_input")
            scan_desc=st.text_area("What it does", value=st.session_state.scan_desc, placeholder="2-3 sentences.", height=100, key="scan_desc_input")

        scan_queries=st.text_area(
            "Search queries — one per line",
            value=st.session_state.scan_queries, height=140, key="scan_queries_input",
            help="Each line is an independent search. Five to ten lines is a good range.\n\nBest pattern: the frustrated phrase — what someone types when actively annoyed by the problem."
        )

    c1,c2=st.columns([2,1])
    with c1:
            if st.button("Copy product details to Competitor Detector", key="copy_scan_to_det"):
                st.session_state.det_name=st.session_state.scan_name
                st.session_state.det_desc=st.session_state.scan_desc
                st.session_state.det_buyer=st.session_state.scan_buyer
                st.session_state.det_url=st.session_state.scan_url
                st.success("Copied to Competitor Detector.")

    c1,c2=st.columns([4,1])
    with c2: run_scan=st.button("▶ RUN SCAN", key="run_scan", use_container_width=True)

    if run_scan:
        queries=get_scan_queries()
        if not st.session_state.scan_name:
            st.warning("Save your product details before scanning.")
        elif not queries:
            st.warning("Add search queries in Your Product above.")
        else:
            client=get_client()
            all_posts,seen=[],set()
            pb=st.progress(0,text="Starting scan...")
            for i,query in enumerate(queries):
                pb.progress(int((i/len(queries))*50),text=f"Scanning... ({i+1}/{len(queries)})")
                for post in search_community_posts(client,query):
                    k=post.get("title","").lower().strip()
                    if k and k not in seen:
                        seen.add(k); all_posts.append(post)
                time.sleep(0.3)
            if not all_posts:
                pb.empty(); st.warning("No posts found. Try adjusting queries.")
            else:
                scored=[]
                for i,post in enumerate(all_posts):
                    pb.progress(50+int((i/len(all_posts))*50),text=f"Drafting responses... ({i+1}/{len(all_posts)})")
                    a=score_post(client,post)
                    scored.append({**post,**a,"id":i,"stale":is_stale(post)})
                    time.sleep(0.2)
                scored.sort(key=lambda x:({"High":0,"Medium":1,"Low":2}.get(x.get("opportunity","Low"),2),1 if x.get("stale") else 0))
                st.session_state.community_posts=scored
                st.session_state.community_last_run=time.strftime("%B %d, %Y at %I:%M %p")
                pb.empty(); st.rerun()

    if st.session_state.community_posts:
        posts=st.session_state.community_posts
        fresh=[p for p in posts if not p.get("stale")]
        stale=[p for p in posts if p.get("stale")]
        c1,c2,c3,c4,c5=st.columns(5)
        with c1: st.markdown(f'<div class="stat-number">{len(fresh)}</div><div class="stat-label">FRESH</div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-number" style="color:#27ae60">{sum(1 for p in fresh if p.get("opportunity")=="High")}</div><div class="stat-label">HIGH OPP</div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-number" style="color:#e67e22">{sum(1 for p in fresh if p.get("opportunity")=="Medium")}</div><div class="stat-label">MEDIUM OPP</div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="stat-number" style="color:#388bfd">{sum(1 for p in fresh if p.get("productFit"))}</div><div class="stat-label">PRODUCT FITS</div>', unsafe_allow_html=True)
        with c5: st.markdown(f'<div class="stat-number" style="color:#9e8e80">{len(stale)}</div><div class="stat-label">FILTERED OLD</div>', unsafe_allow_html=True)
        if st.session_state.community_last_run: st.caption(f"Last run: {st.session_state.community_last_run}")
        st.divider()
        filt=st.radio("Filter:",["All","High","Medium","Low"],horizontal=True,label_visibility="collapsed",key="scan_filt")
        display=fresh if filt=="All" else [p for p in fresh if p.get("opportunity")==filt]
        st.markdown(f"**{len(display)} posts** · {len(stale)} older post(s) filtered")
        st.write("")
        for post in display:
            opp=post.get("opportunity","Low")
            blabel={"High":"🎯 High","Medium":"◎ Medium","Low":"· Low"}.get(opp,opp)
            pfit=post.get("productFit",False)
            with st.expander(post.get("title","Untitled"),expanded=False):
                bhtml=f'<span class="badge badge-{opp.lower()}">{blabel}</span>'
                bhtml+=f'<span class="source-label">{post.get("source","")}</span>'
                if pfit: bhtml+=' &nbsp;<span class="badge badge-product">↗ PRODUCT FIT</span>'
                bhtml+=f'&nbsp;&nbsp;<span style="color:#9e8e80;font-size:0.78rem">{post.get("age","")}</span>'
                st.markdown(bhtml, unsafe_allow_html=True)
                st.markdown(f'<div class="reason-text">{post.get("reason","")}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="summary-text"><strong style="color:#9e8e80;font-size:0.72rem">CONTEXT &nbsp;</strong>{post.get("summary","")}</div>', unsafe_allow_html=True)
                url=post.get("url","")
                if url and url not in ["","https://reddit.com"]: st.markdown(f"[→ View post]({url})")
                st.markdown("---")
                st.markdown("**Suggested response** — includes product mention" if pfit else "**Suggested response** — helpful only, no pitch")
                draft=post.get("draft","No draft generated.")
                st.text_area("draft",value=draft,height=220,key=f"draft_{post.get('id',0)}",label_visibility="collapsed")
                if st.button("+ Log this response",key=f"log_{post.get('id',0)}"):
                    st.session_state.activity_log.append({"date":datetime.now().strftime("%Y-%m-%d %H:%M"),"platform":post.get("source",""),"title":post.get("title",""),"url":post.get("url",""),"notes":"","status":"Drafted"})
                    st.success("Added to Activity Log.")
                st.caption("Review and edit before posting. You own every reply.")
        if stale:
            st.write("")
            if st.checkbox(f"Show {len(stale)} older post(s)"):
                for post in stale:
                    with st.expander(f"⚠ {post.get('title','')}",expanded=False):
                        st.markdown(f'<div class="stale-warning">⚠ May be older than 48 hours ({post.get("age","unknown")})</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="summary-text">{post.get("summary","")}</div>', unsafe_allow_html=True)
                        url=post.get("url","")
                        if url and url not in ["","https://reddit.com"]: st.markdown(f"[→ View post]({url})")
                        st.text_area("draft",value=post.get("draft",""),height=180,key=f"sdraft_{post.get('id',0)}",label_visibility="collapsed")
                        st.caption("Verify date before posting.")
    else:
        st.markdown('<div style="text-align:center;padding:3rem 2rem;color:#9e8e80"><div style="font-size:2rem;margin-bottom:1rem">📡</div><div style="font-size:0.9rem;color:#4a3f35;margin-bottom:0.4rem">No posts loaded yet</div><div style="font-size:0.82rem">Save your product details and hit RUN SCAN</div></div>', unsafe_allow_html=True)

    st.divider()
    with st.expander("📝 Activity Log", expanded=False):
        st.markdown("Track where you've engaged. One entry per response posted.")
        st.write("")
        c1,c2=st.columns(2)
        with c1:
            lp=st.text_input("Platform / Community",placeholder="e.g. r/3dprintingbusiness",key="lp")
            lu=st.text_input("Post URL",placeholder="https://...",key="lu")
        with c2:
            lt=st.text_input("Post Title",placeholder="What was the post about?",key="lt")
            ls=st.selectbox("Status",["Posted","Drafted","Skipped"],key="ls")
        ln=st.text_input("Notes",placeholder="Optional — what did you say, any product mention?",key="ln")
        if st.button("Add to Log",key="add_log"):
            if lp or lt:
                st.session_state.activity_log.append({"date":datetime.now().strftime("%Y-%m-%d %H:%M"),"platform":lp,"title":lt,"url":lu,"notes":ln,"status":ls})
                st.success("Entry added.")
                st.rerun()
            else:
                st.warning("Add at least a platform or title.")

        if st.session_state.activity_log:
            log=list(reversed(st.session_state.activity_log))
            posted=sum(1 for e in log if e.get("status")=="Posted")
            drafted=sum(1 for e in log if e.get("status")=="Drafted")
            c1,c2,c3=st.columns(3)
            with c1: st.markdown(f'<div class="stat-number">{len(log)}</div><div class="stat-label">TOTAL</div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="stat-number" style="color:#27ae60">{posted}</div><div class="stat-label">POSTED</div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="stat-number" style="color:#e67e22">{drafted}</div><div class="stat-label">DRAFTED</div>', unsafe_allow_html=True)
            st.write("")
            if st.button("⬇ Export CSV",key="export_csv"):
                out=io.StringIO()
                w=csv.DictWriter(out,fieldnames=["date","platform","title","url","status","notes"])
                w.writeheader(); w.writerows(st.session_state.activity_log)
                st.download_button("Download activity_log.csv",data=out.getvalue(),file_name=f"activity_log_{datetime.now().strftime('%Y%m%d')}.csv",mime="text/csv")
            st.write("")
            for i,entry in enumerate(log):
                sc={"Posted":"#27ae60","Drafted":"#e67e22","Skipped":"#9e8e80"}.get(entry.get("status"),"#9e8e80")
                with st.expander(f"{entry.get('date','')} · {entry.get('platform','')} · {entry.get('title','')[:50]}",expanded=False):
                    c1,c2=st.columns([3,1])
                    with c1:
                        url=entry.get("url","")
                        if url: st.markdown(f"[→ View post]({url})")
                        if entry.get("notes"): st.markdown(f'<div class="reason-text">{entry.get("notes")}</div>', unsafe_allow_html=True)
                    with c2:
                        st.markdown(f'<span style="color:{sc};font-weight:600;font-size:0.85rem">{entry.get("status","")}</span>', unsafe_allow_html=True)
                    if st.button("🗑 Remove",key=f"rm_{i}"):
                        st.session_state.activity_log.pop(len(st.session_state.activity_log)-1-i)
                        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# AUDIENCE MAPPER MODULE
# ══════════════════════════════════════════════════════════════════════════════
def show_mapper():
    if not st.session_state.unlocked_mapper:
        locked_screen(
            "mapper", "Audience Mapper", "🗺️",
            "Enter a subreddit. Get a psychographic profile of your audience, messaging angles, and product ideas — all from publicly available community signals.",
            "$9 — one-time purchase", GUMROAD_URLS["mapper"]
        )
        return

    back_button()
    st.markdown('<h3 style="font-family:\'Lora\',serif;color:#2d2418">🗺️ Audience Mapper</h3>', unsafe_allow_html=True)
    st.markdown("**Map where your audience lives. Shape your marketing, roadmap, and next product idea.**")
    st.write("")
    st.markdown('<div class="reason-text">Searches publicly available Reddit community signals — cross-community references, recurring topics, tools discussed, and identity patterns — then synthesizes them into a strategic audience profile.</div>', unsafe_allow_html=True)
    st.write("")

    c1, c2 = st.columns([3,1])
    with c1:
        map_subreddit = st.text_input(
            "Target subreddit",
            value=st.session_state.map_subreddit,
            placeholder="3dprintingbusiness",
            key="map_subreddit_input",
            help="Enter the subreddit name without r/ — for example: 3dprintingbusiness",
            label_visibility="collapsed",
        )
    with c2:
        run_mapper = st.button("▶ RUN SCAN", key="run_mapper", use_container_width=True)

    if run_mapper:
        sub = map_subreddit.lstrip("r/").strip()
        if not sub:
            st.warning("Enter a subreddit name before running.")
        else:
            st.session_state.map_subreddit = sub
            client = get_client()
            findings = run_mapper_searches(client, sub)
            if not findings:
                st.error("No community signals found. Check the subreddit name and try again.")
            else:
                synthesis = run_mapper_synthesis(client, sub, findings)
                st.session_state.mapper_results = {
                    "subreddit": sub,
                    "findings": findings,
                    "synthesis": synthesis,
                }
                st.session_state.mapper_last_run = time.strftime("%B %d, %Y at %I:%M %p")
                st.rerun()

    if st.session_state.mapper_results:
        res = st.session_state.mapper_results
        synthesis = res["synthesis"]
        sub = res["subreddit"]
        signals = synthesis.get("overlap_signals", [])
        strong = sum(1 for s in signals if s.get("strength") == "Strong")
        moderate = sum(1 for s in signals if s.get("strength") == "Moderate")

        st.markdown(f'<div class="idea-chip">r/{sub}</div>', unsafe_allow_html=True)
        if st.session_state.mapper_last_run:
            st.caption(f"Last run: {st.session_state.mapper_last_run}")

        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="stat-number">{len(signals)}</div><div class="stat-label">SIGNALS FOUND</div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-number" style="color:#27ae60">{strong}</div><div class="stat-label">STRONG</div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-number" style="color:#e67e22">{moderate}</div><div class="stat-label">MODERATE</div>', unsafe_allow_html=True)

        st.divider()

        tab1, tab2, tab3, tab4 = st.tabs(["📊 Community Signals", "🧠 Psychographic Profile", "📣 Marketing Angles", "💡 Product Ideas"])

        with tab1:
            st.markdown(f'<div class="mono-label">Communities and topics connected to r/{sub} — ranked by signal strength</div>', unsafe_allow_html=True)
            st.write("")
            strength_color = {"Strong": "#27ae60", "Moderate": "#e67e22", "Weak": "#9e8e80"}
            for signal in signals:
                color = strength_color.get(signal.get("strength","Weak"), "#9e8e80")
                st.markdown(f"""
                <div class="sub-row">
                    <span class="sub-name">{signal.get("community","")}</span>
                    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.72rem;font-weight:600;color:{color};margin:0 1rem;min-width:60px">{signal.get("strength","")}</span>
                    <span class="sub-score" style="flex:1">{signal.get("reason","")}</span>
                </div>
                """, unsafe_allow_html=True)

        with tab2:
            st.markdown('<div class="mono-label">Audience profile — written as a briefing for a product strategist</div>', unsafe_allow_html=True)
            st.write("")
            summary = synthesis.get("psychographic_summary","")
            for para in summary.split("\n\n"):
                if para.strip():
                    st.markdown(f'<div class="psycho-block">{para.strip()}</div>', unsafe_allow_html=True)

        with tab3:
            st.markdown('<div class="mono-label">Messaging angles suggested by the community signals</div>', unsafe_allow_html=True)
            st.write("")
            for angle in synthesis.get("marketing_angles",[]):
                st.markdown(f"""
                <div class="angle-card">
                    <div class="angle-title">{angle.get("angle","")}</div>
                    <div class="angle-rationale">{angle.get("rationale","")}</div>
                </div>
                """, unsafe_allow_html=True)

        with tab4:
            st.markdown('<div class="mono-label">Product ideas sparked by this audience profile</div>', unsafe_allow_html=True)
            st.write("")
            for idea in synthesis.get("product_ideas",[]):
                st.markdown(f"""
                <div class="product-idea-card">
                    <div class="product-idea-name">{idea.get("name","")}</div>
                    <div class="product-idea-desc">{idea.get("description","")}</div>
                    <div class="product-idea-rationale">↳ {idea.get("rationale","")}</div>
                </div>
                """, unsafe_allow_html=True)

        st.write("")
        if st.button("🔄 Run a New Scan"):
            st.session_state.mapper_results = None
            st.rerun()

    else:
        st.markdown('<div style="text-align:center;padding:3rem 2rem;color:#9e8e80"><div style="font-size:2rem;margin-bottom:1rem">🗺️</div><div style="font-size:0.9rem;color:#4a3f35;margin-bottom:0.4rem">No results yet</div><div style="font-size:0.82rem">Enter a subreddit name and hit RUN SCAN</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════
module = st.session_state.current_module

if module == "home":
    show_home()
elif module == "validator":
    show_validator()
elif module == "detector":
    show_detector()
elif module == "scanner":
    show_scanner()
elif module == "mapper":
    show_mapper()
else:
    show_home()
