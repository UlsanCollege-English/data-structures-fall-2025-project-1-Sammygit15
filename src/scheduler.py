"""
Scheduler + QueueRR implementation for the Multi-Queue Round-Robin Café project.
Supports SPECIAL (menu specials) and SETWEIGHT (weighted fairness).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

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
        self.queue_id = queue_id
        self.capacity = capacity
        self.data: List[Optional[Task]] = [None] * capacity if capacity > 0 else []
        self.head = 0
        self.tail = 0
        self.size = 0

    def enqueue(self, task: Task) -> bool:
        if self.size == self.capacity or self.capacity == 0:
            return False
        self.data[self.tail] = task
        self.tail = (self.tail + 1) % self.capacity
        self.size += 1
        return True

    def dequeue(self) -> Optional[Task]:
        if self.size == 0:
            return None
        task = self.data[self.head]
        self.data[self.head] = None
        self.head = (self.head + 1) % self.capacity
        self.size -= 1
        return task

    def __len__(self) -> int:
        return self.size

    def peek_front(self) -> Optional[Task]:
        return self.data[self.head] if self.size > 0 else None

class Scheduler:
    def __init__(self) -> None:
        self.time = 0
        self.queues: Dict[str, QueueRR] = {}
        self.order: List[str] = []
        self.id_counters: Dict[str, int] = {}
        self.skip_flags: Dict[str, bool] = {}
        self.rr_index = 0
        self._menu = dict(REQUIRED_MENU)
        self._specials: List[Tuple[str, int, int, int]] = []  # item_name, burst, start, end
        self._weights: Dict[str, int] = {}  # queue_id -> weight

    def menu(self) -> Dict[str, int]:
        return dict(self._menu)

    def next_queue(self) -> Optional[str]:
        if not self.order:
            return None
        return self.order[self.rr_index % len(self.order)]

    def create_queue(self, queue_id: str, capacity: int) -> List[str]:
        logs: List[str] = []
        if queue_id in self.queues or capacity < 0:
            logs.append(f"time={self.time} event=error queue={queue_id} reason=bad_create")
            return logs
        q = QueueRR(queue_id, capacity)
        self.queues[queue_id] = q
        self.order.append(queue_id)
        self.id_counters[queue_id] = 0
        self.skip_flags[queue_id] = False
        self._weights[queue_id] = 1  # default weight
        logs.append(f"time={self.time} event=create queue={queue_id}")
        return logs

    def enqueue(self, queue_id: str, item_name: str) -> List[str]:
        logs: List[str] = []
        if queue_id not in self.queues:
            logs.append(f"time={self.time} event=error queue={queue_id} reason=unknown_queue")
            return logs
        q = self.queues[queue_id]

        if item_name not in self._menu:
            print("Sorry, we don't serve that.")
            self.id_counters[queue_id] += 1
            task_id = f"{queue_id}-{self.id_counters[queue_id]:03d}"
            logs.append(f"time={self.time} event=reject queue={queue_id} task={task_id} reason=unknown_item")
            return logs

        # Apply special burst if any active
        remaining = self._menu[item_name]
        for itm, burst, start, end in self._specials:
            if itm == item_name and start <= self.time < end:
                remaining = burst
                break

        self.id_counters[queue_id] += 1
        task_id = f"{queue_id}-{self.id_counters[queue_id]:03d}"
        task = Task(task_id, remaining)
        if not q.enqueue(task):
            print("Sorry, we're at capacity.")
            logs.append(f"time={self.time} event=reject queue={queue_id} task={task_id} reason=full")
            return logs
        logs.append(f"time={self.time} event=enqueue queue={queue_id} task={task_id} remaining={remaining}")
        return logs

    def mark_skip(self, queue_id: str) -> List[str]:
        logs: List[str] = []
        if queue_id not in self.queues:
            logs.append(f"time={self.time} event=error queue={queue_id} reason=unknown_queue")
            return logs
        self.skip_flags[queue_id] = True
        logs.append(f"time={self.time} event=skip queue={queue_id}")
        return logs

    def special(self, item_name: str, burst: int, start_time: int, end_time: int) -> List[str]:
        logs: List[str] = []
        if item_name not in self._menu:
            logs.append(f"time={self.time} event=error reason=unknown_item")
            return logs
        self._specials.append((item_name, burst, start_time, end_time))
        logs.append(f"time={self.time} event=special item={item_name} burst={burst} start={start_time} end={end_time}")
        return logs

    def set_weight(self, queue_id: str, weight: int) -> List[str]:
        logs: List[str] = []
        if queue_id not in self.queues or weight <= 0:
            logs.append(f"time={self.time} event=error queue={queue_id} reason=bad_weight")
            return logs
        self._weights[queue_id] = weight
        logs.append(f"time={self.time} event=setweight queue={queue_id} weight={weight}")
        return logs

    def run(self, quantum: int, steps: Optional[int]) -> List[str]:
        logs: List[str] = []
        if not self.order:
            logs.append(f"time={self.time} event=error reason=no_queues")
            return logs
        if steps is not None:
            if steps < 1 or steps > len(self.order):
                logs.append(f"time={self.time} event=error reason=invalid_steps")
                return logs
            turn_limit = steps
        else:
            turn_limit = None

        turns_done = 0
        while True:
            qid = self.order[self.rr_index]
            queue = self.queues[qid]
            logs.append(f"time={self.time} event=run queue={qid}")

            if self.skip_flags[qid]:
                self.skip_flags[qid] = False
                self.rr_index = (self.rr_index + 1) % len(self.order)
                logs.extend(self.display())
                turns_done += 1
                if turn_limit and turns_done >= turn_limit:
                    break
                continue

            if len(queue) == 0:
                self.rr_index = (self.rr_index + 1) % len(self.order)
                logs.extend(self.display())
                turns_done += 1
                if turn_limit and turns_done >= turn_limit:
                    break
                continue

            task = queue.dequeue()
            if not task:
                self.rr_index = (self.rr_index + 1) % len(self.order)
                logs.extend(self.display())
                turns_done += 1
                if turn_limit and turns_done >= turn_limit:
                    break
                continue

            work_time = min(task.remaining, quantum * self._weights.get(qid, 1))
            self.time += work_time
            task.remaining -= work_time
            logs.append(f"time={self.time - work_time} event=work queue={qid} task={task.task_id} remaining={task.remaining + work_time}")
            if task.remaining == 0:
                logs.append(f"time={self.time} event=finish queue={qid} task={task.task_id}")
            else:
                queue.enqueue(task)

            self.rr_index = (self.rr_index + 1) % len(self.order)
            logs.extend(self.display())
            turns_done += 1

            if turn_limit and turns_done >= turn_limit:
                break
            if not turn_limit:
                if all(len(self.queues[q]) == 0 for q in self.order) and not any(self.skip_flags.values()):
                    break
        return logs

    def display(self) -> List[str]:
        out: List[str] = []
        next_qid = self.next_queue()
        next_str = next_qid if next_qid else "none"
        out.append(f"display time={self.time} next={next_str}")
        menu_items = ",".join(f"{name}:{minutes}" for name, minutes in sorted(self._menu.items()))
        out.append(f"display menu=[{menu_items}]")
        for qid in self.order:
            q = self.queues[qid]
            skip_flag = " [ skip]" if self.skip_flags[qid] else ""
            cap_str = f"[{len(q)}/{q.capacity}]"
            weight_str = f" w={self._weights.get(qid, 1)}" if self._weights.get(qid, 1) != 1 else ""
            tasks = []
            for i in range(q.size):
                idx = (q.head + i) % q.capacity if q.capacity > 0 else 0
                task = q.data[idx]
                if task:
                    tasks.append(f"{task.task_id}:{task.remaining}")
            tasks_str = ",".join(tasks)
            out.append(f"display {qid} {cap_str}{skip_flag}{weight_str} -> [{tasks_str}]")
        return out
