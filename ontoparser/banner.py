"""Startup ASCII-art splash banner for the OntoParser CLI."""

from rich.columns import Columns
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text

STYLE_MASCOT = "bright_blue"
STYLE_TITLE = "bold bright_blue"
STYLE_DIM = "dim"

MASCOT = r"""
   __________
  [__________]
   | .  . : |
   | :  .   |
   | .  : . |
~~~|________|~~~
  ~  ~  ~  ~
"""

_DESCRIPTION = "DWA M 150 XML -> OWL parser for the M150-Onto ontology"
_CREDIT_LINE = (
    "Developed by Luis Jamora and Raquel Valles, as part of the KaSyTwin Project."
)


def _build_banner_renderable() -> Panel:
    info = Group(
        Text("OntoParser", style=STYLE_TITLE),
        Text(_DESCRIPTION, style=STYLE_DIM),
        Text(""),
        Text(_CREDIT_LINE, style=STYLE_DIM),
    )
    body = Columns(
        [Text(MASCOT, style=STYLE_MASCOT), info],
        padding=(0, 3),
        expand=False,
    )
    return Panel(body, border_style=STYLE_MASCOT, padding=(1, 2))


def print_banner(log=None) -> None:
    """Prints the OntoParser splash banner.

    If `log` is given (a RunLogger), the same content is also appended to the run log
    as plain text.
    """
    console = Console(record=True)
    console.print(_build_banner_renderable())
    if log is not None:
        log.write(console.export_text())
