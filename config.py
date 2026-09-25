from autogen_ext.models.ollama import OllamaChatCompletionClient


# ============================================================
# LOCAL QWEN MODEL
# ============================================================

model_client = OllamaChatCompletionClient(
    model="qwen2.5:3b",
    host="http://localhost:11434",
)