"""Writes a clean, timestamped transcript of a parser run to disk."""

from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[1] / "logs"


class RunLogger:
    """Appends clean, human-readable run output to a timestamped log file.

    Unlike the live terminal, this omits intermediate progress-bar redraw frames
    (carriage-return noise) and keeps only the banner, load/save messages,
    warnings, and the final progress-bar state.
    """

    def __init__(self):
        LOG_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.path = LOG_DIR / f"parse_{timestamp}.log"
        self._file = open(self.path, "w", encoding="utf-8")

    def write(self, message: str) -> None:
        self._file.write(message.rstrip("\n") + "\n")
        self._file.flush()

    def close(self) -> None:
        self._file.close()
