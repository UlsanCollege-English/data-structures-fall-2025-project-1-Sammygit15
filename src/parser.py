from typing import List, Tuple, Optional

def parse_command(line: str) -> Optional[Tuple[str, List[str]]]:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    parts = stripped.split()
    cmd = parts[0].upper()
    args = parts[1:]
    return cmd, args
