"""
Content Processor Module
Handles extraction of text from various file formats and sources.
"""

import io
import os
import re
from typing import Optional

# ── Optional heavy deps ────────────────────────────────────────────────────────
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes. Falls back to a helpful message if PyMuPDF is unavailable."""
    if not PYMUPDF_AVAILABLE:
        return "[PDF extraction requires PyMuPDF. Install with: pip install PyMuPDF]\n\nDemo content: This is a sample educational text about important concepts. Key topics include theoretical frameworks, practical applications, and research methodologies. Students should focus on understanding the core principles and their real-world applications."
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        return "\n".join(text_parts)
    except Exception as e:
        return f"[Error reading PDF: {e}]"


def extract_text_from_image(file_bytes: bytes) -> str:
    """OCR text extraction from image bytes."""
    if not OCR_AVAILABLE:
        return "[Image OCR requires Pillow + pytesseract + Tesseract. Using demo text]\n\nDemo content: This textbook page discusses fundamental concepts in the subject area. Important formulas, definitions, and examples are highlighted for student reference."
    try:
        img = Image.open(io.BytesIO(file_bytes))
        return pytesseract.image_to_string(img)
    except Exception as e:
        return f"[Error reading image: {e}]"


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a .docx file."""
    if not DOCX_AVAILABLE:
        return "[DOCX extraction requires python-docx. Install with: pip install python-docx]\n\nDemo content: These lecture notes cover the essential topics of the course. Students are expected to understand all concepts presented here."
    try:
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        return f"[Error reading DOCX: {e}]"


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Decode plain-text bytes."""
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return file_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
    return "[Could not decode text file]"


def process_uploaded_file(uploaded_file) -> tuple[str, str]:
    """
    Given a Streamlit UploadedFile, return (extracted_text, file_type).
    file_type is one of: pdf | image | docx | txt | unknown
    """
    name = uploaded_file.name.lower()
    raw  = uploaded_file.read()

    if name.endswith(".pdf"):
        return extract_text_from_pdf(raw), "pdf"
    elif name.endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp")):
        return extract_text_from_image(raw), "image"
    elif name.endswith(".docx"):
        return extract_text_from_docx(raw), "docx"
    elif name.endswith(".txt"):
        return extract_text_from_txt(raw), "txt"
    else:
        try:
            return extract_text_from_txt(raw), "txt"
        except Exception:
            return "[Unsupported file format]", "unknown"


def clean_text(text: str) -> str:
    """Basic text normalisation."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\/\\]', '', text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks suitable for AI processing."""
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunk = " ".join(words[i: i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks or [text]


def count_words(text: str) -> int:
    return len(text.split())


def estimate_reading_time(text: str, wpm: int = 200) -> float:
    """Return estimated reading time in minutes."""
    return round(count_words(text) / wpm, 1)


SAMPLE_CONTENTS = {
    "Machine Learning": """
Machine Learning (ML) is a subset of artificial intelligence that enables systems to learn from data without being explicitly programmed.
Key types include Supervised Learning (labeled data → regression, classification), Unsupervised Learning (unlabeled data → clustering, dimensionality reduction), and Reinforcement Learning (reward-based feedback).
Important algorithms: Linear Regression, Logistic Regression, Decision Trees, Random Forests, Support Vector Machines (SVM), K-Means Clustering, Neural Networks, and Gradient Boosting.
The ML pipeline covers: Data Collection → Preprocessing → Feature Engineering → Model Training → Evaluation → Deployment.
Metrics: Accuracy, Precision, Recall, F1-Score, ROC-AUC, MSE, RMSE.
Overfitting occurs when a model memorises training data; it is prevented via regularisation (L1/L2), dropout, and cross-validation.
Deep Learning uses multi-layer neural networks (CNNs for images, RNNs/LSTMs for sequences, Transformers for NLP).
    """,
    "Data Structures": """
Data structures organise and store data efficiently to support algorithms.
Arrays: fixed-size, O(1) access, O(n) insert/delete.
Linked Lists: dynamic size, O(n) access, O(1) insert/delete at head.
Stacks (LIFO) and Queues (FIFO) are fundamental linear structures.
Trees: Binary Tree, BST (O(log n) search), AVL Tree, Red-Black Tree, Heap.
Graphs: represented as adjacency matrix or list; traversed via BFS (level-order) and DFS (depth-first).
Hash Tables: O(1) avg lookup; collisions resolved via chaining or open addressing.
Sorting algorithms: Bubble O(n²), Selection O(n²), Insertion O(n²), Merge O(n log n), Quick O(n log n) avg.
Searching: Linear O(n), Binary O(log n) (sorted arrays only).
    """,
    "Thermodynamics": """
Thermodynamics is the branch of physics concerned with heat, work, and temperature.
Zeroth Law: if A=B and B=C in thermal equilibrium, then A=C (defines temperature).
First Law: Energy is conserved; ΔU = Q − W (internal energy = heat added − work done).
Second Law: Entropy of an isolated system never decreases; heat flows hot → cold.
Third Law: Entropy approaches a constant as temperature approaches absolute zero.
Key concepts: enthalpy (H = U + PV), entropy (S), Gibbs free energy (G = H − TS).
Carnot efficiency: η = 1 − T_cold/T_hot (theoretical maximum for heat engines).
Thermodynamic processes: isothermal, adiabatic, isobaric, isochoric.
    """,
}
