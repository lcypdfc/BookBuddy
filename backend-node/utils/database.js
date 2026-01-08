const { MongoClient } = require("mongodb");
require("dotenv").config();

const uri = process.env.MONGODB_URI;
const dbName = process.env.DB_NAME || "ragdb";

let client;
let db;

async function connectToDatabase() {
  if (!client || !client.topology || !client.topology.isConnected()) {
    client = new MongoClient(uri, { useNewUrlParser: true, useUnifiedTopology: true });
    await client.connect();
    db = client.db(dbName);
    console.log("[MongoDB] Connected to", dbName);
  }
  return db;
}

module.exports = {
  connectToDatabase,
};
