"""NL -> SPARQL -> execute -> NL answer orchestration for the M150-Onto chatbot."""

from dataclasses import dataclass, field

import pyoxigraph

from chatbot import llm_client
from chatbot.schema_context import INDIVIDUAL_PREFIX


@dataclass
class AnswerResult:
    question: str
    sparql: str = ""
    bindings: list[dict[str, str]] = field(default_factory=list)
    answer: str = ""
    retried: bool = False
    error: str | None = None


def _run_query(store: pyoxigraph.Store, sparql: str) -> list[dict[str, str]]:
    results = store.query(sparql)
    # Variable.__str__ returns "?name", but QuerySolution indexing needs the bare name.
    var_names = [str(v).lstrip("?") for v in results.variables]
    rows = []
    for solution in results:
        row = {}
        for name in var_names:
            value = solution[name]
            row[name] = str(value) if value is not None else None
        rows.append(row)
    return rows


def _bindings_to_text(bindings: list[dict[str, str]]) -> str:
    if not bindings:
        return "(no rows)"
    lines = []
    for row in bindings:
        lines.append(", ".join(f"{k}={v}" for k, v in row.items()))
    return "\n".join(lines)


def _strip_placeholder_prefix(text: str) -> str:
    return text.replace(INDIVIDUAL_PREFIX, "")


def answer_question(
    store: pyoxigraph.Store,
    question: str,
    verbose: bool = False,
    history: list[tuple[str, str]] | None = None,
) -> AnswerResult:
    result = AnswerResult(question=question)

    sparql = llm_client.generate_sparql(question, history=history)
    result.sparql = sparql
    bindings: list[dict[str, str]] = []
    query_error: str | None = None

    try:
        bindings = _run_query(store, sparql)
    except (SyntaxError, OSError) as exc:
        query_error = str(exc)

    if query_error is not None:
        result.retried = True
        retry_note = f"That query failed with error: {query_error}\nFix it and try again."
        sparql = llm_client.generate_sparql(question, retry_note=retry_note, history=history)
        result.sparql = sparql
        try:
            bindings = _run_query(store, sparql)
            query_error = None
        except (SyntaxError, OSError) as exc:
            query_error = str(exc)

    elif not bindings:
        result.retried = True
        retry_note = (
            "That query ran but returned zero rows -- it is likely using the wrong property, "
            "individual, or direction. Reconsider the schema rules and try again."
        )
        retry_sparql = llm_client.generate_sparql(question, retry_note=retry_note, history=history)
        try:
            retry_bindings = _run_query(store, retry_sparql)
        except (SyntaxError, OSError):
            retry_bindings = []
        if retry_bindings:
            sparql = retry_sparql
            result.sparql = sparql
            bindings = retry_bindings

    if query_error is not None:
        result.error = query_error
        result.answer = (
            "I couldn't translate that into a valid query against the ontology. "
            "Try rephrasing the question."
        )
        return result

    result.bindings = bindings
    answer = llm_client.compose_answer(question, sparql, _bindings_to_text(bindings))
    result.answer = _strip_placeholder_prefix(answer)
    return result
