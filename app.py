"""
Smart Study Generator — Main Streamlit Application
IBM Granite + watsonx.ai powered adaptive study companion
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import datetime
import time

# ── Local modules ──────────────────────────────────────────────────────────────
from modules.granite_ai      import get_ai
from modules.content_processor import (
    process_uploaded_file, clean_text, estimate_reading_time,
    count_words, SAMPLE_CONTENTS
)
from modules.study_planner   import (
    init_session, record_quiz_result, record_study_session,
    get_performance_summary, get_weekly_study_data,
    get_topic_performance, generate_alerts
)
from modules.ui_components   import (
    metric_card, alert_box, section_header, progress_bar,
    flashcard_display, quiz_question_card, render_concept_map, chat_message,
    COLORS
)

# ══════════════════════════════════════════════════════════════════════════════
# Page configuration
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Smart Study Generator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Base ── */
    .stApp { background: linear-gradient(135deg, #EBF5FB 0%, #F8F9FA 100%); }
    .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1200px; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1E3A5F 0%, #2E86AB 100%); }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stRadio label { color: white !important; }
    [data-testid="stSidebar"] .stButton button {
        background: rgba(255,255,255,0.15) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
        border-radius: 8px !important;
        width: 100%;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background: rgba(255,255,255,0.25) !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: white;
        border-radius: 12px;
        padding: 6px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 18px;
        font-weight: 500;
        color: #1E3A5F;
    }
    .stTabs [aria-selected="true"] {
        background: #1E3A5F !important;
        color: white !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important; }

    /* ── Cards / expanders ── */
    .stExpander { border-radius: 10px !important; border: 1px solid #E9ECEF !important; }

    /* ── Text input ── */
    .stTextArea textarea, .stTextInput input {
        border-radius: 8px !important;
        border: 1px solid #CED4DA !important;
    }

    /* ── Metrics ── */
    [data-testid="metric-container"] {
        background: white; border-radius: 10px;
        padding: 14px !important; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }

    /* ── Hide default Streamlit branding ── */
    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }
</style>
""", unsafe_allow_html=True)

# ── Init session & AI ──────────────────────────────────────────────────────────
init_session(st)
ai = get_ai()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:10px 0 20px;'>
        <div style='font-size:48px;'>🧠</div>
        <h2 style='margin:4px 0;font-size:20px;'>Smart Study Generator</h2>
        <p style='opacity:0.8;font-size:12px;margin:0;'>Powered by IBM Granite AI</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Input source ──────────────────────────────────────────────────────────
    st.markdown("### 📥 Load Content")
    input_mode = st.radio("Source", ["📁 Upload File", "📝 Paste Text", "🎯 Sample Topics"], label_visibility="collapsed")

    if input_mode == "📁 Upload File":
        uploaded = st.file_uploader(
            "Upload notes / textbook",
            type=["pdf", "txt", "docx", "png", "jpg", "jpeg"],
            help="PDF, DOCX, TXT, or image files",
        )
        if uploaded:
            with st.spinner("Extracting content…"):
                text, ftype = process_uploaded_file(uploaded)
                st.session_state.uploaded_content = clean_text(text)
                st.session_state.content_source   = uploaded.name
            st.success(f"✅ Loaded ({count_words(st.session_state.uploaded_content)} words)")

    elif input_mode == "📝 Paste Text":
        pasted = st.text_area("Paste your notes here:", height=150, placeholder="Paste lecture notes, article text…")
        if st.button("📥 Load Content") and pasted.strip():
            st.session_state.uploaded_content = clean_text(pasted)
            st.session_state.content_source   = "Pasted Text"
            st.success("✅ Content loaded!")

    else:  # sample topics
        sample_topic = st.selectbox("Pick a sample topic:", list(SAMPLE_CONTENTS.keys()))
        if st.button("📚 Load Sample"):
            st.session_state.uploaded_content = clean_text(SAMPLE_CONTENTS[sample_topic])
            st.session_state.content_source   = sample_topic
            st.session_state.current_subject  = sample_topic
            st.success(f"✅ Loaded: {sample_topic}")

    # ── Subject & days ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    st.session_state.current_subject = st.text_input(
        "Subject / Course:",
        value=st.session_state.current_subject,
        placeholder="e.g. Machine Learning",
    )
    study_days   = st.slider("Study plan days:", 3, 30, 7)
    hours_p_day  = st.slider("Hours per day:",   0.5, 8.0, 2.0, 0.5)

    # ── Quick stats ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📊 Quick Stats")
    total_min = st.session_state.total_study_time
    st.markdown(f"⏱️ **Total Study:** {total_min // 60}h {total_min % 60}m")
    st.markdown(f"🔥 **Streak:** {st.session_state.streak_days} day(s)")
    st.markdown(f"📝 **Quizzes taken:** {len(st.session_state.quiz_history)}")

    if st.session_state.uploaded_content:
        wc  = count_words(st.session_state.uploaded_content)
        rt  = estimate_reading_time(st.session_state.uploaded_content)
        src = st.session_state.content_source
        st.markdown(f"📄 **Source:** {src}")
        st.markdown(f"📏 **{wc} words** (~{rt} min read)")

    st.markdown("---")
    if st.button("🗑️ Clear All Data"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# HEADER BANNER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="background:linear-gradient(135deg,#1E3A5F,#2E86AB);border-radius:16px;
            padding:28px 32px;margin-bottom:24px;color:white;">
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
            <h1 style="margin:0;font-size:30px;">🧠 Smart Study Generator</h1>
            <p style="margin:6px 0 0;opacity:0.85;font-size:15px;">
                Your AI-powered adaptive study companion — IBM Granite + watsonx.ai
            </p>
        </div>
        <div style="text-align:right;opacity:0.85;font-size:13px;">
            <div>🤖 IBM Granite AI</div>
            <div>☁️ IBM Cloud watsonx</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Predictive alerts ─────────────────────────────────────────────────────────
alerts = generate_alerts(st)
if alerts:
    for alert in alerts[:3]:
        alert_box(alert["message"], "warning" if alert["priority"] == "high" else "info", alert["icon"])

# ══════════════════════════════════════════════════════════════════════════════
# MAIN TABS
# ══════════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "📊 Dashboard",
    "📄 Summarize",
    "🃏 Flashcards",
    "❓ Quiz",
    "📅 Study Plan",
    "🗺️ Concept Map",
    "💬 AI Tutor",
    "🔮 Exam Predictor",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    section_header("Learning Dashboard", "Real-time overview of your study progress", "📊")

    # Top metrics
    summary = get_performance_summary(st)
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Avg. Quiz Score", f"{summary['avg_score']}%", "", "🎯")
    with c2: metric_card("Quizzes Taken",   str(summary["total_quizzes"]), "", "📝")
    with c3: metric_card("Study Streak",    f"{st.session_state.streak_days} days", "", "🔥")
    with c4:
        hrs = st.session_state.total_study_time // 60
        mn  = st.session_state.total_study_time % 60
        metric_card("Total Study Time", f"{hrs}h {mn}m", "", "⏱️")

    st.markdown("---")

    col_left, col_right = st.columns([3, 2])

    with col_left:
        # Weekly activity chart
        weekly = get_weekly_study_data(st)
        labels_short = [d[-5:] for d in weekly["dates"]]  # MM-DD
        fig_weekly = go.Figure(go.Bar(
            x=labels_short,
            y=weekly["minutes"],
            marker_color=COLORS["secondary"],
            text=weekly["minutes"],
            textposition="outside",
        ))
        fig_weekly.update_layout(
            title="📅 Weekly Study Activity (minutes)",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=300,
            margin=dict(t=40, b=20, l=20, r=20),
            yaxis_title="Minutes",
        )
        st.plotly_chart(fig_weekly, use_container_width=True)

    with col_right:
        # Topic performance radar
        tp = get_topic_performance(st)
        if tp["topics"]:
            fig_radar = go.Figure(go.Scatterpolar(
                r=tp["scores"] + [tp["scores"][0]],
                theta=tp["topics"] + [tp["topics"][0]],
                fill="toself",
                fillcolor=f"rgba(46,134,171,0.2)",
                line_color=COLORS["secondary"],
            ))
            fig_radar.update_layout(
                title="🎯 Topic Performance",
                polar=dict(radialaxis=dict(range=[0, 100])),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=300,
                margin=dict(t=40, b=20, l=20, r=20),
            )
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("📊 Complete quizzes to see your topic performance radar.")

    # Quiz history table
    if st.session_state.quiz_history:
        st.markdown("#### 📋 Recent Quiz Results")
        df = pd.DataFrame(st.session_state.quiz_history[-10:])
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(
            df[["timestamp", "topic", "score", "total", "pct"]].rename(columns={
                "timestamp": "Date", "topic": "Topic",
                "score": "Score", "total": "Total", "pct": "Percentage (%)"
            }),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("📊 No quiz history yet. Take a quiz to track your progress!")

    # Weak / strong areas
    if st.session_state.weak_areas or st.session_state.strong_areas:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### ⚠️ Areas to Improve")
            for area in st.session_state.weak_areas[:5]:
                progress_bar(area, 40, colour=COLORS["danger"])
        with c2:
            st.markdown("#### ✅ Strong Areas")
            for area in st.session_state.strong_areas[:5]:
                progress_bar(area, 80, colour=COLORS["success"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SUMMARIZE
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    section_header("Smart Summarizer", "AI-generated summaries from your study material", "📄")

    if not st.session_state.uploaded_content:
        alert_box("Please load content using the sidebar first.", "info", "ℹ️")
    else:
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            detail_level = st.select_slider(
                "Summary depth:",
                options=["brief", "medium", "detailed"],
                value="medium",
            )
        with c2:
            st.metric("Words in content", count_words(st.session_state.uploaded_content))
        with c3:
            st.metric("Est. reading time", f"{estimate_reading_time(st.session_state.uploaded_content)} min")

        if st.button("🚀 Generate Summary", type="primary", use_container_width=True):
            with st.spinner("IBM Granite is summarising your content…"):
                summary_text = ai.summarize_content(st.session_state.uploaded_content, detail_level)
                st.session_state.summary = summary_text
                topics = ai.extract_key_topics(st.session_state.uploaded_content)
                st.session_state.extracted_topics = topics
                record_study_session(st, 5, topics[:3])

        if st.session_state.summary:
            st.markdown("#### 📝 Summary")
            st.markdown(f"""
            <div style="background:white;border-radius:12px;padding:24px;border-left:4px solid {COLORS['secondary']};
                        box-shadow:0 2px 8px rgba(0,0,0,0.08);line-height:1.8;font-size:15px;color:{COLORS['primary']};">
                {st.session_state.summary}
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.extracted_topics:
                st.markdown("#### 🏷️ Key Topics Identified")
                cols = st.columns(min(len(st.session_state.extracted_topics), 5))
                for i, topic in enumerate(st.session_state.extracted_topics):
                    with cols[i % len(cols)]:
                        st.markdown(f"""
                        <div style="background:{COLORS['secondary']};color:white;border-radius:20px;
                                    padding:6px 12px;text-align:center;font-size:13px;margin:4px 0;">
                            {topic}
                        </div>
                        """, unsafe_allow_html=True)

            # Mnemonics
            if st.button("💡 Generate Memory Tricks", use_container_width=True):
                with st.spinner("Creating mnemonics…"):
                    mnemonics = ai.generate_mnemonics(st.session_state.extracted_topics[:5])
                    st.session_state.mnemonics = mnemonics

            if st.session_state.mnemonics:
                st.markdown("#### 💡 Memory Tricks (Mnemonics)")
                for m in st.session_state.mnemonics:
                    with st.expander(f"📌 {m.get('topic', 'Topic')}"):
                        st.markdown(f"**Mnemonic:** {m.get('mnemonic', '')}")
                        st.markdown(f"**Explanation:** {m.get('explanation', '')}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — FLASHCARDS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    section_header("Flashcard Deck", "AI-generated flip cards for active recall", "🃏")

    if not st.session_state.uploaded_content:
        alert_box("Please load content using the sidebar first.", "info", "ℹ️")
    else:
        c1, c2 = st.columns([1, 1])
        with c1:
            num_cards = st.slider("Number of flashcards:", 5, 20, 10)
        with c2:
            diff_filter = st.multiselect("Filter by difficulty:", ["easy", "medium", "hard"],
                                         default=["easy", "medium", "hard"])

        if st.button("🃏 Generate Flashcards", type="primary", use_container_width=True):
            with st.spinner("IBM Granite is creating flashcards…"):
                cards = ai.generate_flashcards(st.session_state.uploaded_content, num_cards)
                st.session_state.flashcards        = cards
                st.session_state.current_flashcard = 0
                record_study_session(st, 10, ["Flashcard Review"])

        cards = st.session_state.flashcards
        if cards:
            # Filter
            filtered = [c for c in cards if c.get("difficulty", "medium").lower() in diff_filter] or cards
            idx = st.session_state.current_flashcard % len(filtered)

            # Flip state per card
            flip_key = f"flip_{idx}"
            if flip_key not in st.session_state:
                st.session_state[flip_key] = False

            # Display
            card = filtered[idx]
            flashcard_display(
                card.get("question", ""), card.get("answer", ""),
                card.get("difficulty", "medium"),
                st.session_state[flip_key], idx, len(filtered),
            )

            # Controls
            b1, b2, b3, b4 = st.columns(4)
            with b1:
                if st.button("⬅️ Previous"):
                    st.session_state.current_flashcard = (idx - 1) % len(filtered)
                    for k in [f"flip_{i}" for i in range(len(filtered))]:
                        st.session_state[k] = False
                    st.rerun()
            with b2:
                if st.button("🔄 Flip Card"):
                    st.session_state[flip_key] = not st.session_state[flip_key]
                    st.rerun()
            with b3:
                if st.button("➡️ Next"):
                    st.session_state.current_flashcard = (idx + 1) % len(filtered)
                    for k in [f"flip_{i}" for i in range(len(filtered))]:
                        st.session_state[k] = False
                    st.rerun()
            with b4:
                if st.button("🔀 Shuffle"):
                    import random
                    random.shuffle(st.session_state.flashcards)
                    st.session_state.current_flashcard = 0
                    st.rerun()

            # All cards list
            with st.expander("📋 View All Cards"):
                for i, c in enumerate(filtered):
                    st.markdown(f"**{i+1}. Q:** {c.get('question','')}")
                    st.markdown(f"   **A:** {c.get('answer','')}")
                    st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — QUIZ
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    section_header("Practice Quiz", "Test your knowledge with AI-generated questions", "❓")

    if not st.session_state.uploaded_content:
        alert_box("Please load content using the sidebar first.", "info", "ℹ️")
    else:
        c1, c2 = st.columns(2)
        with c1: num_q = st.slider("Number of questions:", 3, 15, 5)
        with c2: difficulty = st.selectbox("Difficulty:", ["easy", "medium", "hard"], index=1)

        if st.button("🎲 Generate Quiz", type="primary", use_container_width=True):
            with st.spinner("IBM Granite is crafting quiz questions…"):
                questions = ai.generate_quiz(st.session_state.uploaded_content, num_q, difficulty)
                st.session_state.quiz_questions = questions
                st.session_state.quiz_submitted  = False
                st.session_state.quiz_answers    = {}

        if st.session_state.quiz_questions:
            st.markdown(f"### 📋 Quiz — {len(st.session_state.quiz_questions)} questions")

            answers: dict[int, str] = {}
            for i, q in enumerate(st.session_state.quiz_questions):
                choice = quiz_question_card(q, i)
                if choice:
                    answers[i] = choice[0]  # just the letter A/B/C/D

            if not st.session_state.quiz_submitted:
                if st.button("✅ Submit Quiz", type="primary", use_container_width=True):
                    st.session_state.quiz_answers    = answers
                    st.session_state.quiz_submitted  = True
                    # Score
                    score = sum(
                        1 for i, q in enumerate(st.session_state.quiz_questions)
                        if answers.get(i, "").upper() == q.get("correct", "").upper()
                    )
                    topic = st.session_state.current_subject or "General"
                    record_quiz_result(st, topic, score, len(st.session_state.quiz_questions))
                    st.rerun()

            if st.session_state.quiz_submitted:
                answers  = st.session_state.quiz_answers
                score    = sum(
                    1 for i, q in enumerate(st.session_state.quiz_questions)
                    if answers.get(i, "").upper() == q.get("correct", "").upper()
                )
                total    = len(st.session_state.quiz_questions)
                pct      = round(score / total * 100) if total else 0
                colour   = COLORS["success"] if pct >= 70 else (COLORS["warning"] if pct >= 50 else COLORS["danger"])

                st.markdown(f"""
                <div style="background:{colour};color:white;border-radius:12px;padding:20px;
                            text-align:center;margin:16px 0;">
                    <h2 style="margin:0;">Score: {score}/{total} ({pct}%)</h2>
                    <p style="margin:4px 0;">{"Excellent! 🎉" if pct>=80 else "Good job! 👍" if pct>=60 else "Keep practising! 💪"}</p>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("#### 📊 Detailed Results")
                for i, q in enumerate(st.session_state.quiz_questions):
                    correct  = q.get("correct", "").upper()
                    selected = answers.get(i, "").upper()
                    is_right = selected == correct
                    icon     = "✅" if is_right else "❌"
                    with st.expander(f"{icon} Q{i+1}: {q.get('question','')[:80]}…"):
                        st.write(f"**Your answer:** {selected}")
                        st.write(f"**Correct answer:** {correct}")
                        st.write(f"**Explanation:** {q.get('explanation','')}")

                if st.button("🔄 Retake Quiz", use_container_width=True):
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_answers   = {}
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — STUDY PLAN
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    section_header("Personalized Study Plan", "AI-crafted schedule tailored to your topics", "📅")

    if not st.session_state.uploaded_content and not st.session_state.extracted_topics:
        alert_box("Load content and generate a summary first to extract topics automatically, or enter topics manually.", "info", "ℹ️")

    c1, c2 = st.columns([2, 1])
    with c1:
        manual_topics = st.text_area(
            "Topics to cover (one per line):",
            value="\n".join(st.session_state.extracted_topics) if st.session_state.extracted_topics else "",
            height=140,
            placeholder="Topic 1\nTopic 2\nTopic 3",
        )
    with c2:
        st.metric("Study Days", study_days)
        st.metric("Hours/Day",  hours_p_day)

    if st.button("📅 Generate Study Plan", type="primary", use_container_width=True):
        topics_list = [t.strip() for t in manual_topics.split("\n") if t.strip()]
        if not topics_list and st.session_state.uploaded_content:
            with st.spinner("Extracting topics…"):
                topics_list = ai.extract_key_topics(st.session_state.uploaded_content)
        if topics_list:
            with st.spinner("IBM Granite is building your study plan…"):
                plan = ai.generate_study_plan(topics_list, study_days, hours_p_day)
                st.session_state.study_plan = plan
                record_study_session(st, 3, topics_list[:3])
        else:
            st.warning("Please add at least one topic.")

    plan = st.session_state.study_plan
    if plan and plan.get("plan"):
        days_data = plan["plan"]

        # Gantt-style timeline
        st.markdown("#### 🗓️ Study Timeline")
        fig_gantt = go.Figure()
        today = datetime.date.today()
        for day in days_data:
            d_offset = today + datetime.timedelta(days=day["day"] - 1)
            topics_str = ", ".join(day.get("topics", []))
            fig_gantt.add_trace(go.Bar(
                name=f"Day {day['day']}",
                x=[day.get("duration_hours", 2)],
                y=[f"Day {day['day']}: {topics_str[:40]}"],
                orientation="h",
                marker_color=COLORS["secondary"],
                text=f"{day.get('duration_hours', 2)}h",
                textposition="inside",
            ))
        fig_gantt.update_layout(
            title="Study Plan Overview",
            xaxis_title="Hours",
            barmode="stack",
            height=max(300, len(days_data) * 40),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            margin=dict(t=40, b=20, l=180, r=20),
        )
        st.plotly_chart(fig_gantt, use_container_width=True)

        # Day cards
        st.markdown("#### 📋 Daily Breakdown")
        cols = st.columns(min(len(days_data), 3))
        for i, day in enumerate(days_data):
            with cols[i % len(cols)]:
                tasks_html = "".join(f"<li>{t}</li>" for t in day.get("tasks", []))
                topics_html = ", ".join(day.get("topics", []))
                st.markdown(f"""
                <div style="background:white;border-radius:10px;padding:16px;margin:6px 0;
                            border-top:3px solid {COLORS['secondary']};box-shadow:0 2px 6px rgba(0,0,0,0.06);">
                    <h4 style="color:{COLORS['primary']};margin:0 0 6px;">Day {day['day']}</h4>
                    <p style="color:{COLORS['secondary']};font-size:12px;margin:0 0 6px;">📚 {topics_html}</p>
                    <ul style="font-size:13px;color:{COLORS['primary']};padding-left:16px;margin:0;">{tasks_html}</ul>
                    <p style="color:{COLORS['accent']};font-size:12px;margin:6px 0 0;">⏱️ {day.get('duration_hours',2)}h</p>
                </div>
                """, unsafe_allow_html=True)

        # Tips
        if plan.get("tips"):
            st.markdown("#### 💡 Study Tips")
            for tip in plan["tips"]:
                st.markdown(f"✅ {tip}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — CONCEPT MAP
# ══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    section_header("Concept Map", "Visual knowledge graph of your study material", "🗺️")

    if not st.session_state.uploaded_content:
        alert_box("Please load content using the sidebar first.", "info", "ℹ️")
    else:
        if st.button("🗺️ Generate Concept Map", type="primary", use_container_width=True):
            with st.spinner("IBM Granite is building your concept map…"):
                cmap = ai.generate_concept_map(st.session_state.uploaded_content)
                st.session_state.concept_map = cmap
                record_study_session(st, 5, ["Concept Mapping"])

        if st.session_state.concept_map:
            render_concept_map(st.session_state.concept_map)

            with st.expander("📄 Raw Concept Map Data"):
                st.json(st.session_state.concept_map)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — AI TUTOR (Chat)
# ══════════════════════════════════════════════════════════════════════════════
with tabs[6]:
    section_header("AI Tutor", "Ask anything — get instant, context-aware answers", "💬")

    # Chat history display
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            chat_message(msg["role"], msg["content"])

    # Input
    col_input, col_send = st.columns([5, 1])
    with col_input:
        user_q = st.text_input(
            "Ask your question:",
            key="chat_input",
            placeholder="e.g. Explain gradient descent in simple terms…",
            label_visibility="collapsed",
        )
    with col_send:
        send = st.button("Send 📨", use_container_width=True)

    if send and user_q.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_q})
        with st.spinner("IBM Granite is thinking…"):
            ctx = st.session_state.uploaded_content[:2000] if st.session_state.uploaded_content else ""
            answer = ai.answer_question(user_q, ctx)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        record_study_session(st, 2, ["AI Tutoring"])
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

    # Quick prompts
    st.markdown("#### 💡 Quick Prompts")
    qp_cols = st.columns(3)
    quick_prompts = [
        "Summarise the most important concepts",
        "What are the key formulas I need to know?",
        "Give me 3 exam tips for this subject",
        "Explain the hardest topic in simple terms",
        "What should I study first?",
        "Create a 5-question self-test",
    ]
    for i, qp in enumerate(quick_prompts):
        with qp_cols[i % 3]:
            if st.button(qp, key=f"qp_{i}", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": qp})
                with st.spinner("Thinking…"):
                    ctx = st.session_state.uploaded_content[:2000] if st.session_state.uploaded_content else ""
                    ans = ai.answer_question(qp, ctx)
                st.session_state.chat_history.append({"role": "assistant", "content": ans})
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 8 — EXAM PREDICTOR
# ══════════════════════════════════════════════════════════════════════════════
with tabs[7]:
    section_header("Exam Topic Predictor", "AI-predicted high-probability exam topics", "🔮")

    if not st.session_state.uploaded_content:
        alert_box("Please load content using the sidebar first.", "info", "ℹ️")
    else:
        subject_hint = st.text_input(
            "Exam subject (optional hint):",
            value=st.session_state.current_subject,
            placeholder="e.g. Machine Learning Midterm",
        )

        if st.button("🔮 Predict Exam Topics", type="primary", use_container_width=True):
            with st.spinner("IBM Granite is analysing exam patterns…"):
                predictions = ai.predict_exam_topics(st.session_state.uploaded_content, subject_hint)
                st.session_state.exam_predictions = predictions

            # Weak area analysis if quiz history exists
            if st.session_state.quiz_history:
                with st.spinner("Analysing weak areas…"):
                    analysis = ai.analyze_weak_areas(st.session_state.quiz_history)
                    st.session_state.weak_areas   = analysis.get("weak_areas", [])
                    st.session_state.strong_areas = analysis.get("strong_areas", [])

        if st.session_state.exam_predictions:
            st.markdown("### 🎯 Predicted High-Priority Topics")

            # Probability chart
            preds = st.session_state.exam_predictions
            if preds:
                df_pred = pd.DataFrame(preds)
                if "probability" in df_pred.columns and "topic" in df_pred.columns:
                    df_pred = df_pred.sort_values("probability", ascending=True)
                    colours = [
                        COLORS["danger"]  if p.get("priority") == "high"   else
                        COLORS["warning"] if p.get("priority") == "medium" else
                        COLORS["success"]
                        for _, p in df_pred.iterrows()
                    ]
                    fig_pred = go.Figure(go.Bar(
                        x=df_pred["probability"],
                        y=df_pred["topic"],
                        orientation="h",
                        marker_color=colours,
                        text=[f"{v}%" for v in df_pred["probability"]],
                        textposition="outside",
                    ))
                    fig_pred.update_layout(
                        title="Exam Topic Probability",
                        xaxis_title="Probability (%)",
                        xaxis=dict(range=[0, 110]),
                        height=max(300, len(df_pred) * 45),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        margin=dict(t=40, b=20, l=20, r=20),
                    )
                    st.plotly_chart(fig_pred, use_container_width=True)

            # Topic cards
            for pred in preds:
                priority = pred.get("priority", "medium")
                icon     = "🔴" if priority == "high" else ("🟡" if priority == "medium" else "🟢")
                border   = COLORS["danger"] if priority == "high" else (COLORS["warning"] if priority == "medium" else COLORS["success"])
                st.markdown(f"""
                <div style="background:white;border-radius:10px;padding:16px;margin:8px 0;
                            border-left:4px solid {border};box-shadow:0 2px 6px rgba(0,0,0,0.06);">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <h4 style="color:{COLORS['primary']};margin:0;">{icon} {pred.get('topic','')}</h4>
                        <span style="background:{border};color:white;padding:3px 10px;
                                     border-radius:20px;font-size:12px;">{pred.get('probability',0)}%</span>
                    </div>
                    <p style="color:{COLORS['secondary']};font-size:14px;margin:6px 0 0;">{pred.get('reason','')}</p>
                </div>
                """, unsafe_allow_html=True)

        # Weak area deep-dive
        if st.session_state.weak_areas:
            st.markdown("### ⚠️ Focus Areas Based on Quiz Performance")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**❗ Needs Improvement**")
                for a in st.session_state.weak_areas:
                    alert_box(a, "warning", "⚠️")
            with c2:
                st.markdown("**✅ Strong Areas**")
                for a in st.session_state.strong_areas:
                    alert_box(a, "success", "✅")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:24px 0 8px;border-top:1px solid #E9ECEF;margin-top:32px;
            color:#57606A;font-size:13px;">
    🧠 <strong>Smart Study Generator</strong> &nbsp;|&nbsp;
    Powered by <strong>IBM Granite</strong> + <strong>IBM watsonx.ai</strong> &nbsp;|&nbsp;
    Built with <strong>Streamlit</strong>
</div>
""", unsafe_allow_html=True)
