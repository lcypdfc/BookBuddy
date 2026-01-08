const { spawn } = require("child_process");
const path = require("path");

/**
 * Runs a Python script with specified arguments.
 * 
 * @param {string} scriptName - Name of the Python script (e.g. 'rag_ollama_gemma3.py')
 * @param {string[]} args - Arguments to pass to the script (e.g. ['--query', 'What is AI?'])
 * @returns {Promise<string>} - Resolves with stdout or rejects with error
 */
module.exports = function runPython(scriptName, args = []) {
  return new Promise((resolve, reject) => {
    const scriptPath = path.resolve(__dirname, "../../scripts", scriptName);
    console.log(" Running command:", "py", "-3", scriptPath, ...args);
    
    const py = spawn("py", ["-3", scriptPath, ...args], {
      cwd: path.resolve(__dirname, "../../"),
    });

    let stdout = "";
    let stderr = "";

    py.stdout.on("data", (data) => {
      console.log("STDOUT:", data.toString());
      stdout += data.toString();
    });

    py.stderr.on("data", (data) => {
      console.error("STDERR:", data.toString());
      stderr += data.toString();
    });

    py.on("close", (code) => {
      if (code === 0) {
        try {
          const lines = stdout.trim().split("\n");
          const lastLine = lines[lines.length - 1];
          const parsed = JSON.parse(lastLine); 
          // resolve(parsed.answer || "(No answer)");
          resolve(parsed);
        } catch (e) {
          console.warn("Failed to parse JSON from Python:", e.message);
          resolve(stdout.trim()); // fallback to raw output
        }
      } else {
        reject(new Error(stderr || `Python script exited with code ${code}`));
      }
    });
  });
};
