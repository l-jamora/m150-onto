"""CLI REPL for the M150-Onto chatbot.

Run: python -m chatbot.repl
"""

import sys

import pyoxigraph
from rich.console import Console

from chatbot import ui
from chatbot.build_store import DEFAULT_STORE_PATH
from chatbot.sparql_pipeline import answer_question

# How many prior (question, answer) turns to send back to the model when
# history mode is on. Bounds token cost as a session gets long.
HISTORY_MAX_TURNS = 5


def main() -> None:
    console = Console()

    if not DEFAULT_STORE_PATH.exists() or not any(DEFAULT_STORE_PATH.iterdir()):
        console.print(
            f"No triplestore found at {DEFAULT_STORE_PATH}.\n"
            "Run `python -m chatbot.build_store` first.",
            style="red",
        )
        sys.exit(1)

    store = pyoxigraph.Store.read_only(str(DEFAULT_STORE_PATH))
    verbose = False
    history_enabled = False
    conversation_history: list[tuple[str, str]] = []

    ui.render_banner(console)

    while True:
        try:
            question = ui.prompt(console)
        except (EOFError, KeyboardInterrupt):
            console.print()
            break

        if not question:
            continue
        if question.lower() in ("exit", "quit"):
            break
        if question == ":verbose":
            verbose = not verbose
            console.print(f"[blue]verbose[/blue] = {verbose}")
            continue
        if question == ":history":
            history_enabled = not history_enabled
            console.print(f"[blue]history[/blue] = {history_enabled}")
            continue
        if question == ":help":
            ui.render_banner(console)
            continue

        history = conversation_history[-HISTORY_MAX_TURNS:] if history_enabled else None
        result = answer_question(store, question, verbose=verbose, history=history)
        conversation_history.append((question, result.answer))

        if verbose:
            ui.print_verbose(console, result.sparql, result.bindings, result.retried)

        console.print(f"\n{result.answer}")


if __name__ == "__main__":
    main()
