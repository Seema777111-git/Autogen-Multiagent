import json
from pathlib import Path


# ============================================================
# LONG-TERM MEMORY
# ============================================================

MEMORY_FILE = Path("conversation_memory.json")


def load_memory():
    """
    Load previously saved conversations.
    """

    if not MEMORY_FILE.exists():
        return []

    try:

        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return []


def save_memory(question, answer):
    """
    Save a question and answer permanently.
    """

    memories = load_memory()

    memories.append(
        {
            "question": question,
            "answer": answer
        }
    )

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            memories,
            file,
            indent=2,
            ensure_ascii=False
        )


def get_recent_memory(limit=3):
    """
    Return the most recent conversations.
    """

    memories = load_memory()

    return memories[-limit:]