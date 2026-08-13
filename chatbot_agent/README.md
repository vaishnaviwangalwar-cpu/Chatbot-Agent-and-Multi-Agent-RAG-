# Project 1 — ChatBot Agent (DY Patil University AI Workshop)

A production-grade AI ChatBot Agent application built with **FastAPI**, **Google GenAI SDK (`google-genai`)**, **Pydantic**, and an interactive **Web UI**.

---

## 1. Overview & Teaching Objectives

This project demonstrates core AI Engineering concepts in a clean, modular codebase:

1. **SOLID & DRY Architecture**: Separating concerns into Schemas (`app/schemas`), Prompts (`app/prompts`), Tools (`app/tools`), Services (`app/services`), and Routers (`app/api`).
2. **Module 3 Prompt Engineering**: Comparing system prompt techniques (**Structured XML Tags**, **Few-Shot Examples**, **Chain-of-Thought Reasoning**, and **Standard Baseline**).
3. **Session Memory Management**: In-memory sliding-window context manager (`MAX_TURNS = 10`) capping context window token usage without external database overhead.
4. **Tool Calling (Function Calling)**: Python functions (`get_current_datetime`, safe AST `calculate`, `lookup_faq`) executed automatically by Gemini SDK.
5. **Dual Response Modes (Streaming & Standard)**: Real-time token streaming via Server-Sent Events (SSE) or standard JSON response delivery under the same session memory context.

---

## 2. Directory Architecture

```
chatbot_agent/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application setup, static mounting, & health check
│   ├── config.py                   # Centralized Pydantic BaseSettings (.env reader)
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── chat.py                 # Pydantic schemas (ChatRequest, ChatResponse, ToolCallInfo, SessionInfo)
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── system_prompts.py       # Module 3 techniques (Standard, XML Tags, Few-Shot, CoT)
│   │   └── campus_faqs.py          # Campus knowledge base dataset
│   ├── tools/
│   │   ├── __init__.py
│   │   └── campus_tools.py         # Strongly-typed Python tools (DateTime, Math Calculator, FAQ Lookup)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── memory_service.py       # In-Memory sliding-window session manager
│   │   └── agent_service.py        # Gemini SDK orchestration & tool execution tracking
│   └── api/
│       ├── __init__.py
│       └── chat_router.py          # REST API Endpoints (/api/chat, /api/chat/stream, /api/sessions, /api/prompts)
├── static/
│   ├── index.html                  # Glassmorphic HTML5 Web UI
│   ├── css/
│   │   └── style.css               # Modern CSS tokens, animations & responsive styling
│   └── js/
│       └── app.js                  # Client-side chat application & SSE stream manager
├── .env.example                    # Environment variable template
├── requirements.txt                # Dependencies
└── README.md                       # Main Documentation & Presenter Walkthrough
```

---

## 3. Quick Setup

### Step 1: Activate Virtual Environment

```bash
cd "/Users/durgesh.keshri/AI Workshop/chatbot_agent"

python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment

Copy `.env.example` to `.env` and add your **Google AI Studio Gemini API Key**:

```bash
cp .env.example .env
```

Edit `.env`:
```env
GEMINI_API_KEY=your_google_ai_studio_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
APP_ENV=development
HOST=0.0.0.0
PORT=8000
```

---

## 4. Running the Application

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload --port 8000
```

Access the application:
* **Web Application UI**: [http://localhost:8000](http://localhost:8000)
* **Interactive API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **System Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 5. Presenter Walkthrough for Live Presentation

### Phase 1 — Prompt Design (`app/prompts/system_prompts.py`)
Demonstrates four prompt engineering techniques in code:
- **`STRUCTURED_XML_PROMPT`**: Organizes instructions into `<role>`, `<scope>`, `<tone>`, `<instructions>`, and `<rules>` tags.
- **`FEW_SHOT_PROMPT`**: Multi-turn example demonstrations steering format and tone.
- **`COT_PROMPT`**: Instructs the model to analyze intent and determine tool needs step-by-step before answering.
- **`BASELINE_PROMPT`**: Simple role definition baseline.

### Phase 2 — Session Memory (`app/services/memory_service.py`)
- Manages `dict[session_id, list[dict]]` in memory.
- Enforces `MAX_TURNS = 10` sliding window to cap token consumption.
- Reconstructs history into Gemini `types.Content` objects passed to the model.

### Phase 3 — Tool Calling (`app/tools/campus_tools.py`)
- **`get_current_datetime()`**: Returns system day, date, and time.
- **`calculate(expression)`**: Safe AST expression evaluator (Python 3.14 compatible).
- **`lookup_faq(topic)`**: Queries campus FAQ knowledge base (`app/prompts/campus_faqs.py`).

### Agent Orchestration (`app/services/agent_service.py`)
- Configures `GenerateContentConfig` with `system_instruction`, `tools`, and `thinking_config`.
- Inspects `response.automatic_function_calling_history` natively to track executed tools.

---

## 6. Live Demonstration Commands (`curl`)

### 1. Scope Enforcement (Out of Scope Query)
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo1", "message": "What is the capital of France?", "prompt_style": "structured_xml"}'
```

### 2. Multi-Turn Session Memory Test
```bash
# Turn 1: Store student details in memory
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "student_session_1", "message": "My name is Asha and I study Electrical Engineering.", "prompt_style": "structured_xml"}'

# Turn 2: Query stored memory
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "student_session_1", "message": "What is my name and branch?", "prompt_style": "structured_xml"}'
```

### 3. Tool Calling Verification
```bash
# Date/Time Tool Call
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo1", "message": "What time is it right now?", "prompt_style": "structured_xml"}'

# Math Calculator Tool Call
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo1", "message": "I am paying 2000 INR book fees with a 15% discount, calculate 2000 * 0.15 for me.", "prompt_style": "structured_xml"}'

# FAQ Lookup Tool Call
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo1", "message": "What are the hostel fees?", "prompt_style": "structured_xml"}'
```

### 4. Real-Time Token Streaming Test (SSE)
```bash
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"session_id": "stream_demo", "message": "Tell me 3 interesting facts about DY Patil University campus.", "prompt_style": "structured_xml"}'
```

---

## 7. API Contract Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/chat` | Main agent chat endpoint (Standard JSON). Accepts `{session_id, message, prompt_style}`. |
| `POST` | `/api/chat/stream` | Real-time Server-Sent Events (SSE) token streaming endpoint. |
| `GET` | `/api/sessions` | Lists active conversation sessions in memory. |
| `GET` | `/api/chat/{session_id}` | Retrieves conversation history for a specific session. |
| `DELETE` | `/api/chat/{session_id}` | Clears conversation memory for a specific session (idempotent). |
| `GET` | `/api/prompts` | Returns available Prompt Engineering styles and system prompts. |
| `GET` | `/health` | Health check returning status and model configuration. |

---

## 8. Hyperparameter Tuning & Model Behavior

You can fine-tune generation behavior dynamically by modifying environment variables in `.env` (or via `app/config.py`):

| Environment Variable | Default | Impact on Model Output & Behavior |
| :--- | :---: | :--- |
| `MAX_OUTPUT_TOKENS` | `1024` | **Response Length Limit**: Controls the maximum number of tokens generated per turn. Lower values (e.g. `100`) force brief answers; higher values (e.g. `2048`) allow detailed explanations. |
| `TEMPERATURE` | `0.7` | **Creativity vs Determinism**: `0.0` produces strict, deterministic, factual responses (ideal for math & tool calling). `1.0` produces highly creative, varied phrasing. |
| `TOP_P` | `None` *(Model Default)* | **Nucleus Sampling**: Considers top tokens whose cumulative probability reaches `P`. Leaving as `None` uses Gemini's native model default. |
| `TOP_K` | `None` *(Model Default)* | **Vocabulary Candidate Limit**: Limits generation to `K` candidate words. Leaving as `None` uses Gemini's native model default (setting `1` forces greedy decoding). |
| `THINKING_LEVEL` | `"MINIMAL"` | **Gemini 3.x Reasoning Depth**: Supported options are `MINIMAL`, `LOW`, `MEDIUM`, or `HIGH`. Controls how deep Gemini's internal reasoning runs before outputting text. |

### Practical Configuration Presets (`.env` Examples)

#### 1. Factual & Deterministic Preset (Ideal for Math & Tool Calling)
```env
TEMPERATURE=0.0
MAX_OUTPUT_TOKENS=512
THINKING_LEVEL=MINIMAL
```
* **Behavior**: Zero randomness, exact math calculations, and strict adherence to tool outputs without fluff.

#### 2. Creative Assistance Preset (Ideal for Brainstorming & Writing)
```env
TEMPERATURE=0.9
TOP_P=0.95
TOP_K=40
MAX_OUTPUT_TOKENS=2048
THINKING_LEVEL=MEDIUM
```
* **Behavior**: High vocabulary diversity and creative phrasing while maintaining moderate internal reasoning.

#### 3. Deep Problem Solving Preset (Ideal for Complex Analytics)
```env
TEMPERATURE=0.2
MAX_OUTPUT_TOKENS=2048
THINKING_LEVEL=HIGH
```
* **Behavior**: Low temperature for precision combined with `HIGH` thinking level for deep step-by-step internal reasoning.
