"""
UI Components Module
Reusable Streamlit UI helpers and styled components.
"""

import streamlit as st
import json


# ── Colour palette (mirrors app theme) ────────────────────────────────────────
COLORS = {
    "primary":   "#1E3A5F",
    "secondary": "#2E86AB",
    "accent":    "#F18F01",
    "success":   "#2ECC71",
    "warning":   "#F39C12",
    "danger":    "#E74C3C",
    "light":     "#F8F9FA",
    "card_bg":   "#FFFFFF",
}


def metric_card(title: str, value: str, delta: str = "", icon: str = "📊") -> None:
    """Render a styled metric card."""
    delta_html = f'<span style="color:#2ECC71;font-size:12px;">▲ {delta}</span>' if delta else ""
    st.markdown(f"""
    <div style="background:{COLORS['card_bg']};border-radius:12px;padding:20px;
                border-left:4px solid {COLORS['secondary']};margin-bottom:10px;
                box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <p style="color:{COLORS['secondary']};font-size:13px;margin:0;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">{title}</p>
                <h2 style="color:{COLORS['primary']};margin:4px 0;font-size:28px;">{value}</h2>
                {delta_html}
            </div>
            <span style="font-size:32px;">{icon}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def alert_box(message: str, alert_type: str = "info", icon: str = "ℹ️") -> None:
    """Render a styled alert banner."""
    colour_map = {
        "info":    ("#D1ECF1", "#0C5460", "#BEE5EB"),
        "success": ("#D4EDDA", "#155724", "#C3E6CB"),
        "warning": ("#FFF3CD", "#856404", "#FFEEBA"),
        "danger":  ("#F8D7DA", "#721C24", "#F5C6CB"),
    }
    bg, text, border = colour_map.get(alert_type, colour_map["info"])
    st.markdown(f"""
    <div style="background:{bg};border:1px solid {border};border-radius:8px;
                padding:12px 16px;margin:8px 0;color:{text};">
        {icon} {message}
    </div>
    """, unsafe_allow_html=True)


def section_header(title: str, subtitle: str = "", icon: str = "") -> None:
    icon_html = f'<span style="font-size:28px;margin-right:10px;">{icon}</span>' if icon else ""
    sub_html  = f'<p style="color:{COLORS["secondary"]};margin:4px 0 16px;font-size:15px;">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div style="border-bottom:3px solid {COLORS['secondary']};padding-bottom:12px;margin-bottom:20px;">
        <h2 style="color:{COLORS['primary']};margin:0;display:flex;align-items:center;">
            {icon_html}{title}
        </h2>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def progress_bar(label: str, value: float, max_val: float = 100, colour: str = "") -> None:
    """Render a labelled progress bar."""
    pct    = min(100, round(value / max_val * 100)) if max_val else 0
    colour = colour or COLORS["secondary"]
    st.markdown(f"""
    <div style="margin:8px 0;">
        <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
            <span style="color:{COLORS['primary']};font-size:13px;font-weight:500;">{label}</span>
            <span style="color:{COLORS['secondary']};font-size:13px;">{pct}%</span>
        </div>
        <div style="background:#E9ECEF;border-radius:10px;height:10px;">
            <div style="background:{colour};width:{pct}%;height:10px;border-radius:10px;
                        transition:width 0.4s ease;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def flashcard_display(question: str, answer: str, difficulty: str, flipped: bool, index: int, total: int) -> None:
    """Render a single flip-card (Streamlit re-renders handle the flip state)."""
    diff_colours = {"easy": COLORS["success"], "medium": COLORS["warning"], "hard": COLORS["danger"]}
    diff_colour  = diff_colours.get(difficulty.lower(), COLORS["secondary"])

    face    = answer if flipped else question
    label   = "💡 Answer" if flipped else "❓ Question"
    bg      = "#EBF5FB" if flipped else "#FFFFFF"
    border  = COLORS["success"] if flipped else COLORS["secondary"]

    st.markdown(f"""
    <div style="background:{bg};border:2px solid {border};border-radius:16px;
                padding:30px;text-align:center;min-height:160px;margin:10px 0;
                box-shadow:0 4px 12px rgba(0,0,0,0.1);">
        <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
            <span style="background:{diff_colour};color:white;padding:3px 10px;
                         border-radius:20px;font-size:12px;">{difficulty.upper()}</span>
            <span style="color:{COLORS['secondary']};font-size:13px;">{index + 1} / {total}</span>
        </div>
        <p style="color:{COLORS['secondary']};font-size:12px;text-transform:uppercase;
                  letter-spacing:1px;margin-bottom:8px;">{label}</p>
        <p style="color:{COLORS['primary']};font-size:17px;font-weight:500;line-height:1.6;">{face}</p>
    </div>
    """, unsafe_allow_html=True)


def quiz_question_card(q: dict, idx: int) -> str | None:
    """Render a single quiz question and return the selected answer key or None."""
    st.markdown(f"""
    <div style="background:#FFFFFF;border-radius:12px;padding:20px;margin:12px 0;
                border-left:4px solid {COLORS['accent']};box-shadow:0 2px 8px rgba(0,0,0,0.06);">
        <p style="color:{COLORS['primary']};font-size:16px;font-weight:600;margin:0;">
            Q{idx + 1}. {q.get('question', '')}
        </p>
    </div>
    """, unsafe_allow_html=True)

    options = q.get("options", [])
    if options:
        choice = st.radio("Select your answer:", options, key=f"quiz_q_{idx}", label_visibility="collapsed")
        return choice[0] if choice else None  # return just the letter e.g. "A"
    return None


def render_concept_map(concept_map: dict) -> None:
    """Render a simple text-based concept map (no external libs required)."""
    if not concept_map or not concept_map.get("nodes"):
        st.info("No concept map available yet.")
        return

    central = concept_map.get("central_concept", "Main Concept")
    nodes   = concept_map.get("nodes", [])
    edges   = concept_map.get("edges", [])

    # Build adjacency
    adj: dict[str, list[str]] = {}
    id_to_label = {n["id"]: n["label"] for n in nodes}
    for e in edges:
        src = id_to_label.get(e.get("from", ""), e.get("from", ""))
        tgt = id_to_label.get(e.get("to", ""),   e.get("to", ""))
        adj.setdefault(src, []).append(tgt)

    main_nodes = [n for n in nodes if n.get("type") == "main"]
    sub_nodes  = [n for n in nodes if n.get("type") == "sub"]
    detail_nodes = [n for n in nodes if n.get("type") == "detail"]

    st.markdown(f"""
    <div style="background:#F0F7FF;border-radius:12px;padding:20px;text-align:center;">
        <div style="background:{COLORS['primary']};color:white;border-radius:50px;
                    padding:12px 24px;display:inline-block;font-weight:700;font-size:16px;
                    margin-bottom:16px;">{central}</div>
    """, unsafe_allow_html=True)

    if main_nodes:
        cols = st.columns(min(len(main_nodes), 4))
        for i, node in enumerate(main_nodes):
            with cols[i % len(cols)]:
                st.markdown(f"""
                <div style="background:{COLORS['secondary']};color:white;border-radius:8px;
                            padding:10px;text-align:center;font-weight:600;font-size:14px;
                            margin:4px;">{node['label']}</div>
                """, unsafe_allow_html=True)

    if sub_nodes:
        st.markdown("**Related Concepts:**")
        cols = st.columns(min(len(sub_nodes), 5))
        for i, node in enumerate(sub_nodes):
            with cols[i % len(cols)]:
                st.markdown(f"""
                <div style="background:#EBF5FB;border:1px solid {COLORS['secondary']};
                            color:{COLORS['primary']};border-radius:6px;padding:8px;
                            text-align:center;font-size:13px;margin:4px;">{node['label']}</div>
                """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def chat_message(role: str, content: str) -> None:
    """Render a single chat bubble."""
    is_user = role == "user"
    bg      = COLORS["primary"]  if is_user else "#F0F7FF"
    colour  = "white"            if is_user else COLORS["primary"]
    align   = "flex-end"         if is_user else "flex-start"
    avatar  = "👤"               if is_user else "🤖"
    radius  = "18px 18px 4px 18px" if is_user else "18px 18px 18px 4px"

    st.markdown(f"""
    <div style="display:flex;justify-content:{align};margin:8px 0;">
        <div style="max-width:75%;background:{bg};color:{colour};border-radius:{radius};
                    padding:12px 16px;box-shadow:0 2px 6px rgba(0,0,0,0.1);">
            <span style="font-size:16px;margin-right:8px;">{avatar}</span>
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)
