"""
Interactive CLI with Extra Credit Support:
- Reads lines from stdin.
- A blank line ends the session and prints "Break time!".
- Commands handled: CREATE, ENQ, SKIP, RUN, SPECIAL, SETWEIGHT.
- RUN prints logs and, after each turn, the café display including skips and weights.
"""

import sys
from typing import List
from src.parser import parse_command
from src.scheduler import Scheduler


def main() -> None:
    sched = Scheduler()

    for raw in sys.stdin:
        line = raw.rstrip("\n")

        # Blank line ends session
        if line == "":
            print("Break time!")
            return

        # Ignore comment lines
        if line.startswith("#"):
            continue

        parsed = parse_command(line)
        logs: List[str] = []

        if parsed is None:
            continue

        cmd, args = parsed

        try:
            if cmd == "CREATE":
                if len(args) != 2:
                    logs.append("time=? event=error reason=bad_args")
                else:
                    qid, cap_str = args
                    logs.extend(sched.create_queue(qid, int(cap_str)))

            elif cmd == "ENQ":
                if len(args) != 2:
                    logs.append("time=? event=error reason=bad_args")
                else:
                    qid, item = args
                    logs.extend(sched.enqueue(qid, item))

            elif cmd == "SKIP":
                if len(args) != 1:
                    logs.append("time=? event=error reason=bad_args")
                else:
                    (qid,) = args
                    logs.extend(sched.mark_skip(qid))

            elif cmd == "RUN":
                if not (1 <= len(args) <= 2):
                    logs.append("time=? event=error reason=bad_args")
                else:
                    quantum = int(args[0])
                    steps = int(args[1]) if len(args) == 2 else None
                    run_logs = sched.run(quantum, steps)
                    logs.extend(run_logs)
                    
            elif cmd == "SPECIAL":
                if len(args) != 4:
                    logs.append("time=? event=error reason=bad_args")
                else:
                    item = args[0]
                    burst, start, end = map(int, args[1:])
                    logs.extend(sched.special(item, burst, start, end))

            elif cmd == "SETWEIGHT":
                if len(args) != 2:
                    logs.append("time=? event=error reason=bad_args")
                else:
                    qid = args[0]
                    weight = int(args[1])
                    logs.extend(sched.set_weight(qid, weight))

            else:
                logs.append("time=? event=error reason=unknown_command")

        except ValueError:
            logs.append("time=? event=error reason=bad_args")
        except Exception as e:
            logs.append(f"time=? event=error reason=exception:{type(e).__name__}")

        if logs:
            print("\n".join(logs))


if __name__ == "__main__":
    main()
