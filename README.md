[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/JWEh_q2R)
# Multi-Queue Round-Robin Café (Interactive CLI)
This project simulates a café with multiple order queues served fairly using a Round-Robin scheduler. Each queue represents a customer type (e.g., Mobile, Walk-Ins, Faculty) with a maximum capacity. Orders have preparation times based on the menu item.
The scheduler supports:
Round-Robin order serving,
Quantum-based time slices,
Queue skipping,
Weighted fairness,
Menu specials,

## How to run

Make sure you are in the project root directory.
Run the interactive CLI: python -m src.cli
Enter commands line by line,commands like:

CREATE Mobile 2,
CREATE WalkIns 2,
ENQ Mobile latte,
ENQ WalkIns tea,
SPECIAL latte 1 2 5,
SETWEIGHT Mobile 2,
SKIP WalkIns,
RUN 1 2,

A blank line ends the session and prints: Break time!


## How to run tests locally
python -m pytest -q ,
Expected output: All tests pass (e.g: 8 passed).

## Complexity Notes
Queue design: Circular buffer (QueueRR) for O(1) enqueue/dequeue., 
Time complexity: Enqueue/dequeue: O(1) amortized,
Run: O(#turns + total_minutes_worked),
Space complexity: O(N) tasks + metadata.

Edge Cases:
1. Tasks rejected if queue is full or item is unknown.
2. RUN validates 1 ≤ steps ≤ #queues.
3. Task IDs auto-increment and are zero-padded: <queue_id>-001, <queue_id>-002, …
4. Skipped queues are recorded but time does not advance if empty.
5. Display is printed after each RUN turn only.
6. Messages for errors:
Sorry, we're at capacity.
Sorry, we don't serve that.

## Project Structure 

src/
├── cli.py               # CLI interface (user input)
├── parser.py            # Command parser
├── scheduler.py         # Scheduler + queue logic
tests/
├── public               # Provided test cases
README.md                # This file


##  Author

Created by: Sammygit15,
Assigned By: Prof. Benjamin William Slater, 
Course: Data Structures – Fall 2025,
Ulsan College, South Korea