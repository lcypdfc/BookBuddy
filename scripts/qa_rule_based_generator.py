import re
import json
import uuid
from pathlib import Path
import fitz
from random import choice
import sys
sys.stdout.reconfigure(encoding='utf-8')

# ========== Cleaning Rules ==========
def clean_line(line: str) -> str:
    patterns = [
        r"^\d+\s+CHAPTER\s+\d+",
        r"^CHAPTER\s+\d+(\.\d+)?",
        r"^Figure\s+\d+(\.\d+)?",
        r"^Table\s+\d+(\.\d+)?",
        r"^Page\s+\d+$"
    ]
    for pat in patterns:
        if re.match(pat, line, re.IGNORECASE):
            return ""
    return line.strip()

def is_probably_toc_line(line: str) -> bool:
    if not line.strip():
        return True
    if "table of contents" in line.lower():
        return True
    if re.search(r'\.{3,}', line):
        return True
    if re.search(r'\s\.+\s*\d{1,3}$', line):
        return True
    if re.fullmatch(r'[\d\.\s]+', line.strip()):
        return True
    toc_keywords = ["exercise", "section", "chapter", "contents", "index"]
    if any(k in line.lower() for k in toc_keywords) and len(line.split()) <= 10:
        return True
    return False

# ========== Paragraph Chunking ==========
def is_valid_paragraph(text: str) -> bool:
    if len(text) < 40:
        return False
    if re.fullmatch(r'[\d\s.]+', text):
        return False
    if text.count('.') > 30:
        return False
    return True

def extract_paragraphs(pdf_path: Path, words_per_chunk: int = 180):
    doc = fitz.open(pdf_path)
    buffer, wc = [], 0

    for page in doc:
        blocks = page.get_text("blocks")
        lines = []

        for block in blocks:
            text = block[4].replace("\n", " ").strip()
            if not text:
                continue
            cleaned = clean_line(text)
            if cleaned:
                lines.append(cleaned)

        for ln in lines:
            if is_probably_toc_line(ln):
                continue
            for sent in re.split(r'(?<=[.!?])\s+', ln):
                words = sent.split()
                buffer.append(sent)
                wc += len(words)
                if wc >= words_per_chunk:
                    paragraph = " ".join(buffer).strip()
                    if is_valid_paragraph(paragraph):
                        yield paragraph
                    buffer, wc = [], 0

    if buffer:
        paragraph = " ".join(buffer).strip()
        if is_valid_paragraph(paragraph):
            yield paragraph

# ========== Question Generation ==========
GENERAL_TEMPLATES = [
    "What is the main idea of this paragraph?",
    "What concept is introduced here?",
    "What does this paragraph discuss?",
    "Summarize the topic of this paragraph.",
    "What question does this paragraph try to answer?"
]

REGEX_PATTERNS = [
    r"([A-Z][\w\s-]{2,}) is defined as",
    r"([A-Z][\w\s-]{2,}) is called",
    r"([A-Z][\w\s-]{2,}) refers to",
    r"([A-Z][\w\s-]{2,}) represents",
    r"([A-Z][\w\s-]{2,}) denotes",
    r"([A-Z][\w\s-]{2,}) means"
]

def extract_main_concept(text: str):
    if m := re.search(r"([A-Z][\w ]+?)\s+(is|are|denotes|means|represents|refers to|called)", text):
        c = m.group(1).strip()
        return None if c.lower() in {"it", "this", "that"} else c
    return None

def generate_question(paragraph: str):
    for pat in REGEX_PATTERNS:
        if m := re.search(pat, paragraph):
            qterm = m.group(1).strip().rstrip(".")
            return f"What is {qterm}?", False

    if concept := extract_main_concept(paragraph):
        verb = "do" if concept.lower().endswith("s") else "does"
        return f"What {verb} {concept} mean?", False

    return choice(GENERAL_TEMPLATES), True

# ========== Answer Extraction ==========
def extract_answer(paragraph: str, question: str):
    tokens = re.sub(r"[^\w\s]", "", question).split()
    key = tokens[-1] if tokens else None
    if key:
        for sent in re.split(r'(?<=[.!?])\s+', paragraph):
            if key.lower() in sent.lower():
                return sent.strip()
    return paragraph.strip()

# ========== Main QA Generation ==========
def generate_qa_file(pdf_path: Path, output_path: Path, words_per_chunk=180):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fout:
        for para in extract_paragraphs(pdf_path, words_per_chunk):
            question, is_fb = generate_question(para)
            answer = extract_answer(para, question)
            qa = {
                "id": str(uuid.uuid4()),
                "question": question,
                "answer": answer,
                "context": para,
                "is_fallback": is_fb
            }
            fout.write(json.dumps(qa, ensure_ascii=False) + "\n")
            # print(f"[OK] {question}")  # 禁用调试输出以防止 JSON 混淆

# ========== CLI ==========
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=str, required=True, help="Path to input PDF file")
    parser.add_argument("--out", type=str, required=True, help="Path to output .jsonl")
    parser.add_argument("--chunk_size", type=int, default=180, help="Words per chunk")
    args = parser.parse_args()

    generate_qa_file(
        pdf_path=Path(args.pdf),
        output_path=Path(args.out),
        words_per_chunk=args.chunk_size
    )

    print(json.dumps({
        "success": True,
        "message": f"QA generated successfully from {args.pdf}",
        "output": str(args.out)
    }), flush=True)
