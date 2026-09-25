# ============================================================
# HUMAN-IN-THE-LOOP APPROVAL
# ============================================================


def requires_human_approval(user_question: str) -> bool:
    """
    Identify requests that should require human approval.
    """

    sensitive_keywords = [

        "delete",
        "terminate",
        "disable",
        "remove access",
        "approve vendor",
        "reject vendor",
        "send payment",
        "make payment",
        "change employee record",
        "change salary",
        "security incident",
        "grant access",

    ]

    question = user_question.lower()

    for keyword in sensitive_keywords:

        if keyword in question:

            return True

    return False


def request_human_approval(user_question: str) -> bool:
    """
    Ask a human to approve or reject a sensitive request.
    """

    print(
        "\n=============================================="
    )

    print(
        "        HUMAN APPROVAL REQUIRED"
    )

    print(
        "=============================================="
    )

    print(
        "\nSensitive request detected:"
    )

    print(
        user_question
    )

    print(
        "\nApprove this request?"
    )

    print(
        "Type: yes / no"
    )

    decision = input(
        "\nApproval: "
    )

    return decision.lower().strip() in {

        "yes",
        "y"

    }