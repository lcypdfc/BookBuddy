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

---

## Configuration

All paths and model parameters are defined in `scripts/config.py`:

```python
RAW_PDF_DIR = "../materials/raw"
JSONL_DIR = "../materials/jsonl"
EMBEDDING_DIR = "../materials/embeddings"
MODEL_NAME = "all-MiniLM-L6-v2"
OLLAMA_MODEL = "gemma3:latest"
```

---

## Quick Start (Frontend + Backend)

### 1. Launch Python environment

Make sure your Python environment is activated and all dependencies are installed (faiss-cpu, sentence-transformers, PyMuPDF, etc.).

---

### 2. 2. Start backend server

```bash
cd backend-node
node server.js
```

This launches the UI on http://localhost:3000, allowing users to:
- Upload a PDF
- Select embedding model & LLM
- Ask questions and get RAG-based answers with math formatting
---

## Python Scripts: Usage Examples
### Generate QA pairs from PDF (rule-based)
```bash
python scripts/qa_rule_based_generator.py \
  --pdf materials/raw/mybook.pdf \
  --out materials/jsonl/mybook.qa_with_answers.jsonl
```

### Build FAISS index
```bash
python scripts/build_faiss_index_core.py \
  materials/jsonl/mybook.qa_with_answers.jsonl \
  all-MiniLM-L6-v2 \
  materials/embeddings/faiss_mybook.index \
  materials/embeddings/id_map_mybook.json
```
---

### Run question-answering (RAG engine)
```bash
python scripts/rag_rag_engine.py \# BookBuddy: RAG-Based QA System for Educational PDFs

BookBuddy is a modular pipeline for building a Retrieval-Augmented Generation (RAG) system using PDF textbooks. It allows users to upload academic material, generate QA datasets, and interact with the content through an AI model with contextual memory.

---

## Features

- Upload textbook PDFs and convert them to QA datasets
- Query content using RAG powered by local LLMs (e.g., via Ollama)
- Support for multiple embedding models (MiniLM, E5, etc.)
- Chat session memory using MongoDB Atlas
- Persistent session and user identification across page reloads


---

## Installation Instructions

### 1. Backend Setup

1. Navigate to the backend directory:

   ```bash
   cd backend-node
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Create your environment file:

   ```bash
   cp .env.example .env
   ```

4. Edit `.env` and fill in your MongoDB Atlas URI:

   ```env
   MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
   DB_NAME=ragdb
   ```

5. Start the backend server:

   ```bash
   node server.js
   ```

The backend exposes:

- `POST /upload` – Process PDF and generate embeddings
- `POST /ask` – Ask a question with or without RAG
- `GET /history` – Load QA history for a user/session

---

### 2. Frontend Setup

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Install frontend dependencies:

   ```bash
   npm install
   ```

3. Start the development server:

   ```bash
   npm start
   ```

The frontend will run at `http://localhost:3000` by default.

---

## MongoDB Setup (Atlas)

- Create a free MongoDB Atlas cluster at https://cloud.mongodb.com
- Create a new database named `ragdb` (or use the one specified in `.env`)
- Create a user with read/write access to that database
- Whitelist your IP address in the security settings
- Use the connection string in your `.env` file

No manual collection creation is needed; `conversations` collection will be auto-created when users interact.

---

## Notes

- LLM queries use a local Ollama model by default; you can adjust model settings via the frontend dropdown
- Only paragraph-level RAG is currently implemented; sentence-level retrieval is under development
- Ensure your Ollama backend is running before starting the full stack

---

## License

This project is for academic and educational purposes only.
  --query "What is a random variable?" \
  --index materials/embeddings/faiss_mybook.index \
  --id_map materials/embeddings/id_map_mybook.json \
  --llm_model llama3:8b \
  --embed_model intfloat/e5-base-v2
```

## Features
- Selectable LLM and embedding models (MiniLM, BGE, E5, etc.)
- Local model inference using Ollama or external APIs
- React frontend with math-rendered answers using LaTeX (KaTeX)
- RAG pipeline: PDF → QA → FAISS index → semantic retrieval + LLM generation
- Fully modular and customizable

## License
MIT License. 
