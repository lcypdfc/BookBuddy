import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import requests
from pathlib import Path
from config import *


# ========== Configuration Section ==========
QUESTION_FILE_NAME = 'basic_math_questions_no_answer.jsonl'
QUESTION_FILE = QUESTION_DIR + QUESTION_FILE_NAME
FULL_CONTEXT_FILE = QA_WITH_ANS
INDEX_PATH = FAISS_INDEX
ID_MAP_PATH = ID_MAP
MODEL_NAME = MODEL_NAME
OLLAMA_URL = OLLAMA_URL
OLLAMA_MODEL = OLLAMA_MODEL
TOP_K = 3
OUTPUT_FILE = "../report/batch_eval_results.jsonl"
# ===========================================

def load_index_and_map():
    """Load FAISS index and corresponding ID map."""
    index = faiss.read_index(INDEX_PATH)
    with open(ID_MAP_PATH, "r", encoding="utf-8") as f:
        id_map = json.load(f)
    return index, id_map

def load_full_context(path):
    """Load all full contexts from a .jsonl file."""
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line)["context"] for line in f if "context" in json.loads(line)]

def embed_query(query, model):
    """Encode a question string into embedding vector."""
    return model.encode([query])[0]

def query_ollama(prompt):
    """Query local Ollama model with prompt."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(OLLAMA_URL, json=payload)
    result = response.json()
    if "response" in result:
        return result["response"].strip()
    elif "error" in result:
        return f"Ollama returned error: {result['error']}"
    else:
        return "Unknown error: no response field"

def build_prompt(query, contexts):
    """Build LLM prompt from user query and list of contexts."""
    context_block = "\n\n".join([f"{i+1}. {c.strip()}" for i, c in enumerate(contexts)])
    return f"""You are a helpful math tutor. Based on the following context, answer the question clearly.

Context:
{context_block}

Question: {query}
Answer:"""

def run_eval():
    """Run evaluation for three modes: zero-shot, full-prompt, RAG."""
    with open(QUESTION_FILE, "r", encoding="utf-8") as f:
        questions = [json.loads(line)["question"] for line in f]

    embed_model = SentenceTransformer(MODEL_NAME)
    index, id_map = load_index_and_map()
    full_contexts = load_full_context(FULL_CONTEXT_FILE)

    results = []
    for q in questions:
        print(f"Evaluating question: {q}")

        # Zero-shot
        zs_prompt = f"""You are a helpful math tutor. Please answer the following question clearly.

Question: {q}
Answer:"""
        zs_answer = query_ollama(zs_prompt)
        results.append({
            "question": q,
            "mode": "zero-shot",
            "prompt": zs_prompt,
            "answer": zs_answer
        })

        # Full-prompt (first TOP_K full contexts)
        full_prompt = build_prompt(q, full_contexts[:TOP_K])
        full_answer = query_ollama(full_prompt)
        results.append({
            "question": q,
            "mode": "full-prompt",
            "prompt": full_prompt,
            "answer": full_answer
        })

        # RAG-prompt (context from index)
        q_vec = embed_query(q, embed_model).astype("float32")
        _, I = index.search(np.array([q_vec]), TOP_K)
        rag_contexts = [id_map[i]["context"] for i in I[0]]
        rag_prompt = build_prompt(q, rag_contexts)
        rag_answer = query_ollama(rag_prompt)
        results.append({
            "question": q,
            "mode": "rag",
            "prompt": rag_prompt,
            "retrieved": rag_contexts,
            "answer": rag_answer
        })

    # Save results to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_eval()
