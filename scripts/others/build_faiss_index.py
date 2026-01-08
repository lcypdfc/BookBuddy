import json
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from config import *


# ========== Configuration Section ==========
JSONL_PATH = QA_WITH_ANS
INDEX_OUT = FAISS_INDEX
ID_MAP_OUT = ID_MAP
EMBED_MODEL = MODEL_NAME
# ===========================================

def load_contexts(jsonl_path):
    """Load context texts and build ID map from a .jsonl file."""
    contexts, id_map = [], []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            obj = json.loads(line)
            ctx = obj.get("context", "").strip()
            if len(ctx) > 30:
                contexts.append(ctx)
                id_map.append({
                    "index": i,
                    "context": ctx,
                    "question": obj.get("question", "")
                })
    return contexts, id_map

def embed_texts(texts, model_name):
    """Encode a list of texts into sentence embeddings."""
    model = SentenceTransformer(model_name, trust_remote_code=True)
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    return embeddings

def build_and_save_faiss_index(embeddings, index_path, id_map_path, id_map):
    """Build FAISS index and save it along with the ID map."""
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    faiss.write_index(index, index_path)
    with open(id_map_path, "w", encoding="utf-8") as f:
        json.dump(id_map, f, ensure_ascii=False, indent=2)
    print(f"Index saved to {index_path}, ID map saved to {id_map_path}")

def main():
    print("Loading data...")
    contexts, id_map = load_contexts(JSONL_PATH)

    print(f"Embedding {len(contexts)} contexts...")
    embeddings = embed_texts(contexts, EMBED_MODEL)

    print("Building FAISS index...")
    build_and_save_faiss_index(np.array(embeddings), INDEX_OUT, ID_MAP_OUT, id_map)

if __name__ == "__main__":
    main()
