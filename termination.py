# ============================================================
# FINAL ANSWER / TERMINATION CONTROL
# ============================================================


FINAL_ANSWER_SIGNAL = "FINAL_ANSWER"


def mark_final_answer(answer: str) -> str:
    """
    Add an explicit final-answer signal.
    """

    return f"{FINAL_ANSWER_SIGNAL}\n{answer}"


def is_final_answer(response: str) -> bool:
    """
    Check whether the response contains
    the explicit final-answer signal.
    """

    if not response:
        return False

    return response.startswith(
        FINAL_ANSWER_SIGNAL
    )


def remove_final_answer_signal(response: str) -> str:
    """
    Remove the internal termination signal
    before displaying the answer to the user.
    """

    if not response:
        return response

    if response.startswith(
        FINAL_ANSWER_SIGNAL
    ):

        return response[
            len(FINAL_ANSWER_SIGNAL):
        ].strip()

    return response