import { Conversation } from "https://esm.sh/@elevenlabs/client";

// DOM Elements
const callBtn = document.getElementById("call-btn");
const hangupBtn = document.getElementById("hangup-btn");
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");
const agentStateLabel = document.getElementById("agent-state-label");
const orbVisualizer = document.getElementById("orb-visualizer");
const visualizerWrapper = document.querySelector(".visualizer-wrapper");
const callTimer = document.getElementById("call-timer");
const transcriptContainer = document.getElementById("transcript-container");
const transcriptPlaceholder = document.getElementById("transcript-placeholder");
const footerAgentId = document.getElementById("footer-agent-id");
const headerPhoneNumber = document.getElementById("header-phone-number");
const heroPhoneNumber = document.getElementById("hero-phone-number");
const patientsTableBody = document.getElementById("patients-table-body");
const refreshPatientsBtn = document.getElementById("refresh-patients-btn");

let activeConversation = null;
let timerInterval = null;
let secondsElapsed = 0;
let messages = [];
let currentAgentId = "";

// Format seconds into MM:SS
function formatTime(totalSeconds) {
  const mins = Math.floor(totalSeconds / 60);
  const secs = totalSeconds % 60;
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

function startTimer() {
  secondsElapsed = 0;
  callTimer.textContent = "00:00";
  timerInterval = setInterval(() => {
    secondsElapsed++;
    callTimer.textContent = formatTime(secondsElapsed);
  }, 1000);
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

function appendTranscript(source, text) {
  if (transcriptPlaceholder) {
    transcriptPlaceholder.classList.add("hidden");
  }

  const bubble = document.createElement("div");
  bubble.className = `msg-bubble ${source === "user" ? "msg-user" : "msg-agent"}`;

  const sender = document.createElement("div");
  sender.className = "msg-sender";
  sender.textContent = source === "user" ? "Caller" : "Agent";

  const content = document.createElement("div");
  content.className = "msg-content";
  content.textContent = text;

  bubble.appendChild(sender);
  bubble.appendChild(content);
  transcriptContainer.appendChild(bubble);

  // Auto scroll
  transcriptContainer.scrollTop = transcriptContainer.scrollHeight;

  messages.push({ source, text, timestamp: new Date().toISOString() });
}

function updateVisualizer(state) {
  orbVisualizer.classList.remove("speaking", "listening");
  statusDot.classList.remove("active", "speaking", "danger");

  if (state === "speaking") {
    orbVisualizer.classList.add("speaking");
    statusDot.classList.add("speaking");
    agentStateLabel.textContent = "Agent is speaking...";
    statusText.textContent = "Agent Speaking";
  } else if (state === "listening") {
    orbVisualizer.classList.add("listening");
    statusDot.classList.add("active");
    agentStateLabel.textContent = "Listening to you...";
    statusText.textContent = "Listening";
  } else if (state === "connected") {
    statusDot.classList.add("active");
    agentStateLabel.textContent = "Connected! State your name to begin.";
    statusText.textContent = "Connected";
  } else if (state === "connecting") {
    agentStateLabel.textContent = "Connecting to intake agent...";
    statusText.textContent = "Connecting...";
  } else {
    agentStateLabel.textContent = "Tap to start patient registration call";
    statusText.textContent = "Ready to Call";
  }
}

// Fetch and display registered patients
async function loadPatients() {
  try {
    const res = await fetch("/patients");
    if (!res.ok) throw new Error("Failed to load patients");
    const envelope = await res.json();
    const patients = envelope.data || [];

    if (patients.length === 0) {
      patientsTableBody.innerHTML = `<tr><td colspan="7" class="loading-cell">No patients registered yet. Complete a call to register.</td></tr>`;
      return;
    }

    patientsTableBody.innerHTML = patients.map(p => `
      <tr>
        <td>
          <span class="patient-name-cell">${escapeHtml(p.first_name)} ${escapeHtml(p.last_name)}</span>
          <span class="patient-id-badge">ID: ${escapeHtml(p.patient_id.substring(0, 8))}...</span>
        </td>
        <td>${escapeHtml(p.date_of_birth)}</td>
        <td>${escapeHtml(p.sex)}</td>
        <td>${escapeHtml(p.phone_number)}</td>
        <td>${escapeHtml(p.city)}, ${escapeHtml(p.state)} ${escapeHtml(p.zip_code)}</td>
        <td>${escapeHtml(p.insurance_provider || "Self-Pay / None")}</td>
        <td>${new Date(p.created_at).toLocaleDateString()}</td>
      </tr>
    `).join("");

  } catch (err) {
    console.error("Error loading patients:", err);
    patientsTableBody.innerHTML = `<tr><td colspan="7" class="loading-cell" style="color: #ef4444;">Error loading patient records.</td></tr>`;
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// Check backend agent status on load
async function checkAgentStatus() {
  try {
    const res = await fetch("/api/agent/info");
    if (!res.ok) throw new Error("Backend not ready");
    const data = await res.json();
    currentAgentId = data.agent_id;
    footerAgentId.textContent = data.agent_id;
    if (data.phone_number) {
      if (headerPhoneNumber) headerPhoneNumber.textContent = data.phone_number;
      if (heroPhoneNumber) heroPhoneNumber.textContent = data.phone_number;
    }
  } catch (err) {
    console.error("Failed to fetch agent info:", err);
    footerAgentId.textContent = "Unable to connect to backend";
  }
}

// Start Call
async function startCall() {
  try {
    callBtn.disabled = true;
    callBtn.querySelector("span").textContent = "Requesting Access...";
    updateVisualizer("connecting");

    // Request microphone access
    await navigator.mediaDevices.getUserMedia({ audio: true });

    // Determine connection options (Signed URL with fallback to Agent ID)
    let sessionOptions = {};
    callBtn.querySelector("span").textContent = "Connecting...";

    try {
      const res = await fetch("/api/agent/signed-url");
      if (res.ok) {
        const { signed_url } = await res.json();
        sessionOptions = { signedUrl: signed_url };
        console.log("Using authenticated signed URL from backend.");
      } else {
        const errData = await res.json().catch(() => ({}));
        console.warn("Signed URL unavailable, falling back to direct agentId connection:", errData.detail);
        sessionOptions = { agentId: currentAgentId };
      }
    } catch (e) {
      console.warn("Signed URL fetch failed, falling back to agentId:", e);
      sessionOptions = { agentId: currentAgentId };
    }

    if (!sessionOptions.signedUrl && !sessionOptions.agentId) {
      throw new Error("No agent ID or signed URL available. Check backend .env configuration.");
    }

    // Start ElevenLabs Conversational Session
    activeConversation = await Conversation.startSession({
      ...sessionOptions,
      onConnect: ({ conversationId }) => {
        console.log("Connected to ElevenLabs session:", conversationId);
        visualizerWrapper.classList.add("active-call");
        updateVisualizer("connected");
        startTimer();

        callBtn.classList.add("hidden");
        callBtn.disabled = false;
        callBtn.querySelector("span").textContent = "Start Voice Call";
        hangupBtn.classList.remove("hidden");
      },
      onDisconnect: () => {
        console.log("Disconnected from ElevenLabs session");
        endCallUI();
      },
      onError: (err) => {
        console.error("ElevenLabs error:", err);
        alert(`Call error: ${err?.message || err}`);
        endCallUI();
      },
      onModeChange: (data) => {
        const mode = typeof data === "object" ? data.mode : data;
        updateVisualizer(mode);
      },
      onStatusChange: (data) => {
        const status = typeof data === "object" ? data.status : data;
        console.log("Status change:", status);
      },
      onMessage: (data) => {
        console.log("Message received:", data);
        if (data && data.message) {
          appendTranscript(data.source || "ai", data.message);
        }
      }
    });

  } catch (err) {
    console.error("Failed to start call:", err);
    alert(`Could not start call: ${err.message}`);
    endCallUI();
  }
}

// End Call
async function endCall() {
  if (activeConversation) {
    try {
      await activeConversation.endSession();
    } catch (e) {
      console.warn("Error while ending session:", e);
    }
  }
  endCallUI();
}

function endCallUI() {
  stopTimer();
  visualizerWrapper.classList.remove("active-call");
  updateVisualizer("idle");

  callBtn.classList.remove("hidden");
  callBtn.disabled = false;
  callBtn.querySelector("span").textContent = "Start Voice Call";
  hangupBtn.classList.add("hidden");

  // Log summary to backend if messages were exchanged
  if (messages.length > 0) {
    const transcriptText = messages.map(m => `${m.source}: ${m.text}`).join("\n");
    fetch("/api/agent/session-log", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        duration_seconds: secondsElapsed,
        transcript: transcriptText,
        summary: `Call completed with ${messages.length} messages exchanged.`
      })
    }).catch(e => console.warn("Failed to log session:", e));
  }

  // Refresh patients table in case registration occurred during call
  setTimeout(loadPatients, 1200);

  activeConversation = null;
}

// Event Listeners
callBtn.addEventListener("click", startCall);
hangupBtn.addEventListener("click", endCall);
if (refreshPatientsBtn) {
  refreshPatientsBtn.addEventListener("click", loadPatients);
}

// Initialize
checkAgentStatus();
loadPatients();
