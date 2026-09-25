import asyncio

from config import model_client

from supervisor import create_supervisor
from knowledge_agent import create_knowledge_agent
from analytics_agent import create_analytics_agent
from web_research_agent import create_web_research_agent
from document_rag_agent import create_document_rag_agent
from quality_agent import create_quality_agent

from memory import save_memory

from human_approval import (
    requires_human_approval,
    request_human_approval,
)

from termination import (
    mark_final_answer,
    is_final_answer,
    remove_final_answer_signal,
)

from execution_tracker import ExecutionTracker


# ============================================================
# CREATE AGENTS
# ============================================================

supervisor = create_supervisor(model_client)
knowledge_agent = create_knowledge_agent(model_client)
analytics_agent = create_analytics_agent(model_client)
web_research_agent = create_web_research_agent(model_client)
document_rag_agent = create_document_rag_agent(model_client)
quality_agent = create_quality_agent(model_client)


# ============================================================
# WORKFLOW CONTROLS
# ============================================================

AGENT_TIMEOUT_SECONDS = 180

# ============================================================
# SHORT-TERM MEMORY
# ============================================================

conversation_memory = {
    "last_question": "",
    "last_answer": "",
}


def save_to_short_term_memory(question: str, answer: str):

    conversation_memory["last_question"] = question
    conversation_memory["last_answer"] = answer


def get_short_term_memory() -> str:

    last_question = conversation_memory["last_question"]
    last_answer = conversation_memory["last_answer"]

    if not last_question:
        return "No previous conversation."

    short_answer = last_answer[:300]

    return f"""
Previous question:
{last_question}

Previous answer:
{short_answer}
"""


# ============================================================
# FAST ROUTER
# ============================================================

def fast_route(user_question: str):

    question = user_question.lower().strip()

    # --------------------------------------------------------
    # COMPANY POLICY / INTERNAL DOCUMENTS
    # --------------------------------------------------------

    document_keywords = [
        "annual leave",
        "sick leave",
        "leave policy",
        "attendance policy",
        "working hours",
        "work from home",
        "wfh",
        "employee conduct",
        "hr policy",
        "data privacy",
        "information security",
        "password policy",
        "mfa",
        "multi-factor authentication",
        "access control",
        "device security",
        "security incident",
        "vendor policy",
        "vendor onboarding",
        "vendor approval",
        "vendor compliance",
        "vendor evaluation",
        "company policy",
        "company rules",
        "internal procedure",
    ]

    for keyword in document_keywords:

        if keyword in question:
            return "DocumentRAGAgent"

    # --------------------------------------------------------
    # CURRENT / EXTERNAL INFORMATION
    # --------------------------------------------------------

    web_keywords = [
        "current",
        "latest",
        "today",
        "2026",
        "recent",
        "market trend",
        "industry trend",
        "competitor",
        "competitors",
        "current ai",
        "latest ai",
        "latest technology",
    ]

    for keyword in web_keywords:

        if keyword in question:
            return "WebResearchAgent"

    # --------------------------------------------------------
    # ANALYTICS
    # --------------------------------------------------------

    analytics_keywords = [
        "calculate",
        "calculation",
        "percentage",
        "percent",
        "kpi",
        "metrics",
        "trend analysis",
        "cost benefit",
        "cost-benefit",
        "roi",
        "business impact",
        "numerical",
        "compare",
        "calculate the",
    ]

    for keyword in analytics_keywords:

        if keyword in question:
            return "AnalyticsAgent"

    # --------------------------------------------------------
    # GENERAL KNOWLEDGE
    # --------------------------------------------------------

    general_patterns = [
        "what is",
        "what are",
        "define",
        "definition of",
        "explain",
        "meaning of",
        "role of",
    ]

    for pattern in general_patterns:

        if question.startswith(pattern):
            return "KnowledgeAgent"

    return None


# ============================================================
# SUPERVISOR ROUTING
# ============================================================

def detect_route(supervisor_response: str):

    if not supervisor_response:
        return "KnowledgeAgent"

    response = supervisor_response.lower()

    if "documentragagent" in response:
        return "DocumentRAGAgent"

    if "webresearchagent" in response:
        return "WebResearchAgent"

    if "analyticsagent" in response:
        return "AnalyticsAgent"

    if "knowledgeagent" in response:
        return "KnowledgeAgent"

    return "KnowledgeAgent"


# ============================================================
# QUALITY GATE
# ============================================================

def requires_quality_review(route: str):

    return route in {
        "DocumentRAGAgent",
        "AnalyticsAgent",
        "WebResearchAgent",
    }


def quality_passed(quality_response: str):

    if not quality_response:
        return False

    response = quality_response.lower().strip()

    return "quality status: pass" in response


# ============================================================
# SPECIALIST LOOKUP
# ============================================================

def get_specialist(route: str):

    specialists = {
        "KnowledgeAgent": knowledge_agent,
        "AnalyticsAgent": analytics_agent,
        "WebResearchAgent": web_research_agent,
        "DocumentRAGAgent": document_rag_agent,
    }

    return specialists.get(route)


# ============================================================
# AGENT EXECUTION
# ============================================================

async def run_agent(
    agent,
    task,
    tracker=None,
    stage_name=None,
):

    if agent is None:

        error = (
            f"Agent configuration error: "
            f"agent is missing for stage '{stage_name}'."
        )

        if tracker and stage_name:
            tracker.fail(error)

        raise RuntimeError(error)

    if tracker and stage_name:
        tracker.start_stage(stage_name)

    stage_completed = False

    try:

        result = await asyncio.wait_for(
            agent.run(
                task=task
            ),
            timeout=AGENT_TIMEOUT_SECONDS,
        )

        if result is None:
            raise RuntimeError(
                f"{stage_name} returned no result."
            )

        if not result.messages:
            raise RuntimeError(
                f"{stage_name} returned no messages."
            )

        final_message = result.messages[-1]

        response = getattr(
            final_message,
            "content",
            None,
        )

        if response is None:
            raise RuntimeError(
                f"{stage_name} returned a message "
                f"without content."
            )

        response = str(response).strip()

        if not response:
            raise RuntimeError(
                f"{stage_name} returned an empty response."
            )

        if tracker and stage_name:

            tracker.end_stage()
            stage_completed = True

        return response

    except asyncio.TimeoutError:

        if tracker and stage_name and not stage_completed:
            tracker.timeout()

        raise

    except Exception as error:

        if tracker and stage_name and not stage_completed:
            tracker.fail(error)

        raise


# ============================================================
# RUN CORPORATE AI WORKFLOW
# ============================================================

async def run_team(user_question):

    tracker = ExecutionTracker(
        user_question
    )

    try:

        # ====================================================
        # INPUT VALIDATION
        # ====================================================

        tracker.start_stage(
            "INPUT_VALIDATION"
        )

        if not isinstance(
            user_question,
            str,
        ):

            raise ValueError(
                "User question must be a string."
            )

        user_question = user_question.strip()

        if not user_question:

            raise ValueError(
                "User question cannot be empty."
            )

        tracker.end_stage()

        # ====================================================
        # HUMAN APPROVAL
        # ====================================================

        if requires_human_approval(
            user_question
        ):

            tracker.start_stage(
                "HUMAN_APPROVAL"
            )

            print(
                "\n=============================================="
            )

            print(
                "        HUMAN APPROVAL REQUIRED"
            )

            print(
                "=============================================="
            )

            approved = request_human_approval(
                user_question
            )

            if not approved:

                print(
                    "\nRequest rejected by human."
                )

                tracker.end_stage()
                tracker.complete()

                return {
                    "route":
                        "HumanApproval",

                    "specialist_response":
                        "Request rejected by human approval.",

                    "quality_response":
                        "Workflow stopped after human rejection.",

                    "request_id":
                        tracker.request_id,

                    "status":
                        "REJECTED",
                }

            print(
                "\nHuman approval granted."
            )

            tracker.end_stage()

        # ====================================================
        # LOAD MEMORY
        # ====================================================

        tracker.start_stage(
            "LOAD_MEMORY"
        )

        short_term_context = (
            get_short_term_memory()
        )

        tracker.end_stage()

        # ====================================================
        # FAST ROUTER
        # ====================================================

        tracker.start_stage(
            "FAST_ROUTER"
        )

        print(
            "\n[1] Fast Router checking..."
        )

        fast_route_result = fast_route(
            user_question
        )

        tracker.end_stage()

        # ====================================================
        # ROUTE SELECTION
        # ====================================================

        if fast_route_result:

            route = fast_route_result

            print(
                f"Fast Route: {route}"
            )

            print(
                "Supervisor skipped for obvious request."
            )

        else:

            print(
                "No obvious route found."
            )

            print(
                "Supervisor is routing..."
            )

            supervisor_task = f"""
Previous conversation:

{short_term_context}

Current user question:

{user_question}

Route the current question to the correct specialist.

Available specialists:

- KnowledgeAgent
- AnalyticsAgent
- WebResearchAgent
- DocumentRAGAgent

Use previous conversation only when relevant.

Return only the routing decision and a brief reason.
"""

            supervisor_result = await run_agent(
                supervisor,
                supervisor_task,
                tracker,
                "SUPERVISOR",
            )

            route = detect_route(
                supervisor_result
            )

            print(
                f"Supervisor Route: {route}"
            )

        # ====================================================
        # SPECIALIST
        # ====================================================

        specialist = get_specialist(
            route
        )

        if specialist is None:

            raise RuntimeError(
                f"Invalid specialist route: {route}"
            )

        print(
            f"\n[2] {route}"
        )

        specialist_task = f"""
Previous conversation:

{short_term_context}

Current user question:

{user_question}

Answer the current question.

Use previous conversation only when relevant.

For company-specific questions, use the appropriate
corporate source or retrieval tool.

Do not invent company-specific information.

Return a concise and accurate answer.
"""

        specialist_result = await run_agent(
            specialist,
            specialist_task,
            tracker,
            f"SPECIALIST: {route}",
        )

        # ====================================================
        # QUALITY GATE
        # ====================================================

        if requires_quality_review(route):

            print(
                "\n[3] QualityAgent reviewing..."
            )

            quality_task = f"""
USER QUESTION:

{user_question}


SPECIALIST ANSWER:

{specialist_result}


QUALITY REVIEW INSTRUCTIONS:

Evaluate ONLY whether the specialist answer correctly
answers the user's actual question.

For DocumentRAGAgent:

- Treat the retrieved corporate document information
  contained in the answer as the evidence.
- Do not demand information that the user did not ask for.
- Do not invent additional requirements.
- Do not require unrelated information.
- If the requested value is clearly provided, consider
  that part complete.

Example:

If the answer says:

"Eligible employees can work from home up to 2 days per week."

Do NOT mark it incomplete because the total number of
working days in the week is not stated.

Return exactly:

Quality Status: PASS

or:

Quality Status: NEEDS_REVISION
Reason: <one short, specific reason>

Do not rewrite the answer.
Do not perform additional research.
Do not ask questions.
"""

            quality_result = await run_agent(
                quality_agent,
                quality_task,
                tracker,
                "QUALITY_GATE",
            )

            # ------------------------------------------------
            # QA DIAGNOSTICS
            # ------------------------------------------------

            print(
                "\n----------------------------------------------"
            )

            print(
                "QUALITY AGENT RESPONSE"
            )

            print(
                "----------------------------------------------"
            )

            print(
                quality_result
            )

            print(
                "----------------------------------------------"
            )

            # ------------------------------------------------
            # QA DECISION
            # ------------------------------------------------

            if quality_passed(
                quality_result
            ):

                print(
                    "Quality: PASS"
                )

            else:

                print(
                    "Quality: NEEDS_REVISION"
                )

                print(
                    "QA warning retained for review."
                )

        else:

            quality_result = (
                "Quality review not required."
            )

            print(
                "\n[3] QualityAgent skipped."
            )

        # ====================================================
        # FINAL ANSWER
        # ====================================================

        tracker.start_stage(
            "FINAL_ANSWER"
        )

        specialist_result = mark_final_answer(
            specialist_result
        )

        if is_final_answer(
            specialist_result
        ):

            final_answer = (
                remove_final_answer_signal(
                    specialist_result
                )
            )

            print(
                "\nFinal-answer signal detected."
            )

        else:

            final_answer = specialist_result

        tracker.end_stage()

        # ====================================================
        # SHORT-TERM MEMORY
        # ====================================================

        tracker.start_stage(
            "SAVE_SHORT_TERM_MEMORY"
        )

        save_to_short_term_memory(
            user_question,
            final_answer,
        )

        print(
            "Short-term memory: saved."
        )

        tracker.end_stage()

        # ====================================================
        # LONG-TERM MEMORY
        # ====================================================

        tracker.start_stage(
            "SAVE_LONG_TERM_MEMORY"
        )

        save_memory(
            user_question,
            final_answer,
        )

        print(
            "Long-term memory: saved."
        )

        tracker.end_stage()

        # ====================================================
        # COMPLETE
        # ====================================================

        tracker.complete()

        return {
            "route":
                route,

            "specialist_response":
                final_answer,

            "quality_response":
                quality_result,

            "request_id":
                tracker.request_id,

            "status":
                "COMPLETED",
        }

    # ========================================================
    # TIMEOUT
    # ========================================================

    except asyncio.TimeoutError:

        print()
        print(
            "=============================================="
        )

        print(
            "WORKFLOW TIMEOUT"
        )

        print(
            "=============================================="
        )

        print(
            f"Agent timeout: "
            f"{AGENT_TIMEOUT_SECONDS} seconds."
        )

        print(
            f"Request ID: "
            f"{tracker.request_id}"
        )

        print(
            "Check the execution tracker to identify "
            "the stage that timed out."
        )

        print(
            "=============================================="
        )

        return {
            "route":
                "ERROR",

            "specialist_response":
                "The workflow timed out before completing.",

            "quality_response":
                "Quality review was not completed.",

            "request_id":
                tracker.request_id,

            "status":
                "TIMEOUT",
        }

    # ========================================================
    # GENERAL ERROR
    # ========================================================

    except Exception as error:

        if tracker.status != "FAILED":

            tracker.fail(error)

        print()
        print(
            "=============================================="
        )

        print(
            "WORKFLOW ERROR"
        )

        print(
            "=============================================="
        )

        print(
            f"Request ID: "
            f"{tracker.request_id}"
        )

        print(
            f"Error: {error}"
        )

        print(
            "=============================================="
        )

        return {
            "route":
                "ERROR",

            "specialist_response":
                "The workflow encountered an internal error.",

            "quality_response":
                "Quality review was not completed.",

            "request_id":
                tracker.request_id,

            "status":
                "FAILED",
        }


# ============================================================
# CLI APPLICATION
# ============================================================

async def main():

    print(
        "\n=============================================="
    )

    print(
        "   CORPORATE AGENTIC AI MULTI-AGENT SYSTEM"
    )

    print(
        "=============================================="
    )

    print(
        "\nArchitecture:"
    )

    print(
        "Fast Router → Supervisor when needed → "
        "Specialist → Quality"
    )

    print(
        "\nMemory:"
    )

    print(
        "Short-term + Long-term"
    )

    print(
        "\nTermination:"
    )

    print(
        "Explicit FINAL_ANSWER signal"
    )

    print(
        "\nQuality review:"
    )

    print(
        "Document/RAG + Analytics + Web Research"
    )

    print(
        "\nExecution tracking:"
    )

    print(
        "Every workflow stage is timed."
    )

    print(
        "\nEnter 'exit' to stop."
    )

    while True:

        print(
            "\n----------------------------------------------"
        )

        try:

            user_question = input(
                "\n> "
            )

        except (
            KeyboardInterrupt,
            EOFError,
        ):

            print(
                "\n\nConversation ended."
            )

            break

        if user_question.lower().strip() == "exit":

            print(
                "\nConversation ended."
            )

            break

        if not user_question.strip():

            print(
                "\nPlease enter a question."
            )

            continue

        result = await run_team(
            user_question
        )

        if result is None:

            print(
                "\nNo result was produced."
            )

            continue

        print(
            "\n=============================================="
        )

        print(
            "FINAL ANSWER"
        )

        print(
            "=============================================="
        )

        print(
            result["specialist_response"]
        )

        print(
            "\n----------------------------------------------"
        )

        print(
            "QUALITY REVIEW"
        )

        print(
            "----------------------------------------------"
        )

        print(
            result["quality_response"]
        )

        print(
            "\n----------------------------------------------"
        )

        print(
            f"ROUTE: {result['route']}"
        )

        print(
            f"STATUS: {result['status']}"
        )

        print(
            f"REQUEST ID: {result['request_id']}"
        )

        print(
            "\n=============================================="
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )