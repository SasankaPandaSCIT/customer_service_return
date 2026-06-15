# AI Customer Support Agent

This repository contains a synthetic customer support assistant built with a React frontend and a Python backend. The assistant is designed to handle refund requests, validate customer identity, check order eligibility, and apply a simple business refund policy.

## Business Purpose

The AI Customer Support Agent is intended for e-commerce customer service scenarios where the system must:

- Validate a customer request using Customer ID and order number
- Verify order details from CRM data
- Apply a refund policy consistently
- Approve or deny refunds based on defined business rules
- Communicate denials with policy-backed reasons

This project demonstrates how to combine conversational AI, workflow agents, and tool-based decision logic to manage customer support interactions.

## Key Backend Functionality

The backend is located in `backend/app` and includes the following core components:

- `main.py`
  - FastAPI application exposing `/ws/chat` for live chat and `/api/tts` for text-to-speech.
  - Streams conversation events from the LangGraph workflow to the frontend.
- `agent.py`
  - Defines a three-phase workflow with Triage, Policy, and Action agents.
  - Uses `langgraph` and `langchain-google-genai` to orchestrate conversation routing.
  - Validates refund requests and executes final decisions.
- `tools.py`
  - Implements tools for CRM lookup and refund actions:
    - `get_customer_info(customer_id)`
    - `get_order_details(order_id)`
    - `process_refund(order_id)`
    - `deny_refund(order_id, reason)`
    - `check_policy()`
- `prompts.py`
  - Contains the agent prompts and business rules for each stage.
  - Enforces that the Policy Agent provides a complete denial reason and that the Action Agent uses it in the tool call.
- `utils.py`
  - Loads CRM data and refund policy content from disk.

## Business Rules and Policy

The refund policy is stored in `backend/data/refund_policy.md` and currently includes:

- General refund rules: refunds are returned to the original payment method, shipping is non-refundable.
- Electronics: 14-day return window.
- Clothing: 30-day return window with condition requirements.
- Software & Digital Downloads: strictly non-refundable.
- Final Sale / Clearance: non-refundable.

The policy is applied during the Policy Agent stage, and denials are expected to clearly explain why the item is ineligible.

## Frontend

The frontend is in `backend/frontend` and is based on React + Vite.

- `src/` contains the UI components and chat client.
- The frontend connects to the backend by opening a websocket to `/ws/chat`.
- It also supports TTS via the `/api/tts` endpoint.

## Data

CRM data is stored in `backend/data/crm.json` and simulates customer orders and purchase history. The backend uses this data to validate order ownership and fetch order details.

## Running the Project

### Backend

From `backend/`:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Frontend

From `frontend/`:

```bash
npm install
npm run dev
```

## Project Structure

- `backend/`
  - `app/`
    - `agent.py`
    - `main.py`
    - `prompts.py`
    - `tools.py`
    - `utils.py`
  - `data/`
    - `crm.json`
    - `refund_policy.md`
  - `requirements.txt`
- `frontend/`
  - `src/`
  - `package.json`
  - `vite.config.js`
  - `README.md`

## System Architecture

The system uses a structured agent workflow in the backend to manage refund requests reliably.

- The React frontend connects to the FastAPI backend using WebSocket at `/ws/chat` for real-time chat.
- The backend exposes a TTS endpoint at `/api/tts` for speech generation with ElevenLabs.
- The backend orchestrates three agents in sequence:
  - `Triage`: validates Customer ID and order ownership using `get_customer_info`.
  - `Policy`: checks refund eligibility with `get_order_details` and `check_policy`.
  - `Action`: executes the final outcome with `process_refund` or `deny_refund`.
- Internal `[INTERNAL]` messages are used to move the flow from one agent to the next without exposing intermediate decision logic to the user.
- The routing is deterministic in `backend/app/agent.py`; there is no hidden supervisor agent making phase transitions.
- The data layer is currently synthetic: `backend/data/crm.json` and `backend/data/refund_policy.md`.

## Notes

- The assistant uses synthetic business content for testing refund logic.
- The backend includes a mock refund action rather than real payment processing.
- The current policy is intentionally strict for digital and final-sale items to demonstrate denial reasoning.

If you want, I can also add a short section describing the conversation workflow and how the triage/policy/action agents interact.