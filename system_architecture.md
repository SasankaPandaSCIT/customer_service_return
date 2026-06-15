# AI Customer Support Agent: Architecture & Logic

This document details the structure and underlying logic of the AI Customer Support Agent, visualizing the system with Mermaid diagrams.

## 1. High-Level System Architecture

The application is split into a React frontend and a Python backend. It uses WebSockets for real-time text streaming and a REST endpoint for native audio streaming via ElevenLabs.

```mermaid
graph TD
    UI["Frontend (React + Vite)"] 
    API["Backend (FastAPI)"]
    Graph["LangGraph Orchestrator"]
    LLM["Google Gemini API"]
    Voice["ElevenLabs API (TTS)"]
    DB[("Synthetic Data\n(crm.json / refund_policy.md)")]

    UI -- "WebSocket (/ws/chat)\nJSON Messages" --> API
    UI -- "GET (/api/tts)\nAudio Stream" --> API
    API -- "Invokes State Graph" --> Graph
    API -- "Converts Text to Speech" --> Voice
    Graph -- "Prompts & Tool Calls" --> LLM
    Graph -- "Tool Executions" --> DB
```

> [!NOTE]
> WebSockets are crucial here for the chat interface. Unlike a standard REST API, WebSockets allow the FastAPI server to actively stream events (like `on_tool_start`, `on_chat_model_stream`) back to the frontend in real-time. For the voice output, a direct `GET` request is used so the browser can natively stream the MP3 chunks from ElevenLabs with near-zero latency.

---

## 2. Multi-Agent Orchestration (Sequential Pipeline)

The backend orchestrator is implemented with **LangGraph** and a deterministic three-phase pipeline. The current flow is driven by internal signaling in Python, not by a high-level supervisor LLM router.

The graph routes the user's input through specialized agents in a fixed order:

```mermaid
flowchart TD
    %% Styling customized for a clean presentation (Loopp brand aesthetic)
    classDef worker fill:#ffffff,color:#000000,stroke:#cccccc,stroke-width:2px,rx:8,ry:8
    classDef terminal fill:#f8fafc,color:#4b5563,stroke:#cbd5e1,stroke-width:2px,stroke-dasharray: 5 5,rx:99,ry:99

    Start(((User Input))):::terminal --> Triage
    
    Triage["Triage Agent\n• get_customer_info\n• Identifies user & order"]:::worker
    Policy["Policy Agent\n• get_order_details\n• check_policy\n• Validates refund eligibility"]:::worker
    Action["Action Agent\n• process_refund / deny_refund\n• Replies to user"]:::worker

    Triage -- "Asks Question" --> End1(((Wait for User))):::terminal
    Triage -- "Validates order and emits [INTERNAL]" --> Policy
    Policy -- "Evaluates policy and emits [INTERNAL]" --> Action
    Action -- "Streams final answer" --> End2(((End))):::terminal
```

### Routing Logic
1. A user message enters the `Triage` agent first.
2. `Triage` checks whether the customer provided a valid Customer ID and order number.
3. If more information is needed, `Triage` asks the user directly and the workflow ends until the next user message.
4. If the order is validated, `Triage` returns a hidden `[INTERNAL]` success message instead of a user-facing answer.
5. The Python `route_from_triage` function detects the `[INTERNAL]` marker in `app/agent.py` and deterministically routes the flow to the `Policy` agent.
6. `Policy` applies the refund policy, forms a structured internal decision, and emits another `[INTERNAL]` message.
7. The `Action` agent parses that internal decision, executes `process_refund(order_id)` or `deny_refund(order_id, reason)`, and returns the final user-facing response.

### Why this works
- The workflow is explicit: no LLM-based routing decisions are needed for phase transitions.
- Internal tags preserve the separation between agent-to-agent communication and user-facing text.
- The pipeline is easier to debug and reduces the chance of an agent skipping a phase.

---

## 3. Data & Utility Flow

The agents rely on mock Python tools to interface with the database.

```mermaid
flowchart LR
    subgraph "Backend Tools Layer"
        T_Customer["get_customer_info(email)"]
        T_Order["get_order_details(order_id)"]
        T_Policy["check_policy()"]
        T_Refund["process_refund(order_id)"]
        T_Deny["deny_refund(order_id, reason)"]
    end
    
    subgraph "Data Storage"
        CRM[/"data/crm.json"/]
        Policy[/"data/refund_policy.md"/]
    end

    T_Customer --> CRM
    T_Order --> CRM
    T_Policy --> Policy
    T_Refund -. "Mocks Success" .-> CRM
    T_Deny -. "Mocks Denial" .-> CRM
```

> [!TIP]
> This modular structure makes it incredibly easy to replace the synthetic JSON database with a real SQL database (e.g., PostgreSQL) or an actual headless CRM (e.g., Salesforce) in the future without changing the agent logic.
