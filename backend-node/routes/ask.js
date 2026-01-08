const express = require("express");
const router = express.Router();
const runPython = require("../utils/runPython");
const { connectToDatabase } = require("../utils/database");

router.post("/", async (req, res) => {
  const {
    question,
    indexPath,
    idMapPath,
    llm_model,
    embedding_model,
    session_id,
    user_id
  } = req.body;

  if (!question || typeof question !== "string") {
    return res.status(400).json({ error: "Missing or invalid question" });
  }

  const args = ["--query", question];

  if (indexPath && idMapPath) {
    args.push("--index", indexPath);
    args.push("--id_map", idMapPath);
  }
  if (llm_model) args.push("--llm_model", llm_model);
  if (embedding_model) args.push("--embed_model", embedding_model);

  try {
    const output = await runPython("rag_rag_engine.py", args);
    const { answer, llm_model: modelUsed, embed_model: embedUsed } = output;

    if (user_id && session_id) {
      const db = await connectToDatabase();
      const logs = db.collection("conversations");
      await logs.insertOne({
        user_id,
        session_id,
        question,
        answer: answer || "(No answer)",
        model: modelUsed,
        embedding_model: embedUsed,
        timestamp: new Date()
      });
    }

    res.json({
      answer: answer || "(No answer)",
      model: modelUsed || "unknown",
      embedding_model: embedUsed || "unknown"
    });
  } catch (err) {
    console.error("Python script error:", err.message);
    res.status(500).json({ error: "Internal error from Python script", detail: err.message });
  }
});

module.exports = router;