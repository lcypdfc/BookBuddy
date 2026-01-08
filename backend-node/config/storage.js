const path = require("path");

const ROOT_DIR = path.resolve(__dirname, "..", "..");
const SCRIPT_DIR = path.join(ROOT_DIR, "scripts");
const MATERIALS_DIR = path.join(ROOT_DIR, "materials");

module.exports = { ROOT_DIR, SCRIPT_DIR, MATERIALS_DIR };
