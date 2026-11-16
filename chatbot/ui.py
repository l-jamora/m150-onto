"""Terminal presentation for the M150-Onto chatbot REPL.

Sole module that imports `rich` -- `repl.py` calls into this module instead of
touching rich types or markup strings directly.
"""

from rich.columns import Columns
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from chatbot import llm_client

STYLE_MASCOT = "bright_blue"
STYLE_TITLE = "bold bright_blue"
STYLE_LABEL = "blue"
STYLE_ACCENT = "cyan"
STYLE_DIM = "dim"
STYLE_BORDER_DIM = "bright_black"

MASCOT = r"""
   __________
  [__________]
   | .  . : |
   | :  .   |
   | .  : . |
~~~|________|~~~
  ~  ~  ~  ~
"""

_COMMANDS = [
    (":verbose", "toggle SPARQL query and bindings output"),
    (":history", "toggle conversation memory across turns"),
    (":help", "show this panel again"),
    ("exit / quit", "leave the chatbot"),
]


def _commands_table() -> Table:
    table = Table(box=None, show_header=False, padding=(0, 1, 0, 0))
    table.add_column(style="bold " + STYLE_ACCENT, no_wrap=True)
    table.add_column(style=STYLE_DIM)
    for command, description in _COMMANDS:
        table.add_row(command, description)
    return table


def _build_banner_renderable() -> Panel:
    info = Group(
        Text("M150-Onto Chatbot", style=STYLE_TITLE),
        Text("Natural-language SPARQL over the sewer-network ontology", style=STYLE_DIM),
        Text(""),
        Text.assemble(("Model: ", STYLE_LABEL), (llm_client.get_model_name(), STYLE_ACCENT)),
        Text(""),
        _commands_table(),
    )
    body = Columns(
        [Text(MASCOT, style=STYLE_MASCOT), info],
        padding=(0, 3),
        expand=False,
    )
    return Panel(body, border_style=STYLE_MASCOT, padding=(1, 2))


def render_banner(console: Console) -> None:
    console.print(_build_banner_renderable())


def prompt(console: Console) -> str:
    return console.input(f"\n[bold {STYLE_LABEL}]>[/bold {STYLE_LABEL}] ").strip()


def print_verbose(console: Console, sparql: str, bindings, retried: bool) -> None:
    sparql_title = "SPARQL query (retried)" if retried else "SPARQL query"
    console.print()
    console.print(
        Panel(
            Text(sparql, style=STYLE_ACCENT),
            title=sparql_title,
            title_align="left",
            border_style=STYLE_BORDER_DIM,
            padding=(0, 1),
        )
    )
    console.print(
        Panel(
            Text(str(bindings), style=STYLE_DIM),
            title="bindings",
            title_align="left",
            border_style=STYLE_BORDER_DIM,
            padding=(0, 1),
        )
    )
