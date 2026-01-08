import React from "react";
import MathText from "./MathText";

export default function QACard({ qa }) {
  return (
    <div className="qa-card">
      <h2 className="question">
        Q: {qa.question}
        {qa.is_fallback && <span className="fallback">(Fallback)</span>}
      </h2>
      <div className="answer">
        <strong>Answer:</strong> <MathText content={qa.answer} />
      </div>
      {qa.context && (
        <div className="context">
          <strong>Context:</strong> <MathText content={qa.context} />
        </div>
      )}
      <p className="meta">
        Model: {qa.model} | Embedding: {qa.embedding_model} | ID: {qa.id}
      </p>
    </div>
  );
}