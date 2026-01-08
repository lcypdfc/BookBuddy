import React, { useState, useEffect } from "react";
import QACard from "./components/QACard";
import MathText from "./components/MathText";
import "./style.css";
import { v4 as uuidv4 } from "uuid";

export default function MainApp({ userId, setUserId }) {
  const [qas, setQas] = useState([]);
  const [question, setQuestion] = useState("");
  const [file, setFile] = useState(null);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [indexPath, setIndexPath] = useState("");
  const [idMapPath, setIdMapPath] = useState("");
  const [pdfName, setPdfName] = useState("");
  const [uploading, setUploading] = useState(false);
  const [qaList, setQaList] = useState([]);
  const [llmModel, setLlmModel] = useState("gemma3:latest");
  const [embeddingModel, setEmbeddingModel] = useState("all-MiniLM-L6-v2");

  const [sessionId, setSessionId] = useState(() => {
    const saved = localStorage.getItem("sessionId");
    if (saved) return saved;
    const newId = uuidv4();
    localStorage.setItem("sessionId", newId);
    return newId;
  });

  useEffect(() => {
    if (sessionId && userId) {
      fetch(`http://localhost:5000/history?session_id=${sessionId}&user_id=${userId}`)
        .then((res) => res.json())
        .then((data) => {
          if (Array.isArray(data.history)) {
            setQaList(data.history);
          }
        })
        .catch((err) => {
          console.warn("Failed to load history:", err);
        });
    }
  }, [sessionId, userId]);

  const handleUpload = () => {
    setUploading(true);
    const formData = new FormData();
    formData.append("pdf", file);
    formData.append("embedding_model", embeddingModel);

    fetch("http://localhost:5000/upload", {
      method: "POST",
      body: formData,
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setIndexPath(data.indexPath);
          setIdMapPath(data.idMapPath);
          alert("Upload and processing succeeded!");
        } else {
          alert("Failed to process PDF.");
        }
      })
      .catch((err) => {
        console.error("Upload error:", err);
        alert("Upload failed: " + err.message);
      })
      .finally(() => {
        setUploading(false);
      });
  };

  const handleAsk = () => {
    if (!userId || !userId.trim()) {
      alert("Please enter your User ID before asking questions.");
      return;
    }

    setAnswer("...thinking...");
    fetch("http://localhost:5000/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        indexPath,
        idMapPath,
        llm_model: llmModel,
        embedding_model: embeddingModel,
        session_id: sessionId,
        user_id: userId
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        const cleanAnswer = (data.answer || "").trim() || "(No answer returned)";
        setAnswer(cleanAnswer);
        setQaList((prev) => [
          ...prev,
          {
            question,
            answer: data.answer.trim(),
            model: data.model,
            embedding_model: data.embedding_model,
            id: Date.now()
          }
        ]);
      })
      .catch((err) => {
        console.error("Fetch error:", err);
        setAnswer("(Error: Failed to fetch answer)");
      });
  };

  return (
    <div className="container">
      <h1 className="main-title">Question-Answer Dataset Viewer (RAG)</h1>
            <button
        style={{ float: "right", background: "#c33", color: "white" }}
        onClick={() => {
          localStorage.removeItem("userId");
          window.location.reload();
        }}
      >
        Logout
      </button>

      <div style={{ marginBottom: "16px" }}>
        <label><strong>User ID:</strong></label>
        <input
          type="text"
          className="custom-input"
          value={userId}
          onChange={(e) => {
            const value = e.target.value.trim();
            setUserId(value);
            localStorage.setItem("userId", value);
          }}
          placeholder="Enter your name or ID"
        />
      </div>


 {/* Upload section */}
    <div className="upload-section">
      <label htmlFor="file-upload" className="custom-button">
        Choose PDF
      </label>
      <input
        id="file-upload"
        type="file"
        style={{ display: "none" }}
        onChange={(e) => {
          const selectedFile = e.target.files[0];
          console.log("File selected:", selectedFile);
          setFile(selectedFile);
          if (selectedFile) setPdfName(selectedFile.name);
        }}
      />
      <button
        onClick={handleUpload}
        className="custom-button"
        disabled={!file}
      >
        Upload
      </button>
      {file && (
        <span style={{ marginLeft: "10px" }}>{file.name}</span>
      )}
      {uploading && (
        <p style={{ marginTop: "10px", color: "#0b486b", fontStyle: "italic" }}>
          Uploading and processing PDF...
        </p>
      )}
    </div>

<div
  style={{
    display: "flex",
    alignItems: "center",
    gap: "20px",
    margin: "20px 0"
  }}
>
  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
    <label style={{ fontWeight: "bold" }}>Embedding:</label>
    <select
      value={embeddingModel}
      onChange={(e) => setEmbeddingModel(e.target.value)}
      className="custom-select"
    >
      <option value="all-MiniLM-L6-v2">MiniLM</option>
      <option value="bge-small-en-v1.5">BGE-small</option>
      <option value="intfloat/e5-base-v2">E5-base</option>
    </select>
  </div>

  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
    <label style={{ fontWeight: "bold" }}>LLM Model:</label>
    <select
      value={llmModel}
      onChange={(e) => setLlmModel(e.target.value)}
      className="custom-select"
    >
      <option value="gemma3:latest">Gemma 3B</option>
      <option value="llama3:8b">LLaMA 3 8B</option>
      <option value="gpt-3.5-turbo">GPT-3.5</option>
    </select>
  </div>
</div>


      {/* Ask */}
      <div className="ask-section">
        <input
          type="text"
          className="custom-input"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Type your question..."
          disabled={loading}
        />
        <button
          onClick={handleAsk}
          className="custom-button"
          disabled={loading || !question.trim()}
        >
          {loading ? "Asking..." : "Ask"}
        </button>
      </div>

        {indexPath ? (
          <p style={{ color: "#0b486b", marginTop: "-10px" }}>
            RAG Mode: <strong>{pdfName.replace(/_/g, " ")}</strong>
          </p>
        ) : (
          <p style={{ color: "#888", marginTop: "-10px" }}>
            Zero-shot: No uploaded material
          </p>
        )}

      {/* Answer or Loading */}
      {loading && (
        <div className="qa-card loading">
          <p>Generating answer...</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="qa-card error">
          <p style={{ color: "red" }}>{error}</p>
        </div>
      )}

      {/* Answer */}
      {!loading && answer && (
        <div className="qa-card">
          <h2 className="question">Q: {question}</h2>
        {/* <div className="answer">
          <strong>Answer:</strong>
          <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
            {answer}
          </pre>
        </div> */}
        <div className="answer">
          <strong>Answer:</strong>
          <MathText content={answer} />
        </div>
        </div>
      )}

      {qaList.length > 0 && (
        <div className="qa-history">
          <h2 style={{ color: "#1a3d7c" }}>History</h2>
          {qaList.map((qa) => (
            <QACard key={qa.id} qa={qa} />
          ))}
        </div>
      )}
    </div>
  );
}
