const express = require("express");
const path = require("path");
const fs = require("fs");
const runPython = require("../utils/runPython");
const { MATERIALS_DIR } = require("../config/storage");

const router = express.Router();

router.post("/generate", async (req, res) => {
  const { indexPath, idMapPath, num_topics, model } = req.body;

  // Debug logs for incoming request parameters
  console.log("[GUIDE DEBUG] Request received at /guide/generate");
  console.log("[GUIDE DEBUG] indexPath:", indexPath);
  console.log("[GUIDE DEBUG] idMapPath:", idMapPath);
  console.log("[GUIDE DEBUG] num_topics:", num_topics);
  console.log("[GUIDE DEBUG] model:", model);

  // Validate required parameters
  if (!indexPath || !idMapPath) {
    return res.status(400).json({ error: "Missing indexPath or idMapPath" });
  }

  try {
    // Create a unique output directory inside root-level materials/bookguide
    const outDir = path.join(MATERIALS_DIR, "bookguide", `${Date.now()}`);
    fs.mkdirSync(outDir, { recursive: true });
    console.log("[GUIDE DEBUG] Output directory created:", outDir);

    // Build arguments for the Python script
    const args = [
      "--index_path", indexPath,
      "--id_map", idMapPath,
      "--out_dir", outDir,
      "--num_topics", String(num_topics ?? 10), // ensure 0 is passed as 0, not converted to 10
      "--model", model || "gemma3:latest"
    ];

    const t0 = process.hrtime.bigint();

    // Run Python script to generate the BookGuide
    console.log("[GUIDE DEBUG] Running Python script: generate_book_guide.py");
    const result = await runPython("generate_topics/generate_book_guide.py", args);
    console.log("[GUIDE DEBUG] Python result:", result);

    const t1 = process.hrtime.bigint();
    const totalMs = Number(t1 - t0) / 1e6;
    console.log(`[GUIDE TIMING] generate (end-to-end) in ${totalMs.toFixed(1)} ms; outDir=${outDir}`);

    // Determine the bookguide.json path from Python output
    let bookguidePath = result.bookguide_json || path.join(outDir, "bookguide.json");

    // Normalize and resolve the path to absolute
    if (!path.isAbsolute(bookguidePath)) {
      bookguidePath = path.resolve(__dirname, "..", "..", bookguidePath.replace(/\\/g, "/"));
    }
    console.log("[GUIDE DEBUG] Resolved bookguide.json path:", bookguidePath);

    // Check if the generated bookguide file exists
    if (!fs.existsSync(bookguidePath)) {
      console.error("[GUIDE ERROR] bookguide.json not found at:", bookguidePath);
      return res.status(500).json({ error: "BookGuide JSON not found after generation" });
    }

    // Read and parse the JSON file
    let bookguideData;
    try {
      bookguideData = JSON.parse(fs.readFileSync(bookguidePath, "utf-8"));
      console.log("[GUIDE DEBUG] bookguide.json successfully read and parsed.");
    } catch (jsonErr) {
      console.error("[GUIDE ERROR] Failed to parse bookguide.json:", jsonErr);
      return res.status(500).json({ error: "Failed to parse bookguide.json", detail: jsonErr.message });
    }

    // Attach paths for markdown and plain text files
    bookguideData.markdown_path = path.join(path.dirname(bookguidePath), "bookguide_full.md").replace(/\\/g, "/");
    bookguideData.plain_text_path = path.join(path.dirname(bookguidePath), "bookguide_plain.txt").replace(/\\/g, "/");

    console.log("[GUIDE DEBUG] Markdown path:", bookguideData.markdown_path);
    console.log("[GUIDE DEBUG] Plain text path:", bookguideData.plain_text_path);

    // Return the combined JSON response
    res.json({
      success: true,
      ...bookguideData
    });
  } catch (err) {
    console.error("[Guide Generation Error]", err);
    res.status(500).json({ error: "Failed to generate BookGuide", detail: err.message });
  }
});

module.exports = router;
