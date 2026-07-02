"""Regression eval for the M150-Onto chatbot.

Built from the demonstration questions in the user's Obsidian doc
("GraphDB M150-Onto TTYG-Demonstration.md") -- real questions with
hand-verified expected facts (checked directly against the store, not
invented), run through the actual pipeline end-to-end.

This is NOT a unit test: it makes real Azure OpenAI calls (see
llm_client.py's module docstring for the per-question call budget) and is
nondeterministic (temperature=0.2). Run it after any change to
schema_context.py, sparql_pipeline.py, or schema_validate.py to catch
regressions like a property name silently reverting to a wrong guess,
instead of hand-testing one question at a time in the REPL.

Not every question has a strict pass/fail check -- a few (asset-type
disjointness, time-relative reasoning, the aspirational inspection-cycle
question) are marked MANUAL because grading free-text NL reliably by
substring match isn't practical; they still run and print so you can eyeball
them.

Run: python -m chatbot.eval [--verbose]
"""

import argparse
import sys
from dataclasses import dataclass
from typing import Callable

import pyoxigraph

from chatbot.build_store import DEFAULT_STORE_PATH
from chatbot.sparql_pipeline import AnswerResult, answer_question

Check = Callable[[AnswerResult], bool]


def _contains_all(*needles: str) -> Check:
    def check(result: AnswerResult) -> bool:
        haystack = result.answer.lower()
        return all(needle.lower() in haystack for needle in needles)

    return check


def _contains_any(*needles: str) -> Check:
    def check(result: AnswerResult) -> bool:
        haystack = result.answer.lower()
        return any(needle.lower() in haystack for needle in needles)

    return check


def _all_of(*checks: Check) -> Check:
    return lambda result: all(check(result) for check in checks)


def _min_bindings(n: int) -> Check:
    return lambda result: len(result.bindings) >= n


def _non_empty(result: AnswerResult) -> bool:
    return len(result.bindings) > 0


@dataclass
class EvalCase:
    question: str
    check: Check | None
    note: str = ""


CASES: list[EvalCase] = [
    # 1. Warm-up / schema literacy
    EvalCase(
        "What information do you have about pipe section 1204015?",
        _non_empty,
    ),
    EvalCase(
        "Which streets and districts does this network cover?",
        _all_of(_contains_all("Ortsmitte"), _contains_any("Schlossallee", "Parkstrasse")),
        note="Ground truth: streets Schlossallee/Parkstrasse, district Ortsmitte.",
    ),
    # 2. Provenance and accountability
    EvalCase(
        "Who inspected pipe section 1204015, and who was the site manager on that inspection?",
        _contains_all("Potter", "Voldemort"),
        note="The hasSiteManagement bug from last session -- regression guard.",
    ),
    EvalCase(
        "Which inspections did H. Potter carry out?",
        _min_bindings(2),
        note="Ground truth: 9 inspections via isInspectorIn (inverse-property demo).",
    ),
    EvalCase(
        "What camera system and video file were used for the inspection of 1204015?",
        _contains_all("Dreh"),
        note="The hasCameraSystem/hasVideoFile bug from this session -- regression guard. "
        'Ground truth: hasCameraSystemUsed -> "Dreh-Schwenkkopf".',
    ),
    # 3. Network topology
    EvalCase(
        "Trace the flow path starting from pipe section 1204015 downstream through the network.",
        _contains_any("1204014"),
        note="Ground truth: 1204015's only direct node-shared neighbor is 1204014.",
    ),
    EvalCase(
        "If pipe section 1204013 has to be shut down for repair, which other sections and nodes "
        "are directly connected to it?",
        _contains_any("1204014", "1204012"),
        note="Ground truth: 1204013 is directly node-connected to both 1204014 and 1204012.",
    ),
    # 4. Condition-based prioritization
    EvalCase(
        "Which conditions were recorded on pipe section 1204015, and at what station distances?",
        _min_bindings(3),
        note="Ground truth: 19 condition individuals recorded via isChildOf.",
    ),
    EvalCase(
        "Are there any root intrusion or crack findings in the inspected sections?",
        _contains_any("riss", "crack", "wurzel", "root"),
        note='Ground truth: hasLongText contains "Riss" and "Komplexes Wurzelwerk" on multiple '
        "conditions.",
    ),
    EvalCase(
        "Which pipe section has the most recorded defects, and what are they?",
        _non_empty,
        note="Ground truth: 1204015 and 1204014 tie at 19 defects each -- no single correct "
        "winner, smoke test only.",
    ),
    # 5. Inference vs. explicit data
    EvalCase(
        "What material is pipe section 1204014 made of, and what other assets use that same "
        "material?",
        _contains_any("beton", "concrete"),
        note="Ground truth: hasMaterial -> M150_RT105_B (Beton/Concrete); isMaterialOf also links "
        "1204012 and 1204013.",
    ),
    EvalCase(
        "Is pipe section 1204015 the same type of asset as node 1204015?",
        None,
        note="Ground truth: Node owl:disjointWith PipeSection -- correct answer is no. Not "
        "auto-graded (NL phrasing varies); review manually.",
    ),
    # 6. Time-relative reasoning
    EvalCase(
        "How long ago was pipe section 1204015 last inspected?",
        None,
        note="Inspection date 2006-04-07 -- date-dependent, review manually.",
    ),
    EvalCase(
        "Based on standard DWA M150 inspection cycles, is this pipe section due for "
        "reinspection?",
        None,
        note="Aspirational per the source doc: the ontology has no inspection-interval data, so "
        "the model should decline or hedge rather than hallucinate a number. Review manually.",
    ),
]


def run(verbose: bool) -> int:
    if not DEFAULT_STORE_PATH.exists() or not any(DEFAULT_STORE_PATH.iterdir()):
        print(f"No store at {DEFAULT_STORE_PATH}. Run `python -m chatbot.build_store` first.")
        return 1

    store = pyoxigraph.Store.read_only(str(DEFAULT_STORE_PATH))
    passed = failed = manual = 0

    for case in CASES:
        result = answer_question(store, case.question)

        if case.check is None:
            manual += 1
            status = "MANUAL"
        elif case.check(result):
            passed += 1
            status = "PASS"
        else:
            failed += 1
            status = "FAIL"

        print(f"[{status}] {case.question}")
        if case.note:
            print(f"        note: {case.note}")
        if result.retried:
            print("        (retried)")
        if verbose or status == "FAIL":
            print(f"        SPARQL:\n{result.sparql}")
            print(f"        bindings: {result.bindings}")
        print(f"        answer: {result.answer}\n")

    total = passed + failed
    print(f"{passed}/{total} auto-graded checks passed, {manual} marked for manual review.")
    return 1 if failed else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verbose", action="store_true", help="print SPARQL/bindings for every case, not just failures"
    )
    args = parser.parse_args()
    sys.exit(run(args.verbose))


if __name__ == "__main__":
    main()
