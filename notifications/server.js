// server.js — Real-time notification service using Socket.IO
// Runs separately from the Python backend on port 3001

const express = require("express");
const http    = require("http");
const { Server } = require("socket.io");
const cors    = require("cors");

const app    = express();
const server = http.createServer(app);

// Allow frontend to connect
const io = new Server(server, {
  cors: { origin: "*", methods: ["GET", "POST"] }
});

app.use(cors());
app.use(express.json());

// ── Track connected clients ────────────────────
let connectedClients = 0;

io.on("connection", (socket) => {
  connectedClients++;
  console.log(`✅ Client connected. Total: ${connectedClients}`);

  socket.on("disconnect", () => {
    connectedClients--;
    console.log(`❌ Client disconnected. Total: ${connectedClients}`);
  });
});

// ── REST endpoint called by Python backend ─────
// When PO status changes, Python POSTs here
// and we broadcast to all connected browsers
app.post("/notify", (req, res) => {
  const { reference_no, old_status, new_status } = req.body;

  const message = {
    reference_no,
    old_status,
    new_status,
    timestamp: new Date().toISOString()
  };

  console.log(`📢 Broadcasting PO update:`, message);

  // Send to ALL connected browser clients
  io.emit("po_status_update", message);

  res.json({ success: true, clients_notified: connectedClients });
});

// ── Health check ───────────────────────────────
app.get("/", (req, res) => {
  res.json({
    status  : "Notification server running",
    clients : connectedClients,
    port    : 3001
  });
});

server.listen(3001, () => {
  console.log("🔔 Notification server running on http://localhost:3001");
});