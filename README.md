# Smart Study Generator

> **AI-powered adaptive study companion built with IBM Granite + watsonx.ai + Streamlit**

---

## 🚀 Quick Start

```bash
# Option A — PowerShell script (Windows)
powershell -ExecutionPolicy Bypass -File run.ps1

# Option B — manual
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## 📁 Project Structure

```
Smart/
├── app.py                        # Main Streamlit application (8 tabs)
├── requirements.txt              # Python dependencies
├── run.ps1                       # One-click launcher
└── modules/
    ├── __init__.py
    ├── granite_ai.py             # IBM Granite / watsonx.ai integration
    ├── content_processor.py      # PDF / DOCX / image / text extraction
    ├── study_planner.py          # Session state, progress tracking, alerts
    └── ui_components.py          # Reusable styled Streamlit components
```

---

## ✨ Features

| Tab | Feature |
|-----|---------|
| 📊 Dashboard | Real-time metrics, weekly activity chart, topic radar, quiz history |
| 📄 Summarize | AI summaries (brief/medium/detailed), key topic extraction, mnemonics |
| 🃏 Flashcards | Auto-generated flip cards, difficulty filter, shuffle |
| ❓ Quiz | MCQ quiz with scoring, explanations, retake |
| 📅 Study Plan | Personalized n-day plan with Gantt chart and daily breakdown |
| 🗺️ Concept Map | Visual knowledge graph of uploaded content |
| 💬 AI Tutor | Context-aware Q&A chat with quick-prompt shortcuts |
| 🔮 Exam Predictor | Probability-ranked topic predictions + weak-area analysis |

---

## ⚙️ IBM Granite Configuration

The IBM credentials are pre-configured in `modules/granite_ai.py`:

```python
IBM_API_KEY    = "Aq0CCkbQoJnb3BViW8BfPDoNoX63V-31X97vAvPbUjWx"
IBM_PROJECT_ID = "8a39dfde-3880-4b31-8270-248a9785f594"
IBM_URL        = "https://us-south.ml.cloud.ibm.com"
GRANITE_MODEL  = "ibm/granite-13b-instruct-v2"
```

> **Note:** `ibm-watsonx-ai` requires Python 3.10–3.13. On Python 3.15 the app runs in **demo mode** with realistic fallback responses. To enable live IBM Granite, use Python 3.11 or 3.12 and run:
> ```
> pip install ibm-watsonx-ai
> ```

---

## 📥 Supported Input Types

- **PDF** — lecture notes, textbooks, research papers
- **DOCX** — Word documents
- **TXT** — plain text notes
- **Images** (PNG/JPG) — textbook pages (OCR via Tesseract)
- **Paste text** — direct copy-paste from any source
- **Sample topics** — built-in demo content (ML, Data Structures, Thermodynamics)

---

## 🛠️ Tech Stack

- **IBM Granite** (`ibm/granite-13b-instruct-v2`) via **IBM watsonx.ai**
- **Streamlit 1.66** — frontend framework
- **Plotly** — interactive charts (bar, radar, Gantt)
- **PyMuPDF** — PDF extraction
- **Pytesseract** — image OCR
- **python-docx** — Word document parsing
