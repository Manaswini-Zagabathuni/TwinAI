import streamlit as st
import anthropic
import json
import time
from datetime import datetime

# ── Model config ─────────────────────────────────────────────────────────────
MODEL = "claude-haiku-4-5-20251001"  # Fast, reliable, less overloaded
 
def call_claude(api_key, messages, max_tokens=800, retries=3):
    """Call Claude with automatic retry on overload (529)."""
    client = anthropic.Anthropic(api_key=api_key)
    for attempt in range(retries):
        try:
            return client.messages.create(
                model=MODEL,
                max_tokens=max_tokens,
                messages=messages
            )
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < retries - 1:
                wait = 3 * (attempt + 1)
                st.toast(f"API busy, retrying in {wait}s... (attempt {attempt+1}/{retries})", icon="⏳")
                time.sleep(wait)
            else:
                raise

st.set_page_config(
    page_title="TwinAI - Your AI Writing Twin",
    page_icon="💕",
    layout="wide"
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    .main-header h1 { font-size: 2.5rem; margin: 0; }
    .main-header p  { font-size: 1.1rem; margin: 0.5rem 0 0; opacity: 0.9; }

    .style-card {
        background: #f8f9ff;
        border: 1px solid #e0e3f0;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
        position: relative;
    }
    .style-card p { margin: 0; font-size: 0.9rem; color: #444; }

    .stat-box {
        background: white;
        border: 1px solid #e0e3f0;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .stat-box .number { font-size: 1.8rem; font-weight: 700; color: #667eea; }
    .stat-box .label  { font-size: 0.8rem; color: #888; margin-top: 4px; }

    .response-box {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 10px;
        padding: 1.25rem;
        font-size: 0.95rem;
        line-height: 1.7;
        white-space: pre-wrap;
    }
    .tone-badge {
        display: inline-block;
        background: #ede9fe;
        color: #6d28d9;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .history-item {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
    }
    .history-item .ts { color: #9ca3af; font-size: 0.75rem; }
    .section-title { font-size: 1.1rem; font-weight: 600; color: #1e1b4b; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Session state init ───────────────────────────────────────────────────────
if "writing_samples" not in st.session_state:
    st.session_state.writing_samples = []
if "history" not in st.session_state:
    st.session_state.history = []
if "style_analysis" not in st.session_state:
    st.session_state.style_analysis = None

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>💕 TwinAI</h1>
    <p>Your AI-powered writing twin - learns your style, writes like you</p>
</div>
""", unsafe_allow_html=True)

# ── API Key (reads from Streamlit secrets if available) ──────────────────────
def get_api_key(manual_key):
    if manual_key and manual_key.strip():
        return manual_key.strip()
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return None

with st.sidebar:
    st.markdown("###  Configuration")
    # Only show input if secret is not set
    secret_set = "ANTHROPIC_API_KEY" in st.secrets if hasattr(st, "secrets") else False
    if secret_set:
        st.success(" API key loaded from secrets")
        manual_key = ""
    else:
        manual_key = st.text_input(
            "Anthropic API Key",
            type="password",
            placeholder="sk-ant-...",
            help="Get your free key at console.anthropic.com"
        )
    api_key = get_api_key(manual_key)
    st.markdown("---")

    # Stats
    st.markdown("###  Your Twin Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <div class="number">{len(st.session_state.writing_samples)}</div>
            <div class="label">Samples</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <div class="number">{len(st.session_state.history)}</div>
            <div class="label">Replies</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Style analysis display
    if st.session_state.style_analysis:
        st.markdown("###  Detected Style")
        analysis = st.session_state.style_analysis
        for trait in analysis.get("traits", []):
            st.markdown(f'<span class="tone-badge">{trait}</span>', unsafe_allow_html=True)
        if analysis.get("summary"):
            st.caption(analysis["summary"])

    st.markdown("---")
    if st.button(" Clear All Data", use_container_width=True):
        st.session_state.writing_samples = []
        st.session_state.history = []
        st.session_state.style_analysis = None
        st.rerun()

# ── Main layout ──────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["✍️ Train Your Twin", "💬 Generate Reply", "📜 History"])

# ═══════════════════════════════════════════
# TAB 1 — Training
# ═══════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-title">Add Writing Samples</div>', unsafe_allow_html=True)
    st.caption("Paste emails, Slack messages, or any text you've written. The more samples, the better your twin!")

    sample_type = st.selectbox(
        "Sample type",
        ["Email", "Slack / Chat", "LinkedIn Message", "Report / Document", "Other"],
        label_visibility="collapsed"
    )

    new_sample = st.text_area(
        "Paste a writing sample",
        height=130,
        placeholder="Hi John,\n\nJust following up on yesterday's meeting. I'll send the slides by EOD.\n\nThanks!"
    )

    col_a, col_b = st.columns([3, 1])
    with col_a:
        add_clicked = st.button("➕ Add Sample", use_container_width=True)
    with col_b:
        analyze_clicked = st.button("🔍 Analyze Style", use_container_width=True,
                                     disabled=len(st.session_state.writing_samples) == 0)

    if add_clicked and new_sample.strip():
        st.session_state.writing_samples.append({
            "text": new_sample.strip(),
            "type": sample_type,
            "added": datetime.now().strftime("%b %d, %H:%M")
        })
        st.success("Sample added!")
        st.rerun()

    # Analyze style via Claude
    if analyze_clicked and api_key:
        with st.spinner("Analyzing your writing style..."):
            try:
                all_samples = "\n\n---\n\n".join(
                    [s["text"] for s in st.session_state.writing_samples]
                )
                msg = call_claude(api_key, [{
                        "role": "user",
                        "content": f"""Analyze the writing style in these samples and return ONLY valid JSON with no extra text:
{{
  "traits": ["trait1", "trait2", "trait3", "trait4"],
  "summary": "One sentence description of the writing style."
}}

Traits should be short labels like: Formal, Casual, Concise, Warm, Direct, Professional, Friendly, etc.

Samples:
{all_samples}"""
                }], max_tokens=400)
                raw = msg.content[0].text.strip()
                # strip markdown fences if present
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                st.session_state.style_analysis = json.loads(raw.strip())
                st.success("Style analyzed! Check the sidebar.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    elif analyze_clicked and not api_key:
        st.warning("Please enter your API key in the sidebar.")

    # Show existing samples
    if st.session_state.writing_samples:
        st.markdown("---")
        st.markdown(f'<div class="section-title">Your Samples ({len(st.session_state.writing_samples)})</div>', unsafe_allow_html=True)
        for i, sample in enumerate(st.session_state.writing_samples):
            with st.container():
                col1, col2 = st.columns([10, 1])
                with col1:
                    st.markdown(f"""
                    <div class="style-card">
                        <p><strong>{sample['type']}</strong> · <span style="color:#9ca3af;font-size:0.8rem">{sample['added']}</span></p>
                        <p style="margin-top:6px">{sample['text'][:200]}{'...' if len(sample['text']) > 200 else ''}</p>
                    </div>""", unsafe_allow_html=True)
                with col2:
                    if st.button("✕", key=f"del_{i}"):
                        st.session_state.writing_samples.pop(i)
                        st.rerun()
    else:
        st.info("No samples yet. Add at least 2–3 samples for best results.")

# ═══════════════════════════════════════════
# TAB 2 — Generate Reply
# ═══════════════════════════════════════════
with tab2:
    if len(st.session_state.writing_samples) == 0:
        st.warning(" Go to the **Train Your Twin** tab and add at least one writing sample first.")
    else:
        st.markdown('<div class="section-title">Message to Respond To</div>', unsafe_allow_html=True)

        context = st.text_input(
            "Context (optional)",
            placeholder="e.g. This is from my manager asking about a project deadline"
        )

        incoming = st.text_area(
            "Paste the message you want to reply to",
            height=120,
            placeholder="Can you send over the final report by end of day?"
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            tone_override = st.selectbox("Tone", ["Auto (match my style)", "More formal", "More casual", "Shorter", "More detailed"])
        with col2:
            platform = st.selectbox("Platform", ["Email", "Slack / Chat", "LinkedIn", "SMS", "General"])
        with col3:
            num_variants = st.selectbox("Variants", [1, 2, 3], index=1)

        generate_btn = st.button(" Generate Reply", use_container_width=True,
                                  disabled=not incoming.strip())

        if generate_btn:
            if not api_key:
                st.error("Please enter your Anthropic API key in the sidebar.")
            else:
                all_samples = "\n\n---\n\n".join(
                    [f"[{s['type']}]\n{s['text']}" for s in st.session_state.writing_samples]
                )
                tone_note = "" if tone_override == "Auto (match my style)" else f"\nAdditional instruction: Make the reply {tone_override.lower()}."

                prompt = f"""You are TwinAI. Your job is to generate {num_variants} reply variant(s) to a message, written in the exact style of the user based on their writing samples.

WRITING SAMPLES (learn the user's exact tone, vocabulary, sentence length, greeting/sign-off style):
{all_samples}

PLATFORM: {platform}
{f'CONTEXT: {context}' if context else ''}
MESSAGE TO REPLY TO:
{incoming}
{tone_note}

Instructions:
- Match the user's writing style precisely (tone, formality, sentence structure, how they sign off)
- Generate exactly {num_variants} variant(s)
- Separate variants with: --- VARIANT X ---
- Do NOT add any explanation, just the reply text(s)
"""

                with st.spinner("Your twin is writing..."):
                    try:
                        msg = call_claude(api_key, [{"role": "user", "content": prompt}])
                        result = msg.content[0].text.strip()

                        # Save to history
                        st.session_state.history.append({
                            "timestamp": datetime.now().strftime("%b %d, %H:%M"),
                            "incoming": incoming,
                            "platform": platform,
                            "response": result
                        })

                        # Display
                        st.markdown("---")
                        st.markdown('<div class="section-title">Generated Replies</div>', unsafe_allow_html=True)

                        if num_variants == 1:
                            st.markdown(f'<div class="response-box">{result}</div>', unsafe_allow_html=True)
                            st.code(result, language=None)
                        else:
                            parts = result.split("--- VARIANT")
                            parts = [p.strip().lstrip("0123456789 -–").strip() for p in parts if p.strip()]
                            for idx, part in enumerate(parts, 1):
                                st.markdown(f"**Variant {idx}**")
                                st.markdown(f'<div class="response-box">{part}</div>', unsafe_allow_html=True)
                                st.code(part, language=None)
                                st.markdown("")

                    except anthropic.APIStatusError as e:
                        if e.status_code == 529:
                            st.error("⚠️ Anthropic servers are busy right now. Please wait 30 seconds and try again.")
                        else:
                            st.error(f"API error: {e}")
                    except Exception as e:
                        st.error(f"Error generating reply: {e}")

# ═══════════════════════════════════════════
# TAB 3 — History
# ═══════════════════════════════════════════
with tab3:
    if not st.session_state.history:
        st.info("No replies generated yet. Head to the **Generate Reply** tab to get started!")
    else:
        st.markdown(f'<div class="section-title">Reply History ({len(st.session_state.history)} total)</div>', unsafe_allow_html=True)
        for item in reversed(st.session_state.history):
            with st.expander(f"🕐 {item['timestamp']} · {item['platform']} · \"{item['incoming'][:60]}...\""):
                st.markdown("**Original message:**")
                st.info(item["incoming"])
                st.markdown("**Generated reply:**")
                st.markdown(f'<div class="response-box">{item["response"]}</div>', unsafe_allow_html=True)

        if st.button("Export History as JSON"):
            st.download_button(
                "⬇️ Download history.json",
                data=json.dumps(st.session_state.history, indent=2),
                file_name="twinai_history.json",
                mime="application/json"
            )
