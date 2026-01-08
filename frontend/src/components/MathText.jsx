// src/components/MathText.jsx
import React from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

export default function MathText({ content }) {
  return (
    <ReactMarkdown
      children={content}
      remarkPlugins={[remarkMath]}
      rehypePlugins={[rehypeKatex]}
      components={{
        p: ({ children }) => (
          <p style={{ whiteSpace: "pre-wrap", fontSize: "16px", lineHeight: "1.6" }}>
            {children}
          </p>
        )
      }}
    />
  );
}
