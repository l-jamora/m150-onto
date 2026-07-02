"""Azure OpenAI client wrapper for the M150-Onto chatbot.

Mirrors the working call pattern in the repo's local, gitignored azure.test.py
scratch file: an AzureOpenAI client pointed at the user's own Azure resource,
authenticated via the AZURE_OPENAI_API_KEY environment variable.

Two LLM calls happen per question (generate_sparql, then compose_answer), and
each can be retried once by sparql_pipeline.py -- so a single question can cost
up to 4 Azure OpenAI calls. Worth knowing if this shows up in an Azure billing
dashboard.
"""

import os
import re

from openai import AzureOpenAI

from chatbot.schema_context import (
    ANSWER_COMPOSITION_SYSTEM_PROMPT,
    FEW_SHOT_EXAMPLES,
    SPARQL_GENERATION_SYSTEM_PROMPT,
)

AZURE_ENDPOINT = "https://kasytwinressource.services.ai.azure.com"
AZURE_API_VERSION = "2024-10-21"
DEPLOYMENT_NAME = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-5.4-mini")

_client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version=AZURE_API_VERSION,
)


def get_model_name() -> str:
    """Single source of truth for the deployment name shown in the UI."""
    return DEPLOYMENT_NAME

_FENCE_RE = re.compile(r"^```(?:sparql)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def _strip_code_fences(text: str) -> str:
    return _FENCE_RE.sub("", text).strip()


def _few_shot_messages() -> list[dict]:
    messages = []
    for question, sparql in FEW_SHOT_EXAMPLES:
        messages.append({"role": "user", "content": question})
        messages.append({"role": "assistant", "content": sparql})
    return messages


def _history_message(history: list[tuple[str, str]]) -> dict:
    turns = "\n".join(f"Q: {q}\nA: {a}" for q, a in history)
    content = (
        "Conversation history, most recent last. Use this only to resolve pronouns/context "
        "(e.g. \"it\", \"that pipe\") in the question below -- do not treat it as new data to "
        f"query for:\n\n{turns}"
    )
    return {"role": "user", "content": content}


def generate_sparql(
    question: str,
    retry_note: str | None = None,
    history: list[tuple[str, str]] | None = None,
) -> str:
    messages = [{"role": "system", "content": SPARQL_GENERATION_SYSTEM_PROMPT}]
    messages.extend(_few_shot_messages())
    if history:
        messages.append(_history_message(history))
    if retry_note:
        messages.append({"role": "user", "content": question})
        messages.append({"role": "user", "content": retry_note})
    else:
        messages.append({"role": "user", "content": question})

    response = _client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=messages,
        temperature=0.2,
    )
    return _strip_code_fences(response.choices[0].message.content)


def compose_answer(question: str, sparql: str, bindings_as_text: str) -> str:
    user_content = (
        f"Question: {question}\n\nSPARQL query run:\n{sparql}\n\nResult rows:\n{bindings_as_text}"
    )
    response = _client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": ANSWER_COMPOSITION_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()
