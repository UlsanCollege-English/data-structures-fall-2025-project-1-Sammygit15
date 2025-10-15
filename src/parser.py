"""
Minimal command parser for one line at a time.
Expected commands:
  CREATE <queue_id> <capacity>
  ENQ <queue_id> <item_name>
  SKIP <queue_id>
  RUN <quantum> [steps]
Lines beginning with '#' are comments. A *blank* line ends the session at the CLI layer.
"""

from typing import List, Tuple, Optional


def parse_command(line: str) -> Optional[Tuple[str, List[str]]]:
    """
    Return (COMMAND, args) or None for blank/comment-only lines.

    Do NOT raise; leave semantic checks to the scheduler and tests.
    Keep whitespace handling predictable.
    """
    s = line.strip()
    if not s or s.startswith("#"):
        return None
    parts = s.split()
    cmd, args = parts[0], parts[1:]
    cmd = cmd.upper()
    # Allowed commands; anything else still returns a tuple and is validated downstream.
    return cmd, args
