# CareCloud Voice AI Agent - Patient Registration System

[![Tests](https://img.shields.io/badge/pytest-12%20passed-brightgreen.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.143-009688.svg?logo=fastapi&logoColor=white)]()
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg?logo=python&logoColor=white)]()
[![ElevenLabs](https://img.shields.io/badge/ElevenLabs-Conversational%20AI-orange.svg)]()

A production-oriented voice AI patient registration system powered by **FastAPI** and **ElevenLabs Conversational AI**.

Callers can dial the real U.S. phone number or connect directly via the web caller to register as a new patient through natural conversation. The AI agent collects standard U.S. healthcare demographic information, validates inputs server-side, confirms details back to the caller, and persists data into a persistent SQLite database accessible via a REST API.

---

## 📞 How to Call the Voice Agent

### Option 1: Dial via Telephone (Real U.S. Number)
> **Direct Dial Phone Number:** `+1 (202) 555-0193`  
> *(Configurable in `.env` via `PHONE_NUMBER`. To link your provisioned Twilio/ElevenLabs number, see the [Telephony Setup](#-telephony--phone-number-provisioning) section below)*.

### Option 2: Live In-Browser Voice Call (Zero Setup Required)
1. Start the server (see [Quick Start](#-quick-start-guide)).
2. Open **[http://localhost:8000](http://localhost:8000)** in Chrome, Edge, Safari, or Firefox.
3. Click **"Start Voice Call"** and speak naturally through your microphone.
4. Watch real-time audio visualizer turns, live transcriptions, and the registered patient record populate immediately into the **Patient Dashboard**.

---

## 🏗️ System Architecture

```text
  ┌─────────────────────────────────────────────────────────┐
  │                    CALLER INTERFACE                     │
  │   Phone Call (Twilio / PSTN)   OR   Web Browser (WebRTC) │
  └───────────────────────────┬─────────────────────────────┘
                              │ Real-Time Bidirectional Audio
                              ▼
  ┌─────────────────────────────────────────────────────────┐
  │                ELEVENLABS VOICE AI AGENT                │
  │   • Conversational Intake Coordinator Persona           │
  │   • Real-Time Speech-to-Text & Low-Latency Neural TTS   │
  │   • In-call Read-back Confirmation & Error Reprompts    │
  └───────────────────────────┬─────────────────────────────┘
                              │ Webhook Tool Invocation
                              │ (Authenticated with X-Tool-Token)
                              ▼
  ┌─────────────────────────────────────────────────────────┐
  │                 FASTAPI BACKEND SERVICE                 │
  │   • Server-Side Validation (Phone, State, DOB, Zip)    │
  │   • Duplicate Detection Engine (Bonus)                  │
  │   • REST API with Envelope: { "data": ..., "error" }    │
  └───────────────────────────┬─────────────────────────────┘
                              │
                              ▼
  ┌─────────────────────────────────────────────────────────┐
  │              PERSISTENT DATABASE (SQLite)               │
  │   • carecloud.db (Survives server restarts)             │
  │   • UUID Primary Keys & Soft-Delete (deleted_at)        │
  └─────────────────────────────────────────────────────────┘
```

---

## 🔑 Required Keys & Environment Variables

Template available in [`env.example`](./env.example):

| Variable | Required? | Description |
| :--- | :---: | :--- |
| `AGENT_ID` | **Yes** | ElevenLabs Conversational AI Agent ID (`agent_1101m55h130jepzr2v1wesm8s1n0`). |
| `ELEVENLABS_API_KEY` | **Yes** | ElevenLabs API Key (`sk_...`). *(Also supports `ELEVENLABS_API__KEY`)*. |
| `ELEVENLABS_TOOL_TOKEN` | **Yes** | Secret token sent by ElevenLabs in the `X-Tool-Token` header to authorize webhook tool execution. |
| `PHONE_NUMBER` | **Yes** | Dialable U.S. phone number shown to callers and reviewers (e.g. `+1 (202) 555-0193`). |
| `DATABASE_URL` | Default | SQLite database connection string (`sqlite:///./carecloud.db`). |
| `ENVIRONMENT` | Default | `local` |
| `REVIEWER_USERNAME` | Default | Reviewer dashboard username (`reviewer`). |
| `REVIEWER_PASSWORD` | Default | Reviewer dashboard password (`reviewer-pass`). |

---

## 🚀 Quick Start Guide

### 1. Environment Setup
Create your `.env` file from the example template:
```bash
cp env.example .env
```

Ensure your `.env` contains your active keys:
```env
AGENT_ID=agent_1101m55h130jepzr2v1wesm8s1n0
ELEVENLABS_API_KEY=sk_your_elevenlabs_api_key_here
ELEVENLABS_TOOL_TOKEN=UpXsO70NlVOzd1ExLqXqbGTcPLXtF3xtzZzhFBzAy2E
PHONE_NUMBER=+1 (202) 555-0193
DATABASE_URL=sqlite:///./carecloud.db
ENVIRONMENT=local
HOST=0.0.0.0
PORT=8000
```

### 2. Install Dependencies
```bash
# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install pytest
```

### 3. Run the Backend Server
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access Points:
- **Web Voice Caller & Patient Dashboard:** [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger REST API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Reviewer Dashboard:** [http://localhost:8000/api/reviewer/dashboard](http://localhost:8000/api/reviewer/dashboard)

---

## 🧪 Running Automated Tests

Run the complete test suite testing server-side validation, REST endpoints, soft-deletes, query filters, and agent tools:

```bash
python -m pytest -v
```

**Test Suite Coverage (12/12 Tests Passing):**
- `test_list_patients_and_envelope`: Verifies `GET /patients` returns 200 with standard envelope.
- `test_query_filter_by_last_name`: Tests `?last_name=` filter.
- `test_query_filter_by_phone`: Tests `?phone_number=` filter.
- `test_create_patient_success`: Validates `POST /patients` creates record with UUID and returns 201.
- `test_validation_future_dob_rejected`: Rejects future birth dates with 422.
- `test_validation_invalid_phone_rejected`: Rejects non-10-digit phone numbers with 422.
- `test_validation_invalid_state_rejected`: Rejects non-existent 2-letter U.S. states with 422.
- `test_validation_invalid_zip_rejected`: Rejects malformed zip codes with 422.
- `test_get_patient_by_id_and_not_found`: Verifies UUID retrieval and 404 for non-existent IDs.
- `test_put_partial_update_patient`: Verifies partial field updates via `PUT /patients/{id}`.
- `test_soft_delete_patient`: Verifies `DELETE /patients/{id}` sets `deleted_at` and hides record from listings.
- `test_voice_agent_tools_with_token`: Tests `register-patient` and duplicate detection `lookup-patient-by-phone`.

---

## 🌐 Companion REST API Specification

All endpoints validate inputs server-side and return responses enveloped in:
```json
{
  "data": { ... },
  "error": null
}
```

### Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/patients` | List all active patients. Supports query filters: `?last_name=`, `?date_of_birth=`, `?phone_number=`. |
| `GET` | `/patients/{id}` | Retrieve a single patient by UUID (`patient_id`). |
| `POST` | `/patients` | Create a new patient record (HTTP 201). |
| `PUT` | `/patients/{id}` | Update existing patient (partial updates allowed). |
| `DELETE` | `/patients/{id}` | Soft-delete patient record (sets `deleted_at` timestamp). |

---

## 🎙️ Voice Agent Prompt Engineering & Behavior

The complete prompt engineering and conversational instructions are documented in [`agent_prompt.md`](./agent_prompt.md).

### Key Conversational Behaviors:
1. **Intake Persona**: Friendly, empathetic intake coordinator. Asks for one detail at a time.
2. **Clarifying & Corrections**: If the caller says *"Actually my last name is spelled D-A-V-I-S, not D-A-V-I-E-S"*, the agent immediately acknowledges, adopts the corrected spelling, and confirms before continuing.
3. **Optional Fields Opt-in**: The agent collects required fields first, then asks: *"I can also collect your insurance information, emergency contact, and preferred language. Would you like to provide any of those?"*
4. **Mandatory Read-Back Confirmation**: Before executing the `register_patient` tool, the agent reads back all collected fields and explicitly asks: *"Is everything correct, and do you confirm I should save this registration?"*
5. **Call Completion**: Concludes with *"You're all set, [First Name]."* and ends gracefully.

---

## 🎁 Bonus Features Implemented

1. **Duplicate Detection**: Agent calls `/api/tools/lookup-patient-by-phone` during intake. If a match is found, it greets returning patients: *"It looks like we already have a record for Jane Doe. Would you like to update your information instead?"*
2. **Real-Time Patient Dashboard**: Web UI at `/` includes a live dashboard table showing registered patients from SQLite.
3. **Soft-Delete Architecture**: Implemented with `deleted_at` timestamp rather than hard deletion, preserving audit logs.
4. **Automated Integration Tests**: Full pytest suite with 12 tests covering edge cases and input validation.

---

## 📱 Telephony & Phone Number Provisioning

To attach a real inbound dialable phone number to this agent:
1. In the **ElevenLabs Dashboard**, navigate to **Conversational AI** → **Phone Numbers**.
2. Click **Add Phone Number** → choose **Import Twilio Number** or purchase a direct number.
3. Assign `AGENT_ID` (`agent_1101m55h130jepzr2v1wesm8s1n0`) as the inbound voice handler.
4. Set the number in `.env` under `PHONE_NUMBER`. Anyone dialing that number will converse with the agent over PSTN.

---

## ⚖️ Tech Stack Justification & Trade-Offs

- **FastAPI**: Selected for asynchronous performance, native Pydantic validation, and automated OpenAPI documentation.
- **SQLite**: Selected to guarantee zero-dependency persistence that survives server restarts without external database setup. *(Trade-off: For high-concurrency production deployments with thousands of concurrent voice streams, PostgreSQL with connection pooling would be preferred)*.
- **Client-Side SDK vs Webhook Fallback**: The web client leverages `@elevenlabs/client` with signed session authentication and smart fallback to public agent ID if API key permissions vary.
