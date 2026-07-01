"""Startup ASCII-art splash banner for the OntoParser CLI."""

_BANNER_ART = r"""
                                   RWTH
                                  o
                                 /|\    <- jumping for joy
                                 / \
                                _____
                            .-'  ? '-.
                           /  [?????]  \
                          |   [?????]   |
                          |   [?????]   |
                           \  [?????]  /
                            '-.....-'
   ___       _        ____
  / _ \ _ __ | |_ ___ |  _ \ __ _ _ __ ___  ___ _ __
 | | | | '_ \| __/ _ \| |_) / _` | '__/ __|/ _ \ '__|
 | |_| | | | | || (_) |  __/ (_| | |  \__ \  __/ |
  \___/|_| |_|\__\___/|_|   \__,_|_|  |___/\___|_|
"""

_CREDIT_LINE = (
    "Developed by Luis Jamora and Raquel Valles, as part of the KaSyTwin Project."
)


def print_banner(log=None) -> None:
    """Prints the OntoParser ASCII splash art followed by the project credit line.

    If `log` is given (a RunLogger), the same content is also appended to the run log.
    """
    print(_BANNER_ART)
    print(_CREDIT_LINE)
    print()
    if log is not None:
        log.write(_BANNER_ART)
        log.write(_CREDIT_LINE)
