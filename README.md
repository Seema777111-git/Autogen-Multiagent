# AutoGen Multi-Agent Corporate AI System

An **Agentic AI application built with Microsoft AutoGen** that uses multiple specialized AI agents to understand corporate questions, route them to the right agent, retrieve internal information, analyze business data, and return a grounded response through a Streamlit interface.

The project demonstrates how **Agentic AI can be designed for practical corporate use cases** rather than relying on one general-purpose chatbot.

---

## 🎯 Project Objective

The goal of this project is to build a corporate AI assistant that can:

- Understand a user's request
- Select the appropriate specialist agent
- Retrieve information from internal documents
- Perform business data analysis
- Conduct web research when required
- Maintain conversation context
- Apply quality checks
- Support human approval where required
- Track workflow execution
- Terminate workflows safely

### Basic Flow

```text
                    ┌─────────────────┐
                    │      User       │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Supervisor    │
                    │ Agent / Router  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌───────────┐  ┌───────────┐  ┌──────────────┐
        │ Document  │  │ Analytics │  │ Web Research│
        │ RAG Agent │  │   Agent   │  │    Agent    │
        └───────────┘  └───────────┘  └──────────────┘
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                    ┌─────────────────┐
                    │ Quality / Final │
                    │    Response     │
                    └─────────────────┘
                             │
                             ▼
                           User
```

---

# 🤖 Agents

## 1. Supervisor Agent

The Supervisor is the **central routing agent**.

Responsibilities:

- Understand the user's question
- Decide which specialist agent should handle it
- Coordinate the workflow
- Receive the specialist response
- Return the final answer

Example:

```text
User:
How many annual leave days can be carried over?

        ↓

Supervisor

        ↓

DocumentRAGAgent
```

---

## 2. Document RAG Agent

The Document RAG Agent handles questions that require information from internal corporate documents.

It uses:

- Document retrieval
- FAISS vector search
- Retrieved context
- LLM-based answer generation

Example:

```text
User:
How many annual leave days can be carried over?

        ↓

Retrieve HR Policy

        ↓

Relevant policy content

        ↓

LLM generates a natural-language answer
```

The goal is to provide an answer based on the available corporate evidence rather than allowing the model to freely invent information.

---

## 3. Knowledge Agent

The Knowledge Agent handles corporate knowledge and information-oriented requests.

It can be extended to work with:

- Corporate knowledge
- Business rules
- Policies
- Organizational information
- Frequently asked questions

---

## 4. Analytics Agent

The Analytics Agent handles business-data questions.

Examples:

- Identify trends
- Compare values
- Calculate changes
- Analyze performance
- Identify highest/lowest values
- Interpret business metrics

Example:

```text
January   → 120 tickets → 8 min
February  → 150 tickets → 7 min
March     → 180 tickets → 6 min
April     → 210 tickets → 5 min
```

The agent can identify that:

- Ticket volume increased.
- Average response time decreased.
- Response performance improved.

---

## 5. Web Research Agent

The Web Research Agent is designed for requests that require information from external sources.

Example:

```text
User Question
      ↓
Supervisor
      ↓
Web Research Agent
      ↓
Research
      ↓
Answer
```

This keeps external research separate from internal corporate-document retrieval.

---

## 6. Quality Agent

The Quality Agent provides an additional quality-control layer.

It can be used to check:

- Relevance
- Completeness
- Grounding
- Response quality
- Potential issues in generated answers

This introduces an important enterprise concept:

> **The agent that generates an answer does not necessarily have to be the final quality gate.**

---

# 📚 RAG Architecture

The project includes sample corporate documents:

```text
documents/
│
├── HR and Workplace Policy.pdf
├── Data Privacy & Information Security Policy.pdf
└── Vendor Management Policy.pdf
```

The RAG pipeline uses a FAISS index to retrieve relevant information.

```text
User Question
      ↓
Document Retrieval
      ↓
FAISS Search
      ↓
Relevant Chunks
      ↓
LLM
      ↓
Grounded Answer
```

### Example

Question:

> How many annual leave days can be carried over?

Retrieved information includes the relevant annual-leave and carryover policy.

The LLM then converts the retrieved information into a natural-language response.

---

# 🧠 Agentic AI Concepts Demonstrated

This project demonstrates several important Agentic AI concepts:

- Multi-agent architecture
- Agent specialization
- Supervisor-based routing
- `SelectorGroupChat`
- Retrieval-Augmented Generation
- FAISS vector search
- Conversation memory
- Human-in-the-loop
- Quality validation
- Workflow termination
- Execution tracking
- Timeout management
- Streamlit UI

---

# 🔄 Example Workflow

### User Request

```text
How many annual leave days can be carried over?
```

### Workflow

```text
1. User submits question

2. Supervisor receives request

3. Supervisor identifies the request
   as a corporate-policy question

4. DocumentRAGAgent is selected

5. RAG retrieves relevant HR policy

6. Agent generates a grounded answer

7. Response returns to Supervisor

8. Final response is displayed to User

9. Workflow terminates
```

---

# 🛡️ Key Risks & Controls

Agentic AI introduces risks beyond a normal chatbot. This project specifically considers several of them.

| Risk | Control |
|---|---|
| **Hallucination** | RAG grounding for corporate-document questions |
| **Wrong agent selection** | Supervisor-based routing |
| **Infinite agent loop** | Explicit termination logic |
| **Long-running request** | Agent-level timeout handling |
| **Unapproved action** | Human-in-the-loop approval |
| **Poor answer quality** | Quality validation |
| **Lost conversation context** | Memory component |
| **Difficult troubleshooting** | Execution tracker |
| **API secret exposure** | Environment-based configuration |

### ⚠️ Important

These controls demonstrate the **design approach**. A production enterprise implementation would require additional security, governance, monitoring, access control, and compliance measures.

---

# 👤 Human-in-the-Loop

Not every business action should be completely autonomous.

The project includes a human approval component for workflows where human confirmation may be required.

Example:

```text
AI Agent
   ↓
Proposed Action
   ↓
Human Approval
   ↓
Approved / Rejected
   ↓
Continue or Stop
```

This demonstrates the principle:

> **AI can recommend or prepare an action while a human retains control over important decisions.**

---

# 🧠 Conversation Memory

The project includes a memory component to maintain useful conversation context.

This helps support multi-turn interactions where the meaning of a question depends on previous messages.

Example:

```text
User:
What is the annual leave policy?

AI:
Provides policy information.

User:
How many can be carried over?

AI:
Understands that "how many" refers to annual leave.
```

---

# ⏱️ Execution Tracking & Timeout Handling

Agentic workflows can take longer than normal chatbot responses because several agents may participate.

The project therefore includes:

### Execution Tracker

Tracks workflow stages such as:

```text
REQUEST
   ↓
SUPERVISOR
   ↓
SPECIALIST
   ↓
QUALITY
   ↓
COMPLETED
```

It also records failures and timeout events.

### Timeout Protection

Long-running agent execution is controlled using an agent-level timeout.

This prevents a request from running indefinitely.

---

# 🔚 Workflow Termination

A multi-agent system needs a clear stopping condition.

The project includes explicit termination handling to prevent situations where:

```text
Agent A
   ↓
Agent B
   ↓
Agent A
   ↓
Agent B
   ↓
Agent A
   ↓
...
```

The workflow should instead reach:

```text
Final Answer
     ↓
Termination
     ↓
Request Complete
```

Consecutive requests are also tested to ensure one completed request does not incorrectly continue into the next request.

---

# 🧪 QA & Testing

The project is tested from both an **AI behavior** and **workflow reliability** perspective.

### Routing Tests

Examples:

```text
Corporate policy question
        ↓
DocumentRAGAgent
```

```text
Business-data question
        ↓
AnalyticsAgent
```

```text
External research question
        ↓
WebResearchAgent
```

### RAG Tests

Test whether the system:

- Retrieves relevant documents
- Uses retrieved evidence
- Preserves important numbers and conditions
- Produces natural-language answers
- Avoids unsupported information

### Analytics Tests

Test:

- Trends
- Highest/lowest values
- Comparisons
- Calculations
- Business interpretation

### Workflow Tests

Test:

- Successful completion
- Multiple consecutive requests
- Agent timeout
- Workflow termination
- Routing failures
- Long-running requests

---

# 🖥️ Streamlit UI

The project uses Streamlit as the user interface.

The UI provides a simple way to:

- Submit questions
- Observe workflow execution
- View agent progress
- Receive the final answer
- Test multiple requests

The UI is intentionally simple so that the **Agentic AI architecture remains the main focus**.

---

# 📁 Project Structure

```text
AutoGen_ChatBot/
│
├── app.py
├── corporate_team.py
├── supervisor.py
│
├── document_rag_agent.py
├── knowledge_agent.py
├── analytics_agent.py
├── web_research_agent.py
├── quality_agent.py
│
├── rag_pipeline.py
├── memory.py
├── conversation_memory.json
├── human_approval.py
├── termination.py
├── execution_tracker.py
│
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
│
├── documents/
│   ├── Data Privacy & Information Security Policy.pdf
│   ├── HR and Workplace Policy.pdf
│   └── Vendor Management Policy.pdf
│
└── faiss_store/
    ├── chunks.txt
    └── corporate_documents.index
```

---

# ⚙️ Technology Stack

| Technology | Purpose |
|---|---|
| **Python** | Application development |
| **Microsoft AutoGen** | Multi-agent orchestration |
| **Streamlit** | User interface |
| **FAISS** | Vector similarity search |
| **RAG** | Grounded corporate knowledge retrieval |
| **LLM** | Reasoning and response generation |
| **PDF Documents** | Corporate knowledge source |
| **Git / GitHub** | Version control |

---

# 🚀 Setup

## 1. Clone the repository

```bash
git clone https://github.com/Seema777111-git/Autogen-Multiagent.git
cd Autogen-Multiagent
```

## 2. Create a virtual environment

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure environment variables

Create a `.env` file based on:

```text
.env.example
```

Add the required API configuration.

**Do not commit real API keys or secrets to GitHub.**

## 5. Run the application

```bash
streamlit run app.py
```

---

# 📌 Production Considerations

This project is a **portfolio / learning implementation of an enterprise-style Agentic AI system**.

For production deployment, additional capabilities would normally be required, such as:

- Enterprise authentication
- Role-based access control
- Secure secret management
- Audit logging
- Advanced observability
- Centralized vector database
- Database integration
- API security
- Data-loss prevention
- Model governance
- Cost monitoring
- Scalability
- High availability
- Compliance controls

---

# 💡 Future Enhancements

Possible next steps include:

- SQL/database analytics agent
- Enterprise authentication
- Role-based document access
- More corporate knowledge sources
- Advanced RAG evaluation
- Agent performance dashboards
- Cloud deployment
- API layer
- Audit and compliance reporting
- More sophisticated human approval workflows

---

# ⭐ Project Summary

**AutoGen Multi-Agent Corporate AI System** is a practical demonstration of how multiple specialized AI agents can work together to solve corporate problems.

Instead of building one large chatbot, the system separates responsibilities:

```text
                 Corporate AI Assistant
                         │
                    Supervisor
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
      RAG            Analytics         Research
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                    Quality Check
                         │
                   Final Response
                         │
                     Terminate
```

### Core Idea

> **One intelligent entry point + specialized agents + controlled orchestration + grounded knowledge + quality and safety controls = a practical Agentic AI system.**

---

## 👩‍💻 Portfolio Focus

This project demonstrates hands-on understanding of:

**Agentic AI • Microsoft AutoGen • Multi-Agent Systems • Supervisor Routing • RAG • FAISS • Business Analytics • Human-in-the-Loop • Memory • Quality Control • Workflow Management • QA Testing • Streamlit**
