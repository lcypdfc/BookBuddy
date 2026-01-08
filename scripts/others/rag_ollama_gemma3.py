print("Python script started", flush=True)

import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import requests
from config import *

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')



# ========== Configuration Section ==========
INDEX_PATH = FAISS_INDEX
ID_MAP_PATH = ID_MAP
MODEL_NAME = MODEL_NAME
OLLAMA_URL = OLLAMA_URL
OLLAMA_MODEL = OLLAMA_MODEL

TOP_K = 3  # Number of top context to retrieve
MAX_TOKENS = 500  # Maximum token length for prompt
# ===========================================

def load_index_and_map():
    """Load the FAISS index and corresponding ID map."""
    index = faiss.read_index(INDEX_PATH)
    with open(ID_MAP_PATH, "r", encoding="utf-8") as f:
        id_map = json.load(f)
    return index, id_map

def embed_query(query, model):
    """Embed the user query using the SentenceTransformer model."""
    return model.encode([query])[0]

def build_prompt(query, contexts):
    """Construct the full prompt for the LLM using retrieved contexts."""
    context_block = "\n\n".join([f"{i+1}. {ctx.strip()}" for i, ctx in enumerate(contexts)])
    prompt = f"""You are a helpful math tutor. Based on the following context, answer the question clearly.

Context:
{context_block}

Question: {query}
Answer:"""
    return prompt

def query_ollama(prompt):
    """Send the constructed prompt to the local Ollama server."""
    payload = {
        "model": OLLAMA_MODEL,
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

# def answer_question(query):
#     """Main RAG loop to answer a user question."""
#     print(f"User query: {query}")
#     index, id_map = load_index_and_map()
#     embed_model = SentenceTransformer(MODEL_NAME)

#     q_vec = embed_query(query, embed_model).astype("float32")
#     _, I = index.search(np.array([q_vec]), TOP_K)

#     retrieved = [id_map[i]["context"] for i in I[0]]
#     prompt = build_prompt(query, retrieved)
#     response = query_ollama(prompt)

    # print("\nPrompt sent to LLM:\n" + "-"*40)
    # print(prompt)
    # print("\nLLM Response:\n" + "-"*40)
    # print(response)

# if __name__ == "__main__":
#     while True:
#         query = input("\nEnter your question (type 'exit' to quit):\n> ").strip()
#         if query.lower() in {"exit", "quit"}:
#             break
#         answer_question(query)

def answer_question(query):
    print(f"User query: {query}")
    index, id_map = load_index_and_map()
    embed_model = SentenceTransformer(MODEL_NAME)

    q_vec = embed_query(query, embed_model).astype("float32")
    _, I = index.search(np.array([q_vec]), TOP_K)

    retrieved = [id_map[i]["context"] for i in I[0]]
    prompt = build_prompt(query, retrieved)
    response = query_ollama(prompt)
    return response  



import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, help="Question to ask the RAG model")
    args = parser.parse_args()

    if args.query:
        print("Python script started with --query:", args.query, flush=True)
        answer = answer_question(args.query)
        print(json.dumps({"answer": answer}, ensure_ascii=False), flush=True)
    else:
        print("Python script started in interactive mode", flush=True)
        while True:
            query = input("\nEnter your question (type 'exit' to quit):\n> ").strip()
            if query.lower() in {"exit", "quit"}:
                break
            answer = answer_question(query)
            print(answer)

