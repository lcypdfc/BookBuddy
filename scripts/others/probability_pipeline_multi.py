import argparse
import json
import re
import uuid
from pathlib import Path
from random import choice
import fitz  # PyMuPDF
from config import *


# ========== Configuration Section ==========
DEFAULT_PDF_DIR = DEFAULT_PDF
DEFAULT_CHUNK_SIZE = 180
# ==========================================

def clean_line(line: str) -> str:
    """Remove headers, footers, figure/table references from text lines."""
    patterns = [
        r"^\d+\s+CHAPTER\s+\d+",
        r"^CHAPTER\s+\d+(\.\d+)?",
        r"^Figure\s+\d+(\.\d+)?",
        r"^Table\s+\d+(\.\d+)?",
        r"^Page\s+\d+$"
    ]
    for p in patterns:
        if re.match(p, line, re.IGNORECASE):
            return ""
    return line

def is_probably_toc_line(line: str) -> bool:
    """Heuristic to detect lines that belong to table of contents."""
    return (
        "table of contents" in line.lower()
        or re.search(r'\.{3,}', line)
        or re.match(r'\s*\d+(\.\d+)*\s+.*', line)
        or re.search(r'\s\.+\s\d{1,3}$', line)
    )

def pdf_to_clean_paragraphs(pdf_path: Path, words_per_chunk: int = 180):
    """Extract and yield cleaned paragraph chunks with metadata from a PDF."""
    doc = fitz.open(pdf_path)
    buffer, chunk_title, wc = [], "", 0

    for page in doc:
        blocks = page.get_text("blocks")
        lines = []

        for block in blocks:
            block_text = block[4]
            block_text = block_text.replace("\n", " ")  # remove newline within block
            if not block_text.strip():
                continue
            cleaned = clean_line(block_text.strip())
            if cleaned:
                lines.append(cleaned)

        for ln in lines:
            if m := re.match(r"CHAPTER\s+\d+(\.\d+)?\s*(.*)", ln, re.IGNORECASE):
                chunk_title = m.group(2).strip() or m.group(0).strip()
                continue
            if is_probably_toc_line(ln):
                continue

            for sent in re.split(r'(?<=[.!?])\s+', ln):
                words = sent.split()
                buffer.append(sent)
                wc += len(words)
                if wc >= words_per_chunk:
                    paragraph = " ".join(buffer).strip()
                    if not is_valid_paragraph(paragraph):
                        buffer, wc = [], 0
                        continue
                    yield {
                        "id": str(uuid.uuid4()),
                        "title": chunk_title,
                        "paragraph": paragraph,
                        "topic": chunk_title or "General Probability"
                    }
                    buffer, wc = [], 0

    if buffer:
        paragraph = " ".join(buffer).strip()
        if is_valid_paragraph(paragraph):
            yield {
                "id": str(uuid.uuid4()),
                "title": chunk_title,
                "paragraph": paragraph,
                "topic": chunk_title or "General Probability"
            }

def is_valid_paragraph(paragraph: str) -> bool:
    """Filter out invalid paragraphs (TOC lines, short text, numeric only, etc)."""
    if len(paragraph) < 40:
        return False
    if re.fullmatch(r'[\d\s.]+', paragraph):
        return False
    if paragraph.count('.') > 20:
        return False
    return True

def save_jsonl(items, path: Path):
    """Save a list of JSON objects to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

GENERAL_TEMPLATES = [
    "What concept is introduced here?",
    "What is the main idea of this paragraph?",
    "What topic does this paragraph explain?",
    "What is discussed in this paragraph?",
    "What fundamental concept is explained here?"
]

TOPIC_TEMPLATES = {
    "Random Variables": [
        "What are random variables?", "How is a random variable used in probability?"
    ],
    "Expected Value": [
        "What is the expected value?", "How is expected value calculated?"
    ],
    "Variance": [
        "What is variance?", "What does variance measure in probability?"
    ],
    "Distributions": [
        "What is a probability distribution?", "How are distributions defined?"
    ],
    "General Probability": GENERAL_TEMPLATES
}

REGEX_PATTERNS = [
    r"([A-Z][\w\s-]{2,}) is defined as",
    r"([A-Z][\w\s-]{2,}) is called",
    r"([A-Z][\w\s-]{2,}) refers to",
    r"([A-Z][\w\s-]{2,}) represents",
    r"([A-Z][\w\s-]{2,}) denotes",
    r"([A-Z][\w\s-]{2,}) means"
]

def extract_main_concept(text: str):
    """Attempt to extract main noun phrase from a definition-like sentence."""
    text = re.sub(r"(Let|Suppose|Assume|Consider)\s+", "", text, flags=re.IGNORECASE)
    if m := re.search(r"([A-Z][\w ]+?)\s+(is|are|denotes|means|represents|refers to|called)", text):
        c = m.group(1).strip()
        return None if c.lower() in {"it", "this", "that"} else c
    return None

def generate_question(paragraph: str, topic: str, title: str):
    """Generate a question from a paragraph, using patterns or fallback templates."""
    for pat in REGEX_PATTERNS:
        if m := re.search(pat, paragraph):
            return f"What is {m.group(1).strip()}?", False

    if concept := extract_main_concept(paragraph):
        verb = "do" if concept.lower().endswith("s") else "does"
        return f"What {verb} {concept} represent?", False

    if title:
        return f"What does the section on {title.lower()} discuss?", False

    return choice(TOPIC_TEMPLATES.get(topic, GENERAL_TEMPLATES)), True

def extract_answer_span(paragraph: str, question: str):
    """Heuristically find an answer sentence from the paragraph based on the question."""
    key = None
    if m := re.search(r"definition of (.+?)\?", question, re.IGNORECASE):
        key = m.group(1).strip()
    else:
        toks = [w for w in re.sub(r"[^\w\s]", "", question).split() if len(w) > 4]
        key = toks[-1] if toks else None

    if key:
        for sent in re.split(r'(?<=[.!?])\s+', paragraph):
            if key.lower() in sent.lower():
                return sent.strip()
    return paragraph.strip()

def run_for_pdf(pdf_path: Path, out_prefix: str, chunk_size: int = 180, force=False):
    """Full pipeline: clean → QA → QA with answers."""
    base = Path(JSONL_DIR)
    cleaned = base / f"{out_prefix}.cleaned.jsonl"
    qa = base / f"{out_prefix}.qa.jsonl"
    qa_ans = base / f"{out_prefix}.qa_with_answers.jsonl"

    if cleaned.exists() and cleaned.stat().st_size > 1000 and not force:
        print(f"{out_prefix}: cleaned already exists, skipping Step-1")
    else:
        items = pdf_to_clean_paragraphs(pdf_path, words_per_chunk=chunk_size)
        save_jsonl(items, cleaned)
        print(f"{out_prefix}: cleaned file written")

    total, fb = 0, 0
    with cleaned.open(encoding="utf-8") as fin, qa.open("w", encoding="utf-8") as fout:
        for ln in fin:
            d = json.loads(ln)
            q, is_fb = generate_question(d["paragraph"], d["topic"], d["title"])
            d.update(question=q, is_fallback=is_fb)
            fout.write(json.dumps(d, ensure_ascii=False) + "\n")
            total += 1
            fb += is_fb
    print(f"{out_prefix}: QA generation completed ({total} total, {fb/total:.1%} fallback)")

    cnt = 0
    with qa.open(encoding="utf-8") as fin, qa_ans.open("w", encoding="utf-8") as fout:
        for ln in fin:
            d = json.loads(ln)
            ans = extract_answer_span(d["paragraph"], d["question"])
            d_out = {
                "id": d["id"], "question": d["question"], "answer": ans,
                "context": d["paragraph"], "topic": d["topic"],
                "is_fallback": d["is_fallback"]
            }
            fout.write(json.dumps(d_out, ensure_ascii=False) + "\n")
            cnt += 1
    print(f"{out_prefix}: QA with answers completed ({cnt} entries)\n")

# if __name__ == "__main__":
#     cli = argparse.ArgumentParser()
#     cli.add_argument("--pdf", type=str, help="Path to a single PDF file")
#     cli.add_argument("--prefix", type=str, help="Output prefix (default: file name)")
#     cli.add_argument("--pdf_dir", type=str, help="Directory for batch processing all PDFs")
#     cli.add_argument("--chunk_size", type=int, default=DEFAULT_CHUNK_SIZE)
#     cli.add_argument("--force", action="store_true")
#     args2 = cli.parse_args()

#     if args2.pdf:
#         run_for_pdf(Path(args2.pdf), args2.prefix or Path(args2.pdf).stem, chunk_size=args2.chunk_size, force=args2.force)
#     elif args2.pdf_dir:
#         pdf_dir = Path(args2.pdf_dir)
#         for pdf_file in pdf_dir.glob("*.pdf"):
#             run_for_pdf(pdf_file, pdf_file.stem, chunk_size=args2.chunk_size, force=args2.force)
#     else:
#         cli.print_help()

if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--pdf", type=str, help="Path to a single PDF file")
    cli.add_argument("--prefix", type=str, help="Output prefix (default: file name)")
    cli.add_argument("--pdf_dir", type=str, help="Directory for batch processing all PDFs")
    cli.add_argument("--chunk_size", type=int, default=DEFAULT_CHUNK_SIZE)
    cli.add_argument("--force", action="store_true")
    args2 = cli.parse_args()

    if args2.pdf:
        prefix = args2.prefix or Path(args2.pdf).stem
        run_for_pdf(Path(args2.pdf), prefix, chunk_size=args2.chunk_size, force=args2.force)

        print(json.dumps({
            "success": True,
            "message": f"PDF processed: {prefix}",
            "indexPrefix": prefix,
            "qaPath": f"{JSONL_DIR}/{prefix}.qa_with_answers.jsonl"
        }), flush=True)

    elif args2.pdf_dir:
        pdf_dir = Path(args2.pdf_dir)
        for pdf_file in pdf_dir.glob("*.pdf"):
            run_for_pdf(pdf_file, pdf_file.stem, chunk_size=args2.chunk_size, force=args2.force)
        print(json.dumps({
            "success": True,
            "message": f"All PDFs processed in directory: {args2.pdf_dir}"
        }), flush=True)

    else:
        cli.print_help()
