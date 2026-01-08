import argparse
import json
import re
import uuid
from pathlib import Path
import fitz  # PyMuPDF
import requests
from tqdm import tqdm
from sentence_transformers import SentenceTransformer, util

# ========== Configuration ==========
DEFAULT_MIN_CHARS = 400
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:latest"
EMBED_MODEL = "all-MiniLM-L6-v2"

embedder = SentenceTransformer(EMBED_MODEL)
# ===================================


def clean_line(line: str) -> str:
    """
    Remove headers, footers, and common structural markers like chapter titles and figure/table labels.
    """
    patterns = [
        r"^\d+\s+CHAPTER\s+\d+",
        r"^CHAPTER\s+\d+(\.\d+)?",
        r"^Figure\s+\d+(\.\d+)?",
        r"^Table\s+\d+(\.\d+)?",
        r"^Page\s+\d+$"
    ]
    for pattern in patterns:
        if re.match(pattern, line, re.IGNORECASE):
            return ""
    return line.strip()


def is_toc_line(line: str) -> bool:
    """
    Heuristically detect lines likely to be part of a table of contents.
    """
    return (
        "table of contents" in line.lower() or
        re.search(r'\.{3,}', line) or
        re.match(r'\s*\d+(\.\d+)*\s+.*', line) or
        re.search(r'\s\.+\s\d{1,3}$', line)
    )


def extract_paragraphs(pdf_path: Path, min_chars: int):
    """
    Parse a PDF and yield clean paragraph blocks of at least `min_chars` characters.
    Sentences are accumulated until a complete paragraph is formed.
    """
    doc = fitz.open(pdf_path)
    buffer, current_len = [], 0

    for page in doc:
        blocks = page.get_text("blocks")
        for block in blocks:
            text = block[4].replace("\n", " ")
            if not text.strip():
                continue
            cleaned = clean_line(text)
            if cleaned and not is_toc_line(cleaned):
                for sentence in re.split(r'(?<=[.!?])\s+', cleaned):
                    buffer.append(sentence)
                    current_len += len(sentence)
                    if current_len >= min_chars:
                        paragraph = " ".join(buffer).strip()
                        if len(paragraph) > 40:
                            yield paragraph
                        buffer, current_len = [], 0

    # Handle remaining text if any
    if buffer:
        paragraph = " ".join(buffer).strip()
        if len(paragraph) > 40:
            yield paragraph


def generate_question(paragraph: str) -> str:
    """
    Use a local Ollama LLM to generate a question from the given paragraph.
    """
    prompt = f"""You are a helpful tutor. Please read the following paragraph and generate a clear and relevant question about it.

Paragraph:
{paragraph}

Question:"""
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        })
        result = response.json()
        question = result.get("response", "").strip()
        if "**Question:**" in question:
            question = question.split("**Question:**")[-1].strip()
        return question
    except Exception as e:
        print(f"[Ollama Error] {e}")
        return "What is this paragraph about?"


def extract_answer(paragraph: str, question: str) -> str:
    """
    Use embedding similarity to identify the most relevant sentence in the paragraph that answers the question.
    """
    sentences = re.split(r'(?<=[.!?])\s+', paragraph)
    if len(sentences) == 1:
        return paragraph.strip()

    q_embedding = embedder.encode(question, convert_to_tensor=True)
    sent_embeddings = embedder.encode(sentences, convert_to_tensor=True)
    scores = util.cos_sim(q_embedding, sent_embeddings)
    best_idx = scores.argmax().item()
    return sentences[best_idx].strip()


def generate_qa_file(pdf_path: Path, output_path: Path, min_chars: int, max_paras: int = None):
    """
    Perform the full QA generation pipeline:
    1. Extract paragraphs from PDF
    2. Generate a question using LLM
    3. Find the most relevant answer sentence
    4. Save as JSONL
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    paras = list(extract_paragraphs(pdf_path, min_chars))
    if max_paras:
        paras = paras[:max_paras]

    with output_path.open("w", encoding="utf-8") as fout:
        for para in tqdm(paras, desc="Generating QA"):
            question = generate_question(para)
            answer = extract_answer(para, question)
            qa = {
                "id": str(uuid.uuid4()),
                "question": question,
                "answer": answer,
                "context": para
            }
            fout.write(json.dumps(qa, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=str, required=True, help="Path to the input PDF file")
    parser.add_argument("--out", type=str, required=True, help="Path to output QA .jsonl file")
    parser.add_argument("--min_chars", type=int, default=DEFAULT_MIN_CHARS, help="Minimum characters per paragraph")
    parser.add_argument("--max_paras", type=int, default=None, help="Maximum number of paragraphs to process")
    args = parser.parse_args()

    generate_qa_file(
        pdf_path=Path(args.pdf),
        output_path=Path(args.out),
        min_chars=args.min_chars,
        max_paras=args.max_paras
    )
