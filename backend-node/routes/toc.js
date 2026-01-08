const express = require("express");
const router = express.Router();
const path = require("path");
const fs = require("fs");
const { spawn } = require("child_process");
const { MATERIALS_DIR } = require("../config/storage");

// Root and script directories
const ROOT_DIR = path.resolve(__dirname, "..", "..");
const SCRIPT_DIR = path.join(ROOT_DIR, "scripts", "extract_lines");

// Materials subdirectories
const RAW_PDF_DIR = path.join(MATERIALS_DIR, "raw");
const TOC_DIR = path.join(MATERIALS_DIR, "toc");

/**
 * POST /toc/toc
 * Extract raw TOC lines from specified page range and refine them via LLM.
 */
router.post("/toc", (req, res) => {
  const { filename, tocStartPage, tocEndPage } = req.body;
  const pdfBase = path.basename(filename, path.extname(filename));
  const pdfPath = path.join(RAW_PDF_DIR, filename);

  // Output file paths
  const tocTxtPath = path.join(TOC_DIR, `${pdfBase}.toc.txt`);
  const tocJsonlPath = path.join(TOC_DIR, `${pdfBase}.toc.jsonl`);
  const tocCleanedPath = path.join(TOC_DIR, `${pdfBase}.toc.cleaned.md`);

  // Python scripts
  const extractScript = path.join(SCRIPT_DIR, "extract_toc_raw_lines.py");
  const refineScript = path.join(SCRIPT_DIR, "toc_ollama_llm_refine.py");

  // Ensure TOC directory exists
  fs.mkdirSync(TOC_DIR, { recursive: true });

  // Step 1: Extract raw TOC lines
  const extract = spawn("python", [
    extractScript,
    "--pdf",
    pdfPath,
    "--toc_start",
    String(tocStartPage),
    "--toc_end",
    String(tocEndPage),
    "--out_txt",
    tocTxtPath,
    "--out_jsonl",
    tocJsonlPath,
  ]);

  extract.stderr.on("data", (data) => {
    console.error("[TOC-EXTRACT ERROR]", data.toString());
  });

  extract.on("close", (code) => {
    if (code !== 0) {
      return res.json({ success: false, message: "TOC raw extraction failed." });
    }

    // Step 2: Refine TOC using LLM
    const refine = spawn("python", [
      refineScript,
      "--toc_file",
      tocJsonlPath,
      "--out",
      tocCleanedPath,
    ]);

    refine.stderr.on("data", (data) => {
      console.error("[TOC-REFINE ERROR]", data.toString());
    });

    refine.stdout.on("data", (data) => {
      try {
        const result = JSON.parse(data.toString());
        if (result.success) {
          const cleanedTOC = fs.readFileSync(tocCleanedPath, "utf-8");
          res.json({ success: true, cleanedTOC });
        } else {
          res.json({ success: false, message: "TOC cleaning failed" });
        }
      } catch (err) {
        res.json({ success: false, message: "Invalid JSON from TOC refine" });
      }
    });
  });
});

/**
 * POST /toc/genIntro
 * Generate an introduction for each TOC section using RAG-based pipeline.
 */
router.post("/genIntro", (req, res) => {
  const { tocPath, outPath, indexPath, idMapPath, embedModel, llmModel } = req.body;

  const scriptPath = path.join(SCRIPT_DIR, "generate_toc_intros_rag.py");

  console.log("[TOC-intro] TOC RAG intro generation started");

  const proc = spawn(
    "python",
    [
      scriptPath,
      "--toc_md",
      path.relative(process.cwd(), tocPath),
      "--out",
      path.relative(process.cwd(), outPath),
      "--index",
      path.relative(process.cwd(), indexPath),
      "--id_map",
      path.relative(process.cwd(), idMapPath),
      "--embed_model",
      embedModel,
      "--llm_model",
      llmModel,
    ],
    {
      cwd: ROOT_DIR,
    }
  );

  let output = "";

  proc.stdout.on("data", (data) => {
    output += data.toString();
  });

  proc.on("close", (code) => {
    try {
      const lines = output.trim().split("\n");
      const lastLine = lines[lines.length - 1];
      const result = JSON.parse(lastLine);
      res.json(result);
    } catch (e) {
      console.warn("[TOC-intro PARSE ERROR]", e.message);
      res.json({ success: false, message: "Failed to parse output." });
    }
  });

  proc.stderr.on("data", (data) => {
    console.error("[TOC-intro ERROR]", data.toString());
  });
});

module.exports = router;
