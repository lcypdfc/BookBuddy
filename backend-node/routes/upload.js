const express = require("express");
const multer = require("multer");
const path = require("path");
const runPython = require("../utils/runPython");
const fs = require("fs");

const router = express.Router();
const upload = multer({ dest: "uploads/" });


router.post("/", upload.single("pdf"), async (req, res) => {
  const file = req.file;
  if (!file) return res.status(400).json({ error: "Missing file" });

  const filename = path.parse(file.originalname).name;
  const base = filename + "_" + Date.now();
  const pdfPath = path.resolve(file.path);
  const jsonlOut = `materials/jsonl/${base}.qa_with_answers.jsonl`;
  const indexOut = `materials/embeddings/faiss_${base}.index`;
  const idMapOut = `materials/embeddings/id_map_${base}.json`;
  const embed_model = req.body?.embedding_model || "all-MiniLM-L6-v2";


  try {
    // await runPython("probability_pipeline_multi.py", [
    //   "--pdf", pdfPath,
    //   "--prefix", base,
    //   "--force"
    // ]);
    const jsonlOut = `materials/jsonl/${base}.qa_with_answers.jsonl`;

    await runPython("qa_rule_based_generator.py", [
    "--pdf", pdfPath,
    "--out", jsonlOut,
    "--chunk_size", "180"
    ]);


    await runPython("build_faiss_index_core.py", [
      jsonlOut,
      embed_model,
      indexOut,
      idMapOut
    ]);

    res.json({ success: true, indexPath: indexOut, idMapPath: idMapOut });
  } catch (err) {
    console.error(err.message);
    res.status(500).json({ error: "Failed to process PDF" });
  }
});

module.exports = router;
