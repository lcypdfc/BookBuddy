# import os

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# RAW_PDF_DIR = "../materials/raw"
# JSONL_DIR = "../materials/jsonl"
# EMBEDDING_DIR = "../materials/embeddings"
# QUESTION_DIR = "../materials/questions/"

# DEFAULT_PDF = f"{RAW_PDF_DIR}/Introduction_to_Probability.pdf"
# QA_WITH_ANS = f"{JSONL_DIR}/Introduction_to_Probability.qa_with_answers.jsonl"
# FAISS_INDEX = os.path.join(BASE_DIR, "../materials/embeddings/faiss_index.index")
# ID_MAP = f"{EMBEDDING_DIR}/id_map.json"

# MODEL_NAME = "all-MiniLM-L6-v2"
# OLLAMA_URL = "http://localhost:11434/api/generate"
# OLLAMA_MODEL = "gemma3:latest"

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RAW_PDF_DIR = os.path.join(BASE_DIR, "../materials/raw")
JSONL_DIR = os.path.join(BASE_DIR, "../materials/jsonl")
EMBEDDING_DIR = os.path.join(BASE_DIR, "../materials/embeddings")
QUESTION_DIR = os.path.join(BASE_DIR, "../materials/questions")

DEFAULT_PDF = os.path.join(RAW_PDF_DIR, "Introduction_to_Probability.pdf")
QA_WITH_ANS = os.path.join(JSONL_DIR, "Introduction_to_Probability.qa_with_answers.jsonl")
FAISS_INDEX = os.path.join(EMBEDDING_DIR, "faiss_index.index")
ID_MAP = os.path.join(EMBEDDING_DIR, "id_map.json")

MODEL_NAME = "all-MiniLM-L6-v2"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:latest"

