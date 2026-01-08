import json
import time
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
import requests
from config import *  # Load shared config paths and model names
from build_faiss_index_core import build_index_with_model

# ========== Configuration Section ==========
QUESTION_FILE_NAME = "basic_math_questions_no_answer.jsonl"
QUESTION_FILE = QUESTION_DIR + QUESTION_FILE_NAME
FULL_CONTEXT_FILE = QA_WITH_ANS
JSONL_PATH = FULL_CONTEXT_FILE
TOP_K = 3
OUTPUT_FILE = "../report/batch_eval_comparison.jsonl"
TIMING_FILE = "../report/batch_eval_timing_report.jsonl"  # Save time profiling info

EMBED_MODELS = [
    "all-MiniLM-L6-v2",
    "intfloat/e5-small-v2",
    "BAAI/bge-small-en",
    "sentence-transformers/all-mpnet-base-v2",
    "thenlper/gte-large",
    "Alibaba-NLP/gte-base-en-v1.5"
]
# ===========================================

def query_ollama(prompt):
    """
    Query the local Ollama LLM server with a given prompt.
    Returns the plain text response.
    """
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    response = requests.post(OLLAMA_URL, json=payload)
    result = response.json()
    return result.get("response", "").strip()

def build_prompt(query, contexts):
    """
    Construct the full prompt for the LLM, combining retrieved context and the question.
    """
    context_block = "\n\n".join([f"{i+1}. {c.strip()}" for i, c in enumerate(contexts)])
    return f"""You are a helpful math tutor. Based on the following context, answer the question clearly.

Context:
{context_block}

Question: {query}
Answer:"""

def main():
    """
    Main evaluation loop to compare the performance of multiple embedding models
    using a common set of questions and retrieval-based prompting.
    """
    # Load all questions
    with open(QUESTION_FILE, "r", encoding="utf-8") as f:
        questions = [json.loads(line)["question"] for line in f]

    comparison_results = [
        {"question": q, "answers": {}, "retrieved": {}} for q in questions
    ]
    timing_results = []

    for model_name in EMBED_MODELS:
        print(f"\n===== Evaluating model: {model_name} =====")
        t0 = time.time()

        # Set paths for FAISS index and ID mapping
        index_path = f"{EMBEDDING_DIR}/faiss_{model_name.replace('/', '_')}.index"
        idmap_path = f"{EMBEDDING_DIR}/id_map_{model_name.replace('/', '_')}.json"

        print(f"→ Building or loading FAISS index...")
        build_index_with_model(JSONL_PATH, model_name, index_path, idmap_path)

        index = faiss.read_index(index_path)
        with open(idmap_path, "r", encoding="utf-8") as f:
            id_map = json.load(f)

        embed_model = SentenceTransformer(model_name, trust_remote_code=True)

        embed_time = 0
        search_time = 0
        llm_time = 0

        for idx, q in enumerate(questions):
            print(f"  → [{idx+1}/{len(questions)}] Processing question...")

            # Step 1: Encode the question into an embedding vector
            t_embed = time.time()
            q_vec = embed_model.encode([q])[0].astype("float32")
            embed_time += time.time() - t_embed

            # Step 2: Use FAISS to find top-K most relevant contexts
            t_search = time.time()
            _, I = index.search(np.array([q_vec]), TOP_K)
            contexts = [id_map[i]["context"] for i in I[0]]
            search_time += time.time() - t_search

            # Step 3: Build the prompt and query the LLM
            prompt = build_prompt(q, contexts)
            t_llm = time.time()
            answer = query_ollama(prompt)
            llm_time += time.time() - t_llm

            # Store results
            comparison_results[idx]["answers"][model_name] = answer
            comparison_results[idx]["retrieved"][model_name] = contexts

        t1 = time.time()

        timing_results.append({
            "model": model_name,
            "total_questions": len(questions),
            "total_time": round(t1 - t0, 2),
            "embedding_time": round(embed_time, 2),
            "retrieval_time": round(search_time, 2),
            "llm_inference_time": round(llm_time, 2)
        })

        print(f"✔ Finished model: {model_name}")
        print(f"  → Time: {round(t1 - t0, 2)}s | Embed: {round(embed_time, 2)}s | Search: {round(search_time, 2)}s | LLM: {round(llm_time, 2)}s")

    # Save results to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in comparison_results:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    with open(TIMING_FILE, "w", encoding="utf-8") as f:
        for item in timing_results:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\n All models evaluated successfully.")
    print(f"  → Results saved to: {OUTPUT_FILE}")
    print(f"  → Timing report saved to: {TIMING_FILE}")

if __name__ == "__main__":
    main()
