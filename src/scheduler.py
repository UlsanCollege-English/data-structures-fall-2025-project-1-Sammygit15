from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# Required menu items
REQUIRED_MENU: Dict[str, int] = {
    "americano": 2,
    "latte": 3,
    "cappuccino": 3,
    "mocha": 4,
    "tea": 1,
    "macchiato": 2,
    "hot_chocolate": 4,
}

@dataclass
class Task:
    task_id: str
    remaining: int

class QueueRR:
    def __init__(self, queue_id: str, capacity: int) -> None:
        if capacity < 0:
            raise ValueError("Capacity must be non-negative")
        self.queue_id = queue_id
        self.capacity = capacity
        self._storage: List[Optional[Task]] = [None] * capacity
        self._head: int = 0
        self._tail: int = 0
        self._size: int = 0

    def is_full(self) -> bool:
        return self._size == self.capacity

    def is_empty(self) -> bool:
        return self._size == 0

    def enqueue(self, task: Task) -> bool:
        if self.is_full():
            return False
        self._storage[self._tail] = task
        self._tail = (self._tail + 1) % self.capacity
        self._size += 1
        return True

    def dequeue(self) -> Optional[Task]:
        if self.is_empty():
            return None
        task = self._storage[self._head]
        self._head = (self._head + 1) % self.capacity
        self._size -= 1
        return task

    def __len__(self) -> int:
        return self._size

    def __iter__(self):
        for i in range(self._size):
            index = (self._head + i) % self.capacity
            yield self._storage[index]

class Scheduler:
    def __init__(self) -> None:
        self._time: int = 0
        self._queues: Dict[str, QueueRR] = {}
        self._queue_order: List[str] = []
        self._task_counters: Dict[str, int] = {}
        self._skip_flags: Dict[str, bool] = {}
        self._weights: Dict[str, int] = {}  # Extra: queue weights (default=1)
        self._specials: Dict[str, List[Tuple[int,int,int]]] = {}  # item -> [(burst,start,end), ...]
        self._next_queue_index: int = 0

    # ----- Menu / state helpers -----
    def menu(self) -> Dict[str, int]:
        return REQUIRED_MENU.copy()

    def next_queue(self) -> Optional[str]:
        if not self._queue_order:
            return None
        return self._queue_order[self._next_queue_index]

    # ----- Commands -----
    def create_queue(self, queue_id: str, capacity: int) -> List[str]:
        if queue_id not in self._queues:
            new_queue = QueueRR(queue_id, capacity)
            self._queues[queue_id] = new_queue
            self._queue_order.append(queue_id)
            self._task_counters[queue_id] = 1
            self._skip_flags[queue_id] = False
            self._weights[queue_id] = 1
        return [f"time={self._time} event=create queue={queue_id}"]

    def enqueue(self, queue_id: str, item_name: str) -> List[str]:
        if item_name not in self.menu():
            print("Sorry, we don't serve that.")
            return [f"time={self._time} event=reject queue={queue_id} reason=unknown_item"]

        queue = self._queues.get(queue_id)
        if queue is None:
            return [f"time={self._time} event=error reason=unknown_queue"]

        task_num = self._task_counters[queue_id]
        task_id = f"{queue_id}-{task_num:03d}"

        if queue.is_full():
            print("Sorry, we're at capacity.")
            return [f"time={self._time} event=reject queue={queue_id} task={task_id} reason=full"]

        burst_time = self._get_burst(item_name)
        queue.enqueue(Task(task_id=task_id, remaining=burst_time))
        self._task_counters[queue_id] += 1
        return [f"time={self._time} event=enqueue queue={queue_id} task={task_id} remaining={burst_time}"]

    def _get_burst(self, item: str) -> int:
        """Return current burst for an item, considering specials."""
        burst = self.menu()[item]
        specials = self._specials.get(item, [])
        for b, start, end in specials:
            if start <= self._time < end:
                return b
        return burst

    def mark_skip(self, queue_id: str) -> List[str]:
        if queue_id in self._queues:
            self._skip_flags[queue_id] = True
            return [f"time={self._time} event=skip queue={queue_id}"]
        return [f"time={self._time} event=error reason=unknown_queue"]

    def special(self, item: str, burst: int, start: int, end: int) -> List[str]:
        """Override burst for an item during [start, end)."""
        if item not in self._specials:
            self._specials[item] = []
        self._specials[item].append((burst, start, end))
        return [f"time={self._time} event=special item={item} burst={burst} start={start} end={end}"]

    def set_weight(self, queue_id: str, weight: int) -> List[str]:
        if queue_id in self._queues and weight > 0:
            self._weights[queue_id] = weight
            return [f"time={self._time} event=setweight queue={queue_id} weight={weight}"]
        return [f"time={self._time} event=error reason=invalid_weight_or_queue"]

    def run(self, quantum: int, steps: Optional[int]) -> List[str]:
        num_queues = len(self._queue_order)
        if num_queues == 0:
            return []
        if steps is not None and not (1 <= steps <= num_queues):
            return [f"time={self._time} event=error reason=invalid_steps"]

        logs = []
        turns_to_run = steps if steps is not None else float('inf')
        turns_done = 0

        while True:
            q_id = self.next_queue()
            if not q_id:
                break
            queue = self._queues[q_id]
            logs.append(f"time={self._time} event=run queue={q_id}")

            if self._skip_flags.get(q_id):
                self._skip_flags[q_id] = False
            elif not queue.is_empty():
                task = queue.dequeue()
                if task:
                    work_quantum = quantum * self._weights.get(q_id, 1)
                    work_time = min(task.remaining, work_quantum)
                    self._time += work_time
                    task.remaining -= work_time
                    if task.remaining > 0:
                        queue.enqueue(task)
                        logs.append(f"time={self._time} event=work queue={q_id} task={task.task_id} remaining={task.remaining}")
                    else:
                        logs.append(f"time={self._time} event=finish queue={q_id} task={task.task_id}")

            self._next_queue_index = (self._next_queue_index + 1) % num_queues
            logs.extend(self.display())

            turns_done += 1
            if steps is not None:
                if turns_done >= turns_to_run:
                    break
            else:
                all_empty = all(q.is_empty() for q in self._queues.values())
                no_skips = not any(self._skip_flags.values())
                if all_empty and no_skips:
                    break
        return logs

    # ----- Display -----
    def display(self) -> List[str]:
        lines = []
        next_q = self.next_queue() or "none"
        lines.append(f"display time={self._time} next={next_q}")

        menu_items = sorted(self.menu().items())
        menu_str = ",".join([f"{k}:{v}" for k, v in menu_items])
        lines.append(f"display menu=[{menu_str}]")

        for q_id in self._queue_order:
            queue = self._queues[q_id]
            cap = queue.capacity
            size = len(queue)
            skip_str = " [ skip]" if self._skip_flags.get(q_id) else ""
            weight_str = f" w={self._weights[q_id]}" if self._weights.get(q_id, 1) != 1 else ""
            tasks_list = [f"{task.task_id}:{task.remaining}" for task in queue if task]
            tasks_str = ",".join(tasks_list)
            lines.append(f"display {q_id} [{size}/{cap}]{skip_str}{weight_str} -> [{tasks_str}]")

        return lines
