import asyncio
import threading

import streamlit as st

from corporate_team import run_team


# ============================================================
# PERSISTENT ASYNC WORKER
# ============================================================

class AsyncWorker:
    """
    Runs AutoGen workflows on one persistent asyncio event loop.

    Streamlit reruns the script frequently, so the worker keeps
    one asyncio event loop alive for the session.
    """

    def __init__(self):

        self.loop = asyncio.new_event_loop()

        self.thread = threading.Thread(
            target=self._run_loop,
            name="autogen-async-worker",
            daemon=True,
        )

        self.thread.start()

    def _run_loop(self):

        asyncio.set_event_loop(self.loop)

        try:

            self.loop.run_forever()

        finally:

            self._cleanup_loop()

    def _cleanup_loop(self):

        try:

            pending_tasks = asyncio.all_tasks(
                self.loop
            )

            for task in pending_tasks:
                task.cancel()

            if pending_tasks:

                self.loop.run_until_complete(
                    asyncio.gather(
                        *pending_tasks,
                        return_exceptions=True,
                    )
                )

            self.loop.run_until_complete(
                self.loop.shutdown_asyncgens()
            )

        except Exception as error:

            print(
                f"[ASYNC CLEANUP WARNING] {error}"
            )

        finally:

            if not self.loop.is_closed():

                self.loop.close()

    def run(self, coroutine):
        """
        Execute the AutoGen workflow on the persistent
        asyncio event loop.

        IMPORTANT:
        There is intentionally NO outer 120-second timeout.

        Individual agent timeouts are controlled by
        corporate_team.py.
        """

        if self.loop.is_closed():

            raise RuntimeError(
                "Async worker event loop is closed."
            )

        if not self.thread.is_alive():

            raise RuntimeError(
                "Async worker thread is not running."
            )

        future = asyncio.run_coroutine_threadsafe(
            coroutine,
            self.loop,
        )

        # ----------------------------------------------------
        # IMPORTANT
        # ----------------------------------------------------
        #
        # Do NOT use:
        #
        # future.result(timeout=120)
        #
        # The workflow already has agent-level timeout
        # protection inside corporate_team.py.
        #
        # Waiting here allows the complete workflow to finish.
        # ----------------------------------------------------

        return future.result()

    def stop(self):

        if self.loop.is_closed():

            return

        try:

            self.loop.call_soon_threadsafe(
                self.loop.stop
            )

        except RuntimeError as error:

            print(
                f"[ASYNC STOP WARNING] {error}"
            )


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

if "processing" not in st.session_state:

    st.session_state.processing = False


if "async_worker" not in st.session_state:

    st.session_state.async_worker = AsyncWorker()


if "messages" not in st.session_state:

    st.session_state.messages = []


if "pending_question" not in st.session_state:

    st.session_state.pending_question = None


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Corporate Agentic AI",
    page_icon="🤖",
    layout="wide",
)


# ============================================================
# HEADER
# ============================================================

st.title(
    "🤖 Corporate Agentic AI"
)

st.caption(
    "Multi-Agent Enterprise Assistant powered by "
    "Microsoft AutoGen + Local Qwen"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("System")

    st.success(
        "System Online"
    )

    st.markdown(
        "### Agents"
    )

    st.write(
        "🧭 Supervisor"
    )

    st.write(
        "📚 Knowledge Agent"
    )

    st.write(
        "📊 Analytics Agent"
    )

    st.write(
        "🌐 Web Research Agent"
    )

    st.write(
        "📄 Document/RAG Agent"
    )

    st.write(
        "✅ Quality Agent"
    )

    st.markdown("---")

    st.caption(
        "Microsoft AutoGen 0.7.5"
    )

    st.caption(
        "Local Qwen 2.5 3B"
    )

    st.caption(
        "Persistent Async Worker"
    )

    st.markdown("---")

    if st.button(
        "Clear conversation",
        disabled=st.session_state.processing,
    ):

        st.session_state.messages = []

        st.rerun()


# ============================================================
# MAIN SECTION
# ============================================================

st.subheader(
    "Enterprise AI Assistant"
)

st.info(
    "Ask a business, analytics, company-policy, "
    "or research question."
)


# ============================================================
# ACTIVE WORKFLOW STATUS
# ============================================================

if st.session_state.processing:

    st.warning(
        "⏳ Your question is being processed."
    )

    st.info(
        "The multi-agent workflow may take some time "
        "because the system uses local Qwen + RAG + "
        "Quality validation."
    )


# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )

        if message["role"] == "assistant":

            route = message.get(
                "route"
            )

            quality = message.get(
                "quality"
            )

            if route:

                st.caption(
                    f"Routed to: {route}"
                )

            if quality and quality != (
                "Quality review not required."
            ):

                with st.expander(
                    "Quality review"
                ):

                    st.markdown(
                        quality
                    )


# ============================================================
# CHAT INPUT
# ============================================================

user_question = st.chat_input(
    "Ask your question...",
    disabled=st.session_state.processing,
)


# ============================================================
# RECEIVE NEW QUESTION
# ============================================================

if user_question:

    user_question = user_question.strip()

    if not user_question:

        st.warning(
            "Please enter a question."
        )

        st.stop()

    if st.session_state.processing:

        st.stop()

    # --------------------------------------------------------
    # Store user message immediately
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_question,
            "route": None,
            "quality": None,
        }
    )

    st.session_state.processing = True

    st.session_state.pending_question = (
        user_question
    )

    st.rerun()


# ============================================================
# RUN PENDING WORKFLOW
# ============================================================

if (
    st.session_state.processing
    and st.session_state.pending_question
):

    question_to_run = (
        st.session_state.pending_question
    )

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "Routing to the right specialist and "
            "generating a response..."
        ):

            try:

                # ------------------------------------------------
                # IMPORTANT:
                #
                # No 120-second timeout here.
                #
                # corporate_team.py controls individual
                # agent execution timeouts.
                # ------------------------------------------------

                result = (
                    st.session_state.async_worker.run(
                        run_team(
                            question_to_run
                        )
                    )
                )

                if result is None:

                    answer = (
                        "Something went wrong while "
                        "processing this request and no "
                        "final answer was produced. "
                        "Please check the application logs "
                        "and try again."
                    )

                    route = None

                    quality = None

                else:

                    answer = result.get(
                        "specialist_response",
                        "No final answer was produced.",
                    )

                    route = result.get(
                        "route"
                    )

                    quality = result.get(
                        "quality_response"
                    )

                # ------------------------------------------------
                # DISPLAY ANSWER
                # ------------------------------------------------

                st.markdown(
                    answer
                )

                if route:

                    st.caption(
                        f"Routed to: {route}"
                    )

                if (
                    quality
                    and quality !=
                    "Quality review not required."
                ):

                    with st.expander(
                        "Quality review"
                    ):

                        st.markdown(
                            quality
                        )

            except asyncio.CancelledError:

                answer = (
                    "⚠️ The workflow was cancelled "
                    "before completion."
                )

                route = None

                quality = None

                st.error(
                    answer
                )

            except Exception as error:

                answer = (
                    "⚠️ An unexpected error occurred "
                    "while processing your request.\n\n"
                    f"Error: {error}"
                )

                route = None

                quality = None

                st.error(
                    answer
                )

    # ========================================================
    # SAVE ASSISTANT MESSAGE
    # ========================================================

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "route": route,
            "quality": quality,
        }
    )

    # ========================================================
    # RESET WORKFLOW STATE
    # ========================================================

    st.session_state.processing = False

    st.session_state.pending_question = None

    st.rerun()