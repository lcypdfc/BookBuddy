print("Python script started", flush=True)

import json
import faiss
import numpy as np
import requests
import argparse
import sys
import io
from sentence_transformers import SentenceTransformer
from config import *

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ========== Argument Parser ==========
parser = argparse.ArgumentParser()
parser.add_argument("--query", type=str, required=True, help="Question to ask")
parser.add_argument("--index", type=str, default=FAISS_INDEX, help="FAISS index path")
parser.add_argument("--id_map", type=str, default=ID_MAP, help="ID map path")
parser.add_argument("--embed_model", type=str, default=MODEL_NAME, help="Embedding model name")
parser.add_argument("--llm_model", type=str, default=OLLAMA_MODEL, help="Ollama model name")
parser.add_argument("--top_k", type=int, default=3, help="Number of contexts to retrieve")
args = parser.parse_args()

# ========== Loaders ==========
def load_index_and_map(index_path, id_map_path):
    index = faiss.read_index(index_path)
    with open(id_map_path, "r", encoding="utf-8") as f:
        id_map = json.load(f)
    return index, id_map

def embed_query(query, model_name):
    model = SentenceTransformer(model_name, trust_remote_code=True)
    return model.encode([query])[0]

# def build_prompt(query, contexts):
#     context_block = "\n\n".join([f"{i+1}. {ctx.strip()}" for i, ctx in enumerate(contexts)])
#     return f"""You are a helpful math tutor. Based on the following context, answer the question clearly.

# Context:
# {context_block}

# Question: {query}
# Answer:"""

def build_prompt(query, contexts):
    context_block = "\n\n".join([f"{i+1}. {ctx.strip()}" for i, ctx in enumerate(contexts)])
    return f"""You are a helpful math tutor. Based on the following context, answer the question clearly.

    - Format your answer in **Markdown**.
    - Use **LaTeX** syntax for math.
    - Wrap inline math with `$...$`, and block formulas with `$$...$$`.
    - Do not explain how you format it, just output the final answer.

    Context:
    {context_block}

    Question: {query}
    Answer:"""


def query_ollama(prompt, model_name):
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(OLLAMA_URL, json=payload)
    result = response.json()
    print("Ollama returned:", result)

    if "response" in result:
        return result["response"].strip()
    elif "error" in result:
        return f"Ollama returned error: {result['error']}"
    else:
        return "Unknown error: no response field returned"

# ========== Main Logic ==========
def answer_question(query, index_path, id_map_path, embed_model, llm_model, top_k):
    print(f"User query: {query}")

    if not index_path or not id_map_path:
        # no RAG - pure prompt
        prompt = f"You are a helpful tutor. Answer the following question clearly:\n\nQuestion: {query}\nAnswer:"
        answer = query_ollama(prompt, llm_model)
        return {
            "answer": answer,
            "question": query,
            "retrieved": [],
            "embed_model": None,
            "llm_model": llm_model
        }

    # RAG logic below as before
    index, id_map = load_index_and_map(index_path, id_map_path)
    q_vec = embed_query(query, embed_model).astype("float32")
    _, I = index.search(np.array([q_vec]), top_k)
    retrieved = [id_map[i]["context"] for i in I[0]]
    prompt = build_prompt(query, retrieved)
    answer = query_ollama(prompt, llm_model)

    return {
        "answer": answer,
        # "question": query,
        # "retrieved": retrieved,
        "embed_model": embed_model,
        "llm_model": llm_model
    }

# ========== Run ==========
if __name__ == "__main__":
    result = answer_question(
        args.query,
        args.index,
        args.id_map,
        args.embed_model,
        args.llm_model,
        args.top_k
    )
    # print(json.dumps(result, ensure_ascii=False), flush=True)
    final_output = {
        "answer": result["answer"],
        "llm_model": result["llm_model"],
        "embed_model": result["embed_model"]
    }
    print(json.dumps(final_output, ensure_ascii=False), flush=True)
