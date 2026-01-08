const express = require("express");
const router = express.Router();
const { connectToDatabase } = require("../utils/database");

router.get("/", async (req, res) => {
  const { user_id, session_id } = req.query;

  if (!user_id || !session_id) {
    return res.status(400).json({ error: "Missing user_id or session_id" });
  }

  try {
    const db = await connectToDatabase();
    const logs = db.collection("conversations");

    const history = await logs
      .find({ user_id, session_id })
      .sort({ timestamp: 1 })
      .toArray();

    const qaPairs = history.map(item => ({
      question: item.question,
      answer: item.answer,
      model: item.model,
      embedding_model: item.embedding_model,
      id: item._id.toString()
    }));

    res.json({ history: qaPairs });
  } catch (err) {
    console.error("History retrieval error:", err);
    res.status(500).json({ error: "Failed to fetch history" });
  }
});

module.exports = router;
