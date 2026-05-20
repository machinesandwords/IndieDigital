import streamlit as st
import anthropic
import json
import time
import csv
import io
import concurrent.futures
from datetime import datetime

st.set_page_config(
    page_title="Indie Digital · Citizen Dev Toolkit",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&family=Source+Sans+3:wght@400;600&display=swap');

    html, body, [class*="css"] { font-family: 'Source Sans 3', sans-serif; }
    .block-container { padding-top: 3.5rem; padding-bottom: 3rem; }

    .stButton > button {
        background-color: #2d2418;
        color: #f5ede0;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.82rem;
        font-weight: 500;
        border: none;
        padding: 0.6rem 1.8rem;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        transition: background 0.2s;
    }
    .stButton > button:hover { background-color: #c0392b; color: #fff; }

    .indie-header { font-family: 'Lora', serif; color: #2d2418; }
    .mono-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #9e8e80; letter-spacing: 0.12em; text-transform: uppercase; }

    /* Verdict */
    .verdict-green { background:#f0faf0; border:2px solid #27ae60; border-radius:6px; padding:1.2rem 1.5rem; margin-bottom:1rem; }
    .verdict-yellow { background:#fffbf0; border:2px solid #e67e22; border-radius:6px; padding:1.2rem 1.5rem; margin-bottom:1rem; }
    .verdict-red { background:#fdf5f5; border:2px solid #c0392b; border-radius:6px; padding:1.2rem 1.5rem; margin-bottom:1rem; }
    .signal-green { color:#27ae60; font-weight:700; font-size:1.05rem; }
    .signal-yellow { color:#e67e22; font-weight:700; font-size:1.05rem; }
    .signal-red { color:#c0392b; font-weight:700; font-size:1.05rem; }
    .conf-high { color:#27ae60; font-family:'IBM Plex Mono',monospace; font-size:0.78rem; }
    .conf-medium { color:#e67e22; font-family:'IBM Plex Mono',monospace; font-size:0.78rem; }
    .conf-low { color:#c0392b; font-family:'IBM Plex Mono',monospace; font-size:0.78rem; }
    .dim-summary { font-size:0.9rem; color:#4a3f35; line-height:1.6; margin-top:0.5rem; }
    .evidence-item { font-size:0.82rem; color:#6b5c50; font-family:'IBM Plex Mono',monospace; border-left:2px solid #e8d8c8; padding-left:0.75rem; margin-bottom:0.4rem; line-height:1.5; }
    .overall-verdict { font-family:'Lora',serif; font-size:1.5rem; font-weight:600; color:#2d2418; }
    .overall-sub { font-size:0.88rem; color:#6b5c50; margin-top:0.3rem; line-height:1.5; }
    .idea-chip { background:#f5ede0; border-radius:4px; padding:0.7rem 1.1rem; font-size:0.82rem; color:#4a3f35; margin-bottom:1.2rem; font-family:'IBM Plex Mono',monospace; }

    /* Scanner/Detector */
    .badge { display:inline-block; padding:2px 10px; border-radius:3px; font-size:0.73rem; font-weight:600; letter-spacing:0.06em; margin-right:6px; }
    .badge-high { background:#1a3328; color:#22c55e; }
    .badge-medium { background:#2d2006; color:#f59e0b; }
    .badge-low { background:#1c1c1c; color:#6e7681; }
    .badge-product { background:#1c2a3d; color:#388bfd; }
    .badge-direct { background:#2d0a0a; color:#f85149; }
    .badge-adjacent { background:#2d2006; color:#f59e0b; }
    .badge-reference { background:#1c1c1c; color:#6e7681; }
    .source { color:#8b949e; font-size:0.8rem; }
    .reason-text { color:#6e7681; font-size:0.82rem; margin-top:0.3rem; }
    .summary-text { color:#6b5c50; font-size:0.83rem; margin:0.5rem 0; line-height:1.5; }
    .stat-number { font-size:1.8rem; font-weight:700; font-family:'Lora',serif; }
    .stat-label { font-size:0.7rem; color:#9e8e80; letter-spacing:0.1em; font-family:'IBM Plex Mono',monospace; }
    .stale-warning { background:#1a1200; border:1px solid #3d2e00; border-left:3px solid #f59e0b; padding:6px 12px; font-size:0.78rem; color:#f59e0b; margin-bottom:8px; border-radius:3px; }

    /* Activity log */
    .log-status-posted { color:#27ae60; font-weight:600; font-size:0.85rem; }
    .log-status-drafted { color:#e67e22; font-weight:600; font-size:0.85rem; }
    .log-status-skipped { color:#9e8e80; font-weight:600; font-size:0.85rem; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
STALE_INDICATORS = [
    "2024","2023","2022","2021","2020",
    "2 years","3 years","4 years","5 years",
    "1 year ago","2 years ago","3 years ago","last year",
]

DEFAULT_QUERIES = """community forum [your product problem] 2026
[your problem] help discussion forum 2026
[your problem] software tool management 2026
[your problem] tracking organization 2026
[your problem] frustrated can't find solution 2026"""

def is_stale(post):
    combined = (post.get("age","") + " " + post.get("title","") + " " + post.get("summary","")).lower()
    return any(i in combined for i in STALE_INDICATORS)

# ── Session state ──────────────────────────────────────────────────────────────
defaults = {
    "product_name": "", "product_description": "", "product_buyer": "",
    "product_url": "", "search_queries": DEFAULT_QUERIES, "product_saved": False,
    "community_posts": [], "community_last_run": None,
    "competitor_products": [], "competitor_last_run": None,
    "validator_results": None,
    "activity_log": [],
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

# ── Shared prompts ─────────────────────────────────────────────────────────────
def community_prompt():
    return f"""You are helping market {st.session_state.product_name}, a product for {st.session_state.product_buyer}.
Product: {st.session_state.product_description}
URL: {st.session_state.product_url}

Rules:
1. Write like a knowledgeable peer — not an expert, not an operator.
2. Solve their problem FIRST. Help genuinely before any product mention.
3. Only mention {st.session_state.product_name} if it directly solves what they're asking. Never pitch.
4. If you mention it: "I actually put something together for this — it's called {st.session_state.product_name} ({st.session_state.product_url})"
5. Real people say "I think" and "in my experience." Match that register.
6. Always include the URL: {st.session_state.product_url}"""

def competitor_prompt():
    return f"""You are a competitive intelligence researcher for {st.session_state.product_name}.
Product: {st.session_state.product_description}
Target buyer: {st.session_state.product_buyer}
URL: {st.session_state.product_url}"""

def validator_context(idea):
    return f"""Product idea being validated:
- Problem it solves: {idea['problem']}
- Intended market: {idea['market']}
- Target price range: {idea['price']}
- Product format: {idea['format']}
- Geography: {idea['geography']}"""

# ── Validator functions ────────────────────────────────────────────────────────
def run_dim1(client, idea):
    try:
        r = client.messages.create(
            model="claude-opus-4-5", max_tokens=1200,
            system=validator_context(idea) + """
Search Reddit, forums, Quora, and online discussions for evidence people experience this problem.
Return JSON only:
{"signal":"green/yellow/red","confidence":"High/Medium/Low","confidence_score":1-10,
"summary":"2-3 sentences","evidence":["up to 4 concrete examples"],"reasoning":"one sentence"}
green=clear repeated demand, yellow=thin/inconsistent, red=little evidence
Return ONLY valid JSON.""",
            messages=[{"role":"user","content":f"Search demand signals: {idea['problem']} for {idea['market']}"}],
            tools=[{"type":"web_search_20250305","name":"web_search"}],
        )
        text = "".join(b.text for b in r.content if hasattr(b,"text"))
        s,e = text.find("{"), text.rfind("}")+1
        if s>=0 and e>s: return json.loads(text[s:e])
    except Exception as ex:
        return {"signal":"yellow","confidence":"Low","confidence_score":1,"summary":f"Error: {ex}","evidence":[],"reasoning":"Search failed."}

def run_dim2(client, idea):
    try:
        r = client.messages.create(
            model="claude-opus-4-5", max_tokens=1200,
            system=validator_context(idea) + """
Search Etsy, Gumroad, GitHub, Product Hunt, app stores for competing products. Also find active communities (subreddits, forums).
Return JSON only:
{"signal":"green/yellow/red","confidence":"High/Medium/Low","confidence_score":1-10,
"summary":"2-3 sentences","competitors":["up to 4 named with platform/price"],"communities":["up to 3"],"reasoning":"one sentence"}
green=clear market, yellow=some signals, red=no meaningful market
Return ONLY valid JSON.""",
            messages=[{"role":"user","content":f"Search market evidence: {idea['problem']} for {idea['market']} at {idea['price']} as {idea['format']}"}],
            tools=[{"type":"web_search_20250305","name":"web_search"}],
        )
        text = "".join(b.text for b in r.content if hasattr(b,"text"))
        s,e = text.find("{"), text.rfind("}")+1
        if s>=0 and e>s: return json.loads(text[s:e])
    except Exception as ex:
        return {"signal":"yellow","confidence":"Low","confidence_score":1,"summary":f"Error: {ex}","competitors":[],"communities":[],"reasoning":"Search failed."}

def run_dim3(client, idea, competitors):
    comp_names = ", ".join(competitors) if competitors else "existing products in this space"
    try:
        r = client.messages.create(
            model="claude-opus-4-5", max_tokens=1200,
            system=validator_context(idea) + f"""
Known competitors: {comp_names}
Search G2, Capterra, Trustpilot, Gumroad reviews, Reddit complaints, app store reviews for negative feedback and unmet needs.
Return JSON only:
{{"signal":"green/yellow/red","confidence":"High/Medium/Low","confidence_score":1-10,
"summary":"2-3 sentences","gaps":["up to 4 specific unmet needs"],"reasoning":"one sentence"}}
green=clear gaps/frustration, yellow=mild complaints, red=buyers seem satisfied
Return ONLY valid JSON.""",
            messages=[{"role":"user","content":f"Search gaps/complaints: {idea['problem']}"}],
            tools=[{"type":"web_search_20250305","name":"web_search"}],
        )
        text = "".join(b.text for b in r.content if hasattr(b,"text"))
        s,e = text.find("{"), text.rfind("}")+1
        if s>=0 and e>s: return json.loads(text[s:e])
    except Exception as ex:
        return {"signal":"yellow","confidence":"Low","confidence_score":1,"summary":f"Error: {ex}","gaps":[],"reasoning":"Search failed."}

def overall_verdict(d1, d2, d3):
    sc = {"green":3,"yellow":2,"red":1}
    total = sc.get(d1["signal"],2)+sc.get(d2["signal"],2)+sc.get(d3["signal"],2)
    avg_conf = (d1.get("confidence_score",5)+d2.get("confidence_score",5)+d3.get("confidence_score",5))/3
    if total>=8: v,h,s = "green","This idea has legs.","Strong signals across demand, market, and gaps. The fundamentals look favorable."
    elif total>=6: v,h,s = "yellow","Proceed with caution.","Mixed signals. Some dimensions look promising but others need more investigation."
    else: v,h,s = "red","Significant headwinds.","Weak signals across multiple dimensions. Consider refining the idea or targeting a different market."
    if avg_conf<4: s += " Note: confidence is low — limited data found. Try more specific inputs."
    return v,h,s

def signal_html(sig):
    icons = {"green":"🟢","yellow":"🟡","red":"🔴"}
    labels = {"green":"GO","yellow":"CAUTION","red":"STOP"}
    classes = {"green":"signal-green","yellow":"signal-yellow","red":"signal-red"}
    return f'<span class="{classes.get(sig,"signal-yellow")}">{icons.get(sig,"🟡")} {labels.get(sig,"CAUTION")}</span>'

def conf_html(conf, score):
    cls = {"High":"conf-high","Medium":"conf-medium","Low":"conf-low"}.get(conf,"conf-medium")
    return f'<span class="{cls}">Confidence: {conf} ({score}/10)</span>'

# ── Scanner/Detector functions ─────────────────────────────────────────────────
def search_community_posts(client, query):
    try:
        r = client.messages.create(
            model="claude-opus-4-5", max_tokens=1000,
            system="""Search Reddit, Prusa forums, Bambu forums, and 3D printing communities.
Return JSON array of up to 3 posts:
[{"title":"","source":"","url":"","summary":"2-3 sentences on struggle","age":"e.g. 2 days ago"}]
Prioritize last 48 hours. Return ONLY valid JSON array.""",
            messages=[{"role":"user","content":f"Search: {query}"}],
            tools=[{"type":"web_search_20250305","name":"web_search"}],
        )
        text = "".join(b.text for b in r.content if hasattr(b,"text"))
        s,e = text.find("["), text.rfind("]")+1
        if s>=0 and e>s: return json.loads(text[s:e])
    except: pass
    return []

def score_post(client, post):
    try:
        r = client.messages.create(
            model="claude-opus-4-5", max_tokens=1000,
            system=community_prompt()+"""
Return JSON only:
{"opportunity":"High/Medium/Low","reason":"one sentence","productFit":true/false,
"draft":"complete reply, peer voice, product only if productFit"}
Return ONLY valid JSON.""",
            messages=[{"role":"user","content":f'Post: "{post["title"]}"\nSource: {post.get("source","")}\nContext: {post["summary"]}'}],
        )
        text = "".join(b.text for b in r.content if hasattr(b,"text"))
        s,e = text.find("{"), text.rfind("}")+1
        if s>=0 and e>s: return json.loads(text[s:e])
    except: pass
    return {"opportunity":"Low","reason":"Could not analyze.","productFit":False,"draft":""}

def search_competitors(client, query):
    try:
        r = client.messages.create(
            model="claude-opus-4-5", max_tokens=1000,
            system="""Search Etsy, Gumroad, GitHub, Product Hunt for competing products.
Return JSON array of up to 3:
[{"name":"","platform":"","url":"","description":"2-3 sentences","price":"","seller":""}]
Return ONLY valid JSON array.""",
            messages=[{"role":"user","content":f"Search competing products: {query}"}],
            tools=[{"type":"web_search_20250305","name":"web_search"}],
        )
        text = "".join(b.text for b in r.content if hasattr(b,"text"))
        s,e = text.find("["), text.rfind("]")+1
        if s>=0 and e>s: return json.loads(text[s:e])
    except: pass
    return []

def analyze_competitor(client, product):
    try:
        r = client.messages.create(
            model="claude-opus-4-5", max_tokens=1000,
            system=competitor_prompt()+"""
Return JSON only:
{"threat":"Direct/Adjacent/Reference","price":"","platform":"",
"gaps":["up to 3"],"strengths":["up to 3"],"notes":"one sentence"}
Return ONLY valid JSON.""",
            messages=[{"role":"user","content":f'Product: "{product["name"]}"\nPlatform: {product.get("platform","")}\nDescription: {product["description"]}\nPrice: {product.get("price","Unknown")}'}],
        )
        text = "".join(b.text for b in r.content if hasattr(b,"text"))
        s,e = text.find("{"), text.rfind("}")+1
        if s>=0 and e>s: return json.loads(text[s:e])
    except: pass
    return {"threat":"Reference","gaps":[],"strengths":[],"notes":"Could not analyze."}

def get_search_queries():
    return [q.strip() for q in st.session_state.search_queries.strip().split("\n") if q.strip()]

def get_competitor_queries():
    desc = st.session_state.product_description[:60] if st.session_state.product_description else "management tool"
    name = st.session_state.product_name
    return [
        f"Etsy {desc} template spreadsheet 2026",
        f"Gumroad {desc} tool template product",
        f"GitHub {desc} open source software",
        f"{desc} software app SaaS 2026",
        f"Product Hunt {desc} management tool",
        f"Etsy spreadsheet {desc} tracking template",
        f"{name} alternative competitor {desc}",
        f"{desc} tool product comparison 2026",
    ]

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<h3 class="indie-header">💡 Indie Digital · Citizen Dev Toolkit</h3>', unsafe_allow_html=True)
st.markdown('<div class="mono-label">Business Validator · Competitor Detector · Community Scanner · Activity Log</div>', unsafe_allow_html=True)
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# PRODUCT SETUP — above tabs
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("⚙️ Product Setup — click to edit", expanded=not st.session_state.product_saved):
    st.caption("Fill in your product details once. All tabs use this information.")
    col1, col2 = st.columns(2)
    with col1:
        name_in = st.text_input("Product name", value=st.session_state.product_name, placeholder="e.g. Offset3D", key="name_in")
        buyer_in = st.text_input("Who it's for", value=st.session_state.product_buyer, placeholder="e.g. 3D print farm operators, 1-20 printers", key="buyer_in")
    with col2:
        url_in = st.text_input("Your URL", value=st.session_state.product_url, placeholder="e.g. offsetos.com/offset3D", key="url_in")
        desc_in = st.text_area("What it does", value=st.session_state.product_description, placeholder="2-3 sentences describing the problem it solves.", height=100, key="desc_in")

    queries_in = st.text_area(
        "Search queries — one per line (Community Scanner)",
        value=st.session_state.search_queries, height=140, key="queries_in",
        help="Each line is an independent search. Five to ten lines is a good range.\n\nBest pattern: the frustrated phrase — what someone types when actively annoyed by the problem."
    )

    if st.button("💾 Save Product Details", key="save_product"):
        if name_in and desc_in:
            st.session_state.product_name = name_in
            st.session_state.product_description = desc_in
            st.session_state.product_buyer = buyer_in
            st.session_state.product_url = url_in
            st.session_state.search_queries = queries_in
            st.session_state.product_saved = True
            st.session_state.community_posts = []
            st.session_state.competitor_products = []
            st.success(f"Saved. Toolkit configured for {name_in}.")
            st.rerun()
        else:
            st.warning("Please add at least a product name and description.")

if st.session_state.product_saved:
    st.caption(f"Active product: **{st.session_state.product_name}** · {st.session_state.product_url}")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs(["🔦 Business Validator", "🔍 Competitor Detector", "📡 Community Scanner", "📝 Activity Log"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — BUSINESS VALIDATOR
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("**Should you build this? Get a red/green viability verdict across three dimensions.**")
    st.write("")

    with st.expander("📋 Your Idea", expanded=st.session_state.validator_results is None):
        c1, c2 = st.columns(2)
        with c1:
            v_problem = st.text_area("Problem it solves", placeholder="Describe the pain from your customer's perspective.", height=100, key="v_problem",
                help="Write this as your customer would describe it, not as a product feature.")
            v_market = st.text_input("Intended market", placeholder="e.g. Small 3D print farm operators, 1-20 printers", key="v_market")
            v_price = st.text_input("Target price range", placeholder="e.g. $9-15 one-time purchase", key="v_price")
        with c2:
            v_format = st.selectbox("Product format", ["Digital download (PDF/guide)","Spreadsheet/template","Web app (hosted)","Mobile app","Software download","Physical product","Service/consulting"], key="v_format")
            v_geo = st.selectbox("Geography", ["Global","United States","North America","Europe","UK","Australia/NZ","Other"], key="v_geo")
            st.write("")
            validate_btn = st.button("🔦 VALIDATE THIS IDEA", key="validate_btn", use_container_width=True)

    if validate_btn:
        if not v_problem or not v_market:
            st.warning("Please describe the problem and intended market.")
        else:
            idea = {"problem":v_problem,"market":v_market,"price":v_price or "unknown","format":v_format,"geography":v_geo}
            client = get_client()
            with st.spinner("Searching demand signals and market landscape simultaneously..."):
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
                    f1 = ex.submit(run_dim1, client, idea)
                    f2 = ex.submit(run_dim2, client, idea)
                    d1 = f1.result()
                    d2 = f2.result()
            with st.spinner("Analyzing gaps in existing products..."):
                d3 = run_dim3(client, idea, d2.get("competitors",[]))
            v, h, s = overall_verdict(d1, d2, d3)
            st.session_state.validator_results = {"d1":d1,"d2":d2,"d3":d3,"verdict":v,"headline":h,"sub":s,"idea":idea}
            st.rerun()

    if st.session_state.validator_results:
        res = st.session_state.validator_results
        d1,d2,d3 = res["d1"],res["d2"],res["d3"]
        idea = res["idea"]

        st.markdown(f'<div class="idea-chip">Validating: {idea["problem"][:100]}{"..." if len(idea["problem"])>100 else ""} · {idea["market"]} · {idea["price"]}</div>', unsafe_allow_html=True)

        vc = f"verdict-{res['verdict']}"
        vi = {"green":"🟢","yellow":"🟡","red":"🔴"}.get(res["verdict"],"🟡")
        st.markdown(f'<div class="{vc}"><div class="mono-label">Overall Verdict</div><div class="overall-verdict">{vi} {res["headline"]}</div><div class="overall-sub">{res["sub"]}</div></div>', unsafe_allow_html=True)
        st.divider()

        for dim, title, question, evidence_key, evidence_label in [
            (d1, "📣 Demand Exists", "Are people describing this problem online?", "evidence", "Evidence found"),
            (d2, "🏪 Market is Proven", "Do competitors and communities already exist?", None, None),
            (d3, "🕳️ Gaps Exist", "Are buyers frustrated with existing options?", "gaps", "Gaps identified"),
        ]:
            with st.expander(f"{title} — {dim.get('summary','')[:70]}...", expanded=True):
                ca, cb = st.columns([3,1])
                with ca:
                    st.markdown(f'<div style="font-family:Lora,serif;font-weight:600;color:#2d2418">{question}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="dim-summary">{dim.get("summary","")}</div>', unsafe_allow_html=True)
                with cb:
                    st.markdown(signal_html(dim.get("signal","yellow")), unsafe_allow_html=True)
                    st.markdown(conf_html(dim.get("confidence","Medium"), dim.get("confidence_score",5)), unsafe_allow_html=True)

                if dim is d2:
                    cc, cd = st.columns(2)
                    with cc:
                        comps = dim.get("competitors",[])
                        if comps:
                            st.markdown('<div class="mono-label">Competitors</div>', unsafe_allow_html=True)
                            for c in comps: st.markdown(f'<div class="evidence-item">{c}</div>', unsafe_allow_html=True)
                    with cd:
                        comms = dim.get("communities",[])
                        if comms:
                            st.markdown('<div class="mono-label">Communities</div>', unsafe_allow_html=True)
                            for c in comms: st.markdown(f'<div class="evidence-item">{c}</div>', unsafe_allow_html=True)
                elif evidence_key:
                    items = dim.get(evidence_key,[])
                    if items:
                        st.write("")
                        st.markdown(f'<div class="mono-label">{evidence_label}</div>', unsafe_allow_html=True)
                        for item in items: st.markdown(f'<div class="evidence-item">{item}</div>', unsafe_allow_html=True)

                st.markdown(f'<div style="font-size:0.78rem;color:#9e8e80;margin-top:0.8rem;font-style:italic">{dim.get("reasoning","")}</div>', unsafe_allow_html=True)

        if st.button("🔄 Validate a Different Idea", key="reset_validator"):
            st.session_state.validator_results = None
            st.rerun()

    else:
        st.markdown('<div style="text-align:center;padding:3rem 2rem;color:#9e8e80"><div style="font-size:2rem;margin-bottom:1rem">🔦</div><div style="font-family:Lora,serif;font-size:1rem;color:#4a3f35;margin-bottom:0.5rem">Should you build this?</div><div style="font-size:0.85rem">Fill in your idea above and hit Validate. About 2 minutes.</div></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — COMPETITOR DETECTOR
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    if not st.session_state.product_saved:
        st.info("Complete Product Setup above before running the Competitor Detector.")
    else:
        c1, c2 = st.columns([4,1])
        with c1: st.markdown("**Find competing and adjacent products across Etsy, Gumroad, GitHub, and the web.**")
        with c2: run_comp = st.button("▶ RUN SCAN", key="run_comp", use_container_width=True)

        if run_comp:
            client = get_client()
            all_products, seen = [], set()
            queries = get_competitor_queries()
            pb = st.progress(0, text="Scanning for competitors...")
            for i, query in enumerate(queries):
                pb.progress(int((i/len(queries))*50), text=f"Searching... ({i+1}/{len(queries)})")
                for p in search_competitors(client, query):
                    k = p.get("name","").lower().strip()
                    if k and k not in seen:
                        seen.add(k); all_products.append(p)
                time.sleep(0.3)
            if not all_products:
                pb.empty(); st.warning("No competing products found. Try again in a few minutes.")
            else:
                analyzed = []
                for i, product in enumerate(all_products):
                    pb.progress(50+int((i/len(all_products))*50), text=f"Analyzing... ({i+1}/{len(all_products)})")
                    a = analyze_competitor(client, product)
                    analyzed.append({**product, **a, "id":i})
                    time.sleep(0.2)
                analyzed.sort(key=lambda x: {"Direct":0,"Adjacent":1,"Reference":2}.get(x.get("threat","Reference"),2))
                st.session_state.competitor_products = analyzed
                st.session_state.competitor_last_run = time.strftime("%B %d, %Y at %I:%M %p")
                pb.empty(); st.rerun()

        if st.session_state.competitor_products:
            prods = st.session_state.competitor_products
            direct = [p for p in prods if p.get("threat")=="Direct"]
            adjacent = [p for p in prods if p.get("threat")=="Adjacent"]
            ref = [p for p in prods if p.get("threat")=="Reference"]

            c1,c2,c3,c4 = st.columns(4)
            with c1: st.markdown(f'<div class="stat-number">{len(prods)}</div><div class="stat-label">FOUND</div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="stat-number" style="color:#c0392b">{len(direct)}</div><div class="stat-label">DIRECT</div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="stat-number" style="color:#e67e22">{len(adjacent)}</div><div class="stat-label">ADJACENT</div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="stat-number" style="color:#9e8e80">{len(ref)}</div><div class="stat-label">REFERENCE</div>', unsafe_allow_html=True)
            if st.session_state.competitor_last_run: st.caption(f"Last run: {st.session_state.competitor_last_run}")
            st.divider()

            filt = st.radio("Filter:", ["All","Direct","Adjacent","Reference"], horizontal=True, label_visibility="collapsed", key="comp_filt")
            display = prods if filt=="All" else [p for p in prods if p.get("threat")==filt]

            for prod in display:
                threat = prod.get("threat","Reference")
                tbadge = {"Direct":"🔴 Direct","Adjacent":"🟡 Adjacent","Reference":"⚪ Reference"}.get(threat,threat)
                bcls = {"Direct":"badge-direct","Adjacent":"badge-adjacent","Reference":"badge-reference"}.get(threat,"badge-reference")
                with st.expander(f"{prod.get('name','Unknown')} — {prod.get('platform','')} — {prod.get('price','')}", expanded=False):
                    st.markdown(f'<span class="badge {bcls}">{tbadge}</span><span class="source">{prod.get("platform","")} · {prod.get("seller","")}</span>', unsafe_allow_html=True)
                    st.markdown(f'<div class="summary-text"><strong style="color:#9e8e80;font-size:0.72rem">DESCRIPTION &nbsp;</strong>{prod.get("description","")}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="reason-text">{prod.get("notes","")}</div>', unsafe_allow_html=True)
                    url = prod.get("url","")
                    if url: st.markdown(f"[→ View listing]({url})")
                    cg, cs = st.columns(2)
                    with cg:
                        gaps = prod.get("gaps",[])
                        if gaps:
                            st.markdown("**Their gaps:**")
                            for g in gaps: st.markdown(f"- {g}")
                    with cs:
                        strs = prod.get("strengths",[])
                        if strs:
                            st.markdown("**Their strengths:**")
                            for s in strs: st.markdown(f"- {s}")
        else:
            st.markdown('<div style="text-align:center;padding:3rem 2rem;color:#9e8e80"><div style="font-size:2rem;margin-bottom:1rem">🔍</div><div style="font-size:0.9rem;color:#4a3f35;margin-bottom:0.4rem">No competitors loaded yet</div><div style="font-size:0.82rem">Hit RUN SCAN to search Etsy, Gumroad, GitHub, and the broader web</div></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — COMMUNITY SCANNER
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    if not st.session_state.product_saved:
        st.info("Complete Product Setup above before running the Community Scanner.")
    else:
        c1, c2 = st.columns([4,1])
        with c1: st.markdown("**Find posts where you can add value and mention your product organically.**")
        with c2: run_scan = st.button("▶ RUN SCAN", key="run_scan", use_container_width=True)

        if run_scan:
            queries = get_search_queries()
            if not queries:
                st.warning("Add search queries in Product Setup above.")
            else:
                client = get_client()
                all_posts, seen = [], set()
                pb = st.progress(0, text="Starting scan...")
                for i, query in enumerate(queries):
                    pb.progress(int((i/len(queries))*50), text=f"Scanning communities... ({i+1}/{len(queries)})")
                    for post in search_community_posts(client, query):
                        k = post.get("title","").lower().strip()
                        if k and k not in seen:
                            seen.add(k); all_posts.append(post)
                    time.sleep(0.3)
                if not all_posts:
                    pb.empty(); st.warning("No posts found. Try adjusting queries or try again.")
                else:
                    scored = []
                    for i, post in enumerate(all_posts):
                        pb.progress(50+int((i/len(all_posts))*50), text=f"Drafting responses... ({i+1}/{len(all_posts)})")
                        a = score_post(client, post)
                        scored.append({**post, **a, "id":i, "stale":is_stale(post)})
                        time.sleep(0.2)
                    scored.sort(key=lambda x: ({"High":0,"Medium":1,"Low":2}.get(x.get("opportunity","Low"),2), 1 if x.get("stale") else 0))
                    st.session_state.community_posts = scored
                    st.session_state.community_last_run = time.strftime("%B %d, %Y at %I:%M %p")
                    pb.empty(); st.rerun()

        if st.session_state.community_posts:
            posts = st.session_state.community_posts
            fresh = [p for p in posts if not p.get("stale")]
            stale = [p for p in posts if p.get("stale")]

            c1,c2,c3,c4,c5 = st.columns(5)
            with c1: st.markdown(f'<div class="stat-number">{len(fresh)}</div><div class="stat-label">FRESH</div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="stat-number" style="color:#27ae60">{sum(1 for p in fresh if p.get("opportunity")=="High")}</div><div class="stat-label">HIGH OPP</div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="stat-number" style="color:#e67e22">{sum(1 for p in fresh if p.get("opportunity")=="Medium")}</div><div class="stat-label">MEDIUM OPP</div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="stat-number" style="color:#388bfd">{sum(1 for p in fresh if p.get("productFit"))}</div><div class="stat-label">PRODUCT FITS</div>', unsafe_allow_html=True)
            with c5: st.markdown(f'<div class="stat-number" style="color:#9e8e80">{len(stale)}</div><div class="stat-label">FILTERED OLD</div>', unsafe_allow_html=True)
            if st.session_state.community_last_run: st.caption(f"Last run: {st.session_state.community_last_run}")
            st.divider()

            filt = st.radio("Filter:", ["All","High","Medium","Low"], horizontal=True, label_visibility="collapsed", key="scan_filt")
            display = fresh if filt=="All" else [p for p in fresh if p.get("opportunity")==filt]
            st.markdown(f"**{len(display)} posts** · {len(stale)} older post(s) filtered")
            st.write("")

            for post in display:
                opp = post.get("opportunity","Low")
                blabel = {"High":"🎯 High","Medium":"◎ Medium","Low":"· Low"}.get(opp,opp)
                pfit = post.get("productFit",False)
                with st.expander(post.get("title","Untitled"), expanded=False):
                    bhtml = f'<span class="badge badge-{opp.lower()}">{blabel}</span>'
                    bhtml += f'<span class="source">{post.get("source","")}</span>'
                    if pfit: bhtml += ' &nbsp;<span class="badge badge-product">↗ PRODUCT FIT</span>'
                    bhtml += f'&nbsp;&nbsp;<span style="color:#9e8e80;font-size:0.78rem">{post.get("age","")}</span>'
                    st.markdown(bhtml, unsafe_allow_html=True)
                    st.markdown(f'<div class="reason-text">{post.get("reason","")}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="summary-text"><strong style="color:#9e8e80;font-size:0.72rem">CONTEXT &nbsp;</strong>{post.get("summary","")}</div>', unsafe_allow_html=True)
                    url = post.get("url","")
                    if url and url not in ["","https://reddit.com"]: st.markdown(f"[→ View post]({url})")
                    st.markdown("---")
                    st.markdown("**Suggested response** — includes product mention" if pfit else "**Suggested response** — helpful only, no pitch")
                    draft = post.get("draft","No draft generated.")
                    st.text_area("draft", value=draft, height=220, key=f"draft_{post.get('id',0)}", label_visibility="collapsed")
                    if st.button("+ Log this response", key=f"log_{post.get('id',0)}"):
                        st.session_state.activity_log.append({"date":datetime.now().strftime("%Y-%m-%d %H:%M"),"platform":post.get("source",""),"title":post.get("title",""),"url":post.get("url",""),"notes":"","status":"Drafted"})
                        st.success("Added to Activity Log.")
                    st.caption("Review and edit before posting. You own every reply.")

            if stale:
                st.write("")
                if st.checkbox(f"Show {len(stale)} older post(s)"):
                    for post in stale:
                        with st.expander(f"⚠ {post.get('title','')}", expanded=False):
                            st.markdown(f'<div class="stale-warning">⚠ May be older than 48 hours ({post.get("age","unknown")})</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="summary-text">{post.get("summary","")}</div>', unsafe_allow_html=True)
                            url = post.get("url","")
                            if url and url not in ["","https://reddit.com"]: st.markdown(f"[→ View post]({url})")
                            st.text_area("draft", value=post.get("draft",""), height=180, key=f"sdraft_{post.get('id',0)}", label_visibility="collapsed")
                            st.caption("Verify date before posting.")
        else:
            st.markdown('<div style="text-align:center;padding:3rem 2rem;color:#9e8e80"><div style="font-size:2rem;margin-bottom:1rem">📡</div><div style="font-size:0.9rem;color:#4a3f35;margin-bottom:0.4rem">No posts loaded yet</div><div style="font-size:0.82rem">Hit RUN SCAN to search online communities for response opportunities</div></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — ACTIVITY LOG
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("**Track where you've engaged. One entry per response posted.**")
    st.write("")

    with st.expander("➕ Add Entry", expanded=len(st.session_state.activity_log)==0):
        c1,c2 = st.columns(2)
        with c1:
            lp = st.text_input("Platform / Community", placeholder="e.g. r/3dprintingbusiness", key="lp")
            lu = st.text_input("Post URL", placeholder="https://...", key="lu")
        with c2:
            lt = st.text_input("Post Title", placeholder="What was the post about?", key="lt")
            ls = st.selectbox("Status", ["Posted","Drafted","Skipped"], key="ls")
        ln = st.text_input("Notes", placeholder="Optional — what did you say, any product mention?", key="ln")
        if st.button("Add to Log", key="add_log"):
            if lp or lt:
                st.session_state.activity_log.append({"date":datetime.now().strftime("%Y-%m-%d %H:%M"),"platform":lp,"title":lt,"url":lu,"notes":ln,"status":ls})
                st.success("Entry added.")
                st.rerun()
            else:
                st.warning("Add at least a platform or title.")

    if st.session_state.activity_log:
        log = list(reversed(st.session_state.activity_log))
        total = len(log)
        posted = sum(1 for e in log if e.get("status")=="Posted")
        drafted = sum(1 for e in log if e.get("status")=="Drafted")

        c1,c2,c3 = st.columns(3)
        with c1: st.markdown(f'<div class="stat-number">{total}</div><div class="stat-label">TOTAL</div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-number" style="color:#27ae60">{posted}</div><div class="stat-label">POSTED</div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-number" style="color:#e67e22">{drafted}</div><div class="stat-label">DRAFTED</div>', unsafe_allow_html=True)
        st.divider()

        if st.button("⬇ Export CSV"):
            out = io.StringIO()
            w = csv.DictWriter(out, fieldnames=["date","platform","title","url","status","notes"])
            w.writeheader(); w.writerows(st.session_state.activity_log)
            st.download_button("Download activity_log.csv", data=out.getvalue(), file_name=f"activity_log_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

        st.write("")
        for i, entry in enumerate(log):
            scls = {"Posted":"log-status-posted","Drafted":"log-status-drafted","Skipped":"log-status-skipped"}.get(entry.get("status"),"log-status-skipped")
            with st.expander(f"{entry.get('date','')} · {entry.get('platform','')} · {entry.get('title','')[:60]}", expanded=False):
                c1,c2 = st.columns([3,1])
                with c1:
                    url = entry.get("url","")
                    if url: st.markdown(f"[→ View post]({url})")
                    if entry.get("notes"): st.markdown(f'<div class="reason-text">{entry.get("notes")}</div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<span class="{scls}">{entry.get("status","")}</span>', unsafe_allow_html=True)
                if st.button("🗑 Remove", key=f"rm_{i}"):
                    st.session_state.activity_log.pop(len(st.session_state.activity_log)-1-i)
                    st.rerun()
    else:
        st.markdown('<div style="text-align:center;padding:3rem 2rem;color:#9e8e80"><div style="font-size:2rem;margin-bottom:1rem">📝</div><div style="font-size:0.9rem;color:#4a3f35;margin-bottom:0.4rem">No activity logged yet</div><div style="font-size:0.82rem">Add an entry above, or use the Log button in the Community Scanner</div></div>', unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption("Indie Digital · Citizen Dev Toolkit · Manual review required before every post.")
