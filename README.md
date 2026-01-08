# BookBuddy: RAG-Based Math Question Answering Framework

**BookBuddy** is a full-stack Retrieval-Augmented Generation (RAG) system that transforms textbook PDFs into interactive Q&A interfaces. It includes:

-  Backend: Node.js server that invokes Python-based RAG scripts
-  Scripts: PDF cleaning, QA generation, FAISS indexing, and LLM-based inference
-  Frontend: React app to upload PDFs, ask questions, and visualize answers with math formatting

---

## Installation

### 1. Clone and set up Python environment

```bash
git clone https://github.com/yourname/bookbuddy.git
cd bookbuddy
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Set up Node.js backend and frontend

```cd backend-node
npm install

cd ../frontend
npm install
```

---

## Project Structure

```
bookbuddy/
├── backend-node/                 ← Express server for file upload and /ask
│   ├── routes/                   ← upload.js and ask.js route handlers
│   ├── utils/                    ← runPython.js: calls Python scripts
│   ├── server.js                 ← Launches backend server on port 5000
├── frontend/                     ← React interface for user interaction
│   ├── src/                      ← App.jsx, QACard, MathText, styling
│   ├── public/                   ← Static assets
│   └── webpack.config.js         ← Webpack setup for bundling
├── scripts/                      ← Python scripts for QA generation + RAG
│   ├── config.py
│   ├── qa_rule_based_generator.py
│   ├── ai_based_generator.py
│   ├── build_faiss_index_core.py
│   └── rag_rag_engine.py
├── materials/                    ← Processed files
│   ├── raw/                      ← Input PDFs
│   ├── jsonl/                    ← QA data
│   └── embeddings/               ← FAISS index and ID maps
├── report/                       ← Final project report and figures
├── venv/                         ← Python virtual environment
└── README.md

```

## Setup

### 1. Python Environment
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Backend & Frontend
```bash
cd backend-node
npm install

cd ../frontend
npm install
```

---

## Run the System

### Start backend
```bash
cd backend-node
node server.js
```

### Start frontend
```bash
cd frontend
npm start
```

Frontend runs at `http://localhost:3000`.

---

## Configuration

Core paths and model settings are defined in:

```
scripts/config.py
```

Example:
```python
RAW_PDF_DIR = "../materials/raw"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
OLLAMA_MODEL = "gemma3:latest"
```

---

## Notes

- Users should place their own PDFs under `materials/raw/`
- Local LLM inference is supported via **Ollama**
- Retrieval is currently paragraph-level

---

## License

MIT License — for educational and research use.

