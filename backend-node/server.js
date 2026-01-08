const express = require("express");
const cors = require("cors");
const app = express();
const askRoute = require("./routes/ask");
const uploadRoute = require("./routes/upload");
const historyRoute = require("./routes/history");

require("dotenv").config(); 
const mongoose = require("mongoose");

const mongoUri = process.env.MONGODB_URI;
const dbName = process.env.DB_NAME;

mongoose
  .connect(mongoUri, { dbName })
  .then(() => console.log(`[MongoDB] Connected to database: ${dbName}`))
  .catch((err) => console.error("[MongoDB] Connection error:", err));



app.use(cors());
app.use(express.json());
app.use("/ask", askRoute);
app.use("/upload", uploadRoute);
app.use("/history", historyRoute);

const PORT = 5000;
app.listen(PORT, () => {
  console.log(`Server listening on http://localhost:${PORT}`);
});
