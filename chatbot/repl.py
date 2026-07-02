"""CLI REPL for the M150-Onto chatbot.

Run: python -m chatbot.repl
"""

import sys

import pyoxigraph

from chatbot.build_store import DEFAULT_STORE_PATH
from chatbot.sparql_pipeline import answer_question

# How many prior (question, answer) turns to send back to the model when
# history mode is on. Bounds token cost as a session gets long.
HISTORY_MAX_TURNS = 5


def main() -> None:
    if not DEFAULT_STORE_PATH.exists() or not any(DEFAULT_STORE_PATH.iterdir()):
        print(
            f"No triplestore found at {DEFAULT_STORE_PATH}.\n"
            "Run `python -m chatbot.build_store` first."
        )
        sys.exit(1)

    store = pyoxigraph.Store.read_only(str(DEFAULT_STORE_PATH))
    verbose = False
    history_enabled = False
    conversation_history: list[tuple[str, str]] = []

    print("M150-Onto chatbot. Type a question, ':verbose' to toggle SPARQL/bindings output, "
          "':history' to toggle conversation memory, 'exit' to quit.")

    while True:
        try:
            question = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not question:
            continue
        if question.lower() in ("exit", "quit"):
            break
        if question == ":verbose":
            verbose = not verbose
            print(f"verbose = {verbose}")
            continue
        if question == ":history":
            history_enabled = not history_enabled
            print(f"history = {history_enabled}")
            continue

        history = conversation_history[-HISTORY_MAX_TURNS:] if history_enabled else None
        result = answer_question(store, question, verbose=verbose, history=history)
        conversation_history.append((question, result.answer))

        if verbose:
            print(f"\n[SPARQL]{' (retried)' if result.retried else ''}\n{result.sparql}")
            print(f"\n[bindings]\n{result.bindings}")

        print(f"\n{result.answer}")


if __name__ == "__main__":
    main()
