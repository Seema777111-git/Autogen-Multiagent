from autogen_ext.models.ollama import OllamaChatCompletionClient


# ============================================================
# LOCAL QWEN MODEL
# ============================================================

model_client = OllamaChatCompletionClient(
    model="qwen2.5:3b",
    host="http://localhost:11434",
    options={
        # Lower temperature = less rambling, sticks closer to
        # the instructed format instead of free-associating.
        "temperature": 0.1,
        # Hard cap on response length so a verbose answer gets
        # cut off rather than running into a full paragraph.
        "num_predict": 250,
    },
)