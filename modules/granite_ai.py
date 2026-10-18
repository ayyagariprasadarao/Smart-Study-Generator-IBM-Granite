"""
IBM Granite AI Integration Module
Handles all interactions with IBM watsonx.ai using Granite models
"""

import os
import json
import re
from typing import Optional

try:
    from ibm_watsonx_ai import APIClient, Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
    IBM_WATSONX_AVAILABLE = True
except ImportError:
    IBM_WATSONX_AVAILABLE = False

# ── Configuration ──────────────────────────────────────────────────────────────
IBM_API_KEY    = "Aq0CCkbQoJnb3BViW8BfPDoNoX63V-31X97vAvPbUjWx"
IBM_PROJECT_ID = "8a39dfde-3880-4b31-8270-248a9785f594"
IBM_URL        = "https://us-south.ml.cloud.ibm.com"
GRANITE_MODEL  = "ibm/granite-13b-instruct-v2"


class GraniteAI:
    """Wrapper around IBM Granite via watsonx.ai for all study-generation tasks."""

    def __init__(self):
        self.available = IBM_WATSONX_AVAILABLE
        self.model: Optional[object] = None
        if self.available:
            self._init_model()

    def _init_model(self):
        try:
            credentials = Credentials(url=IBM_URL, api_key=IBM_API_KEY)
            self.model = ModelInference(
                model_id=GRANITE_MODEL,
                credentials=credentials,
                project_id=IBM_PROJECT_ID,
                params={
                    GenParams.MAX_NEW_TOKENS: 1024,
                    GenParams.MIN_NEW_TOKENS: 50,
                    GenParams.TEMPERATURE:    0.7,
                    GenParams.TOP_P:          0.9,
                    GenParams.REPETITION_PENALTY: 1.1,
                },
            )
        except Exception as e:
            self.available = False
            print(f"[GraniteAI] init failed: {e}")

    def _generate(self, prompt: str, max_tokens: int = 1024) -> str:
        """Core generation call with graceful fallback."""
        if not self.available or self.model is None:
            return self._fallback_response(prompt)
        try:
            response = self.model.generate_text(prompt=prompt)
            return response.strip() if isinstance(response, str) else str(response)
        except Exception as e:
            print(f"[GraniteAI] generation error: {e}")
            return self._fallback_response(prompt)

    # ── Public API ─────────────────────────────────────────────────────────────

    def summarize_content(self, content: str, level: str = "medium") -> str:
        detail = {"brief": "2-3 sentences", "medium": "one paragraph", "detailed": "2-3 paragraphs"}[level]
        prompt = f"""You are an expert study assistant. Summarize the following educational content in {detail}.
Focus on key concepts, important definitions, and main ideas. Use clear, student-friendly language.

Content:
{content[:3000]}

Summary:"""
        return self._generate(prompt)

    def generate_flashcards(self, content: str, num_cards: int = 10) -> list[dict]:
        prompt = f"""You are an expert educator. Create exactly {num_cards} flashcard question-answer pairs from the content below.
Return ONLY a valid JSON array in this format (no extra text):
[{{"question": "...", "answer": "...", "difficulty": "easy|medium|hard"}}]

Content:
{content[:3000]}

JSON:"""
        raw = self._generate(prompt, max_tokens=1500)
        return self._parse_json_list(raw, default_key="question")

    def generate_quiz(self, content: str, num_questions: int = 5, difficulty: str = "medium") -> list[dict]:
        prompt = f"""You are an expert educator. Create exactly {num_questions} multiple-choice quiz questions at {difficulty} difficulty from the content below.
Return ONLY a valid JSON array (no extra text):
[{{"question":"...","options":["A) ...","B) ...","C) ...","D) ..."],"correct":"A","explanation":"..."}}]

Content:
{content[:3000]}

JSON:"""
        raw = self._generate(prompt, max_tokens=2000)
        return self._parse_json_list(raw, default_key="question")

    def generate_study_plan(self, topics: list[str], days: int = 7, hours_per_day: float = 2.0) -> dict:
        topics_str = "\n".join(f"- {t}" for t in topics)
        prompt = f"""You are an expert study planner. Create a {days}-day study plan for these topics,
with {hours_per_day} hours of study per day.
Return ONLY a valid JSON object (no extra text):
{{"plan":[{{"day":1,"date":"Day 1","topics":["..."],"tasks":["..."],"duration_hours":2.0}}],"tips":["..."]}}

Topics:
{topics_str}

JSON:"""
        raw = self._generate(prompt, max_tokens=2000)
        try:
            # extract first {...} block
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                return json.loads(m.group())
        except Exception:
            pass
        return self._default_study_plan(topics, days)

    def generate_concept_map(self, content: str) -> dict:
        prompt = f"""You are an expert educator. Extract key concepts and their relationships from the content below.
Return ONLY a valid JSON object (no extra text):
{{"central_concept":"...","nodes":[{{"id":"n1","label":"concept","type":"main|sub|detail"}}],"edges":[{{"from":"n1","to":"n2","label":"relates to"}}]}}

Content:
{content[:2000]}

JSON:"""
        raw = self._generate(prompt, max_tokens=1500)
        try:
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                return json.loads(m.group())
        except Exception:
            pass
        return {"central_concept": "Main Topic", "nodes": [], "edges": []}

    def extract_key_topics(self, content: str) -> list[str]:
        prompt = f"""Extract the 8-10 most important topics/concepts from the content below.
Return ONLY a JSON array of strings (no extra text): ["topic1","topic2",...]

Content:
{content[:2000]}

JSON:"""
        raw = self._generate(prompt, max_tokens=500)
        try:
            m = re.search(r'\[.*?\]', raw, re.DOTALL)
            if m:
                return json.loads(m.group())
        except Exception:
            pass
        return ["Key Concept 1", "Key Concept 2", "Key Concept 3"]

    def predict_exam_topics(self, content: str, subject: str = "") -> list[dict]:
        subject_hint = f" for {subject}" if subject else ""
        prompt = f"""You are an expert exam predictor{subject_hint}. Analyse the content and predict the most likely exam topics.
Return ONLY a valid JSON array (no extra text):
[{{"topic":"...","probability":85,"reason":"...","priority":"high|medium|low"}}]

Content:
{content[:2500]}

JSON:"""
        raw = self._generate(prompt, max_tokens=1000)
        return self._parse_json_list(raw, default_key="topic")

    def answer_question(self, question: str, context: str = "") -> str:
        ctx = f"\nContext:\n{context[:2000]}\n" if context else ""
        prompt = f"""You are a knowledgeable study assistant. Answer the student's question clearly and thoroughly.{ctx}
Question: {question}

Answer:"""
        return self._generate(prompt, max_tokens=800)

    def generate_mnemonics(self, topics: list[str]) -> list[dict]:
        topics_str = ", ".join(topics[:5])
        prompt = f"""Create memorable mnemonics or memory tricks for these topics: {topics_str}
Return ONLY a valid JSON array (no extra text):
[{{"topic":"...","mnemonic":"...","explanation":"..."}}]

JSON:"""
        raw = self._generate(prompt, max_tokens=800)
        return self._parse_json_list(raw, default_key="topic")

    def analyze_weak_areas(self, quiz_history: list[dict]) -> dict:
        history_str = json.dumps(quiz_history[-10:], indent=2) if quiz_history else "[]"
        prompt = f"""Analyse this student's quiz history and identify weak areas that need more study.
Return ONLY a valid JSON object (no extra text):
{{"weak_areas":["..."],"strong_areas":["..."],"recommendations":["..."],"focus_percentage":{{"topic":percentage}}}}

Quiz history:
{history_str}

JSON:"""
        raw = self._generate(prompt, max_tokens=800)
        try:
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                return json.loads(m.group())
        except Exception:
            pass
        return {"weak_areas": [], "strong_areas": [], "recommendations": [], "focus_percentage": {}}

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_json_list(raw: str, default_key: str = "item") -> list[dict]:
        """Extract the first JSON array from raw text."""
        try:
            m = re.search(r'\[.*\]', raw, re.DOTALL)
            if m:
                return json.loads(m.group())
        except Exception:
            pass
        return []

    @staticmethod
    def _fallback_response(prompt: str) -> str:
        if "summarize" in prompt.lower() or "summary" in prompt.lower():
            return ("This is a summary of the provided content. "
                    "The material covers important concepts that are essential for understanding the subject. "
                    "Key points include the main theories, definitions, and applications discussed.")
        if "flashcard" in prompt.lower():
            return json.dumps([
                {"question": "What is the main concept?", "answer": "The main concept involves the fundamental principles of the subject.", "difficulty": "medium"},
                {"question": "Define the key term.", "answer": "A key term refers to a specific concept within the field of study.", "difficulty": "easy"},
            ])
        if "quiz" in prompt.lower():
            return json.dumps([
                {"question": "Which of the following best describes the concept?",
                 "options": ["A) First option", "B) Second option", "C) Third option", "D) Fourth option"],
                 "correct": "A", "explanation": "The first option is correct because it accurately describes the concept."},
            ])
        return ("I'm here to help you study! Please ensure IBM watsonx.ai is properly configured "
                "to get AI-powered responses. You can still use all features in demo mode.")

    @staticmethod
    def _default_study_plan(topics: list[str], days: int) -> dict:
        per_day = max(1, len(topics) // days)
        plan = []
        for d in range(1, days + 1):
            start = (d - 1) * per_day
            day_topics = topics[start: start + per_day] or ["Review all topics"]
            plan.append({
                "day": d, "date": f"Day {d}",
                "topics": day_topics,
                "tasks": [f"Read and take notes on {t}" for t in day_topics] + ["Review flashcards"],
                "duration_hours": 2.0,
            })
        return {"plan": plan, "tips": ["Take regular breaks", "Use active recall", "Practice with flashcards"]}


# Singleton
_ai_instance: Optional[GraniteAI] = None

def get_ai() -> GraniteAI:
    global _ai_instance
    if _ai_instance is None:
        _ai_instance = GraniteAI()
    return _ai_instance
