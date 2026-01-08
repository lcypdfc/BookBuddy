# build_faiss_index_core.py

import json
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from pathlib import Path


def build_index_with_model(
    jsonl_path: str,
    model_name: str,
    index_out_path: str,
    id_map_out_path: str
):
    """Encode contexts with specified model and build FAISS index."""
    print(f"\n[Embedding] Using model: {model_name}")
    print(f"[Input] Loading: {jsonl_path}")

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

    print(f"[Encoding] Total contexts: {len(contexts)}")
    model = SentenceTransformer(model_name, trust_remote_code=True)
    embeddings = model.encode(contexts, show_progress_bar=True, convert_to_numpy=True)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    faiss.write_index(index, index_out_path)
    with open(id_map_out_path, "w", encoding="utf-8") as f:
        json.dump(id_map, f, ensure_ascii=False, indent=2)

    print(f"[Saved] Index → {index_out_path}")
    print(f"[Saved] ID Map → {id_map_out_path}")

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl_path", type=str, help="Path to input QA .jsonl file")
    parser.add_argument("model_name", type=str, help="Embedding model name")
    parser.add_argument("index_out_path", type=str, help="Path to save FAISS index")
    parser.add_argument("id_map_out_path", type=str, help="Path to save ID map")
    args = parser.parse_args()

    build_index_with_model(
        jsonl_path=args.jsonl_path,
        model_name=args.model_name,
        index_out_path=args.index_out_path,
        id_map_out_path=args.id_map_out_path
    )

    result = {
        "success": True,
        "message": f"Index built using {args.model_name}",
        "indexPath": args.index_out_path,
        "idMapPath": args.id_map_out_path
    }
    print(json.dumps(result), flush=True)

