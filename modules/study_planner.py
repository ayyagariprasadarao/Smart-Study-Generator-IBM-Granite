"""
Study Plan & Agentic Layer Module
Manages personalized study plans, progress tracking, and predictive alerts.
"""

import json
import datetime
from typing import Any


# ── Session-state helpers ──────────────────────────────────────────────────────

def init_session(st) -> None:
    """Initialise all session-state keys required by the app."""
    defaults: dict[str, Any] = {
        # Content
        "uploaded_content":   "",
        "content_source":     "",
        "current_subject":    "",
        "extracted_topics":   [],
        # Generated artefacts
        "flashcards":         [],
        "quiz_questions":     [],
        "study_plan":         {},
        "summary":            "",
        "concept_map":        {},
        "exam_predictions":   [],
        "mnemonics":          [],
        # Progress & history
        "quiz_history":       [],    # [{topic, score, total, timestamp}, ...]
        "study_sessions":     [],    # [{date, duration_min, topics, …}, ...]
        "performance_data":   {},    # {topic: [scores]}
        "weak_areas":         [],
        "strong_areas":       [],
        # UI state
        "current_flashcard":  0,
        "quiz_submitted":     False,
        "quiz_answers":       {},
        "total_study_time":   0,     # minutes
        "streak_days":        0,
        "last_study_date":    None,
        # Chat
        "chat_history":       [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ── Progress tracking ──────────────────────────────────────────────────────────

def record_quiz_result(st, topic: str, score: int, total: int) -> None:
    entry = {
        "topic":     topic,
        "score":     score,
        "total":     total,
        "pct":       round(score / total * 100, 1) if total else 0,
        "timestamp": datetime.datetime.now().isoformat(),
    }
    st.session_state.quiz_history.append(entry)

    # update per-topic performance
    perf = st.session_state.performance_data
    perf.setdefault(topic, []).append(entry["pct"])

    # update study time
    st.session_state.total_study_time = st.session_state.get("total_study_time", 0) + 5  # ~5 min per quiz

    _update_streak(st)


def record_study_session(st, duration_min: int, topics: list[str]) -> None:
    st.session_state.study_sessions.append({
        "date":         datetime.date.today().isoformat(),
        "duration_min": duration_min,
        "topics":       topics,
        "timestamp":    datetime.datetime.now().isoformat(),
    })
    st.session_state.total_study_time = st.session_state.get("total_study_time", 0) + duration_min
    _update_streak(st)


def _update_streak(st) -> None:
    today = datetime.date.today()
    last  = st.session_state.last_study_date
    if last is None:
        st.session_state.streak_days    = 1
        st.session_state.last_study_date = today
    elif (today - last).days == 1:
        st.session_state.streak_days   += 1
        st.session_state.last_study_date = today
    elif (today - last).days > 1:
        st.session_state.streak_days    = 1
        st.session_state.last_study_date = today


# ── Analytics ─────────────────────────────────────────────────────────────────

def get_performance_summary(st) -> dict:
    history = st.session_state.quiz_history
    if not history:
        return {"avg_score": 0, "total_quizzes": 0, "best_topic": None,
                "worst_topic": None, "trend": "no data"}

    scores = [e["pct"] for e in history]
    avg    = round(sum(scores) / len(scores), 1)

    perf   = st.session_state.performance_data
    best   = max(perf, key=lambda t: sum(perf[t]) / len(perf[t])) if perf else None
    worst  = min(perf, key=lambda t: sum(perf[t]) / len(perf[t])) if perf else None

    # trend: compare last 3 vs previous 3
    trend = "stable"
    if len(scores) >= 6:
        recent  = sum(scores[-3:]) / 3
        earlier = sum(scores[-6:-3]) / 3
        if recent > earlier + 5:
            trend = "improving"
        elif recent < earlier - 5:
            trend = "declining"

    return {
        "avg_score":    avg,
        "total_quizzes": len(history),
        "best_topic":   best,
        "worst_topic":  worst,
        "trend":        trend,
    }


def get_weekly_study_data(st) -> dict:
    """Return study minutes per day for the last 7 days."""
    today  = datetime.date.today()
    labels = [(today - datetime.timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    by_day: dict[str, int] = {d: 0 for d in labels}

    for s in st.session_state.study_sessions:
        d = s.get("date", "")
        if d in by_day:
            by_day[d] += s.get("duration_min", 0)

    return {"dates": labels, "minutes": [by_day[d] for d in labels]}


def get_topic_performance(st) -> dict:
    """Return avg score per topic for radar / bar charts."""
    perf = st.session_state.performance_data
    if not perf:
        return {"topics": [], "scores": []}
    topics = list(perf.keys())
    scores = [round(sum(perf[t]) / len(perf[t]), 1) for t in topics]
    return {"topics": topics, "scores": scores}


# ── Predictive alerts ──────────────────────────────────────────────────────────

def generate_alerts(st) -> list[dict]:
    alerts = []
    summary = get_performance_summary(st)

    if summary["worst_topic"]:
        alerts.append({
            "type":    "warning",
            "icon":    "⚠️",
            "message": f"Focus on **{summary['worst_topic']}** — your lowest scoring area.",
            "priority": "high",
        })

    if st.session_state.streak_days >= 3:
        alerts.append({
            "type":    "success",
            "icon":    "🔥",
            "message": f"Great streak! You've studied {st.session_state.streak_days} days in a row.",
            "priority": "info",
        })

    if st.session_state.total_study_time > 60:
        alerts.append({
            "type":    "info",
            "icon":    "📚",
            "message": f"You've logged {st.session_state.total_study_time} minutes of study time. Keep it up!",
            "priority": "info",
        })

    for pred in st.session_state.exam_predictions[:3]:
        if pred.get("priority") == "high":
            alerts.append({
                "type":    "warning",
                "icon":    "🎯",
                "message": f"Exam alert: **{pred.get('topic', '')}** — {pred.get('reason', 'frequently asked')}",
                "priority": "high",
            })

    return alerts
