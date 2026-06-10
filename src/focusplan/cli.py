from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
DEFAULT_DB = Path.home() / ".local" / "share" / "focusplan" / "tasks.json"


@dataclass
class Task:
    id: int
    title: str
    due: str | None = None
    priority: str = "medium"
    minutes: int = 30
    tags: list[str] | None = None
    done: bool = False
    created_at: str = ""
    completed_at: str | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Task":
        return cls(
            id=int(raw["id"]),
            title=str(raw["title"]),
            due=raw.get("due"),
            priority=str(raw.get("priority", "medium")),
            minutes=int(raw.get("minutes", 30)),
            tags=list(raw.get("tags") or []),
            done=bool(raw.get("done", False)),
            created_at=str(raw.get("created_at", "")),
            completed_at=raw.get("completed_at"),
        )


def db_path() -> Path:
    return Path(os.environ.get("FOCUSPLAN_DB", DEFAULT_DB)).expanduser()


def load_tasks(path: Path | None = None) -> list[Task]:
    path = path or db_path()
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise SystemExit(f"Could not read task database: {path} is invalid JSON") from error
    return [Task.from_dict(item) for item in raw]


def save_tasks(tasks: list[Task], path: Path | None = None) -> None:
    path = path or db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(task) for task in tasks], indent=2) + "\n")


def parse_due(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized == "today":
        return date.today().isoformat()
    if normalized == "tomorrow":
        return (date.today() + timedelta(days=1)).isoformat()
    try:
        return date.fromisoformat(normalized).isoformat()
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "due date must be today, tomorrow, or YYYY-MM-DD"
        ) from error


def next_id(tasks: list[Task]) -> int:
    return max((task.id for task in tasks), default=0) + 1


def task_sort_key(task: Task) -> tuple[date, int, int, int]:
    due = date.max if task.due is None else date.fromisoformat(task.due)
    return (due, PRIORITY_ORDER[task.priority], task.minutes, task.id)


def format_task(task: Task) -> str:
    checkbox = "x" if task.done else " "
    due = task.due or "no due date"
    tags = "" if not task.tags else " #" + " #".join(task.tags)
    return (
        f"{task.id:>3}. [{checkbox}] {task.title} "
        f"({task.priority}, {task.minutes} min, due {due}){tags}"
    )


def add_task(args: argparse.Namespace) -> int:
    tasks = load_tasks()
    task = Task(
        id=next_id(tasks),
        title=args.title,
        due=args.due,
        priority=args.priority,
        minutes=args.minutes,
        tags=args.tag,
        created_at=datetime.now().isoformat(timespec="seconds"),
    )
    tasks.append(task)
    save_tasks(tasks)
    print(f"Added task {task.id}: {task.title}")
    return 0


def list_tasks(args: argparse.Namespace) -> int:
    tasks = load_tasks()
    visible = tasks if args.all else [task for task in tasks if not task.done]
    if args.tag:
        visible = [task for task in visible if args.tag in (task.tags or [])]
    visible = sorted(visible, key=task_sort_key)

    if not visible:
        print("No tasks found.")
        return 0
    for task in visible:
        print(format_task(task))
    return 0


def mark_done(args: argparse.Namespace) -> int:
    tasks = load_tasks()
    for task in tasks:
        if task.id == args.id:
            task.done = True
            task.completed_at = datetime.now().isoformat(timespec="seconds")
            save_tasks(tasks)
            print(f"Completed task {task.id}: {task.title}")
            return 0
    raise SystemExit(f"No task found with ID {args.id}")


def remove_task(args: argparse.Namespace) -> int:
    tasks = load_tasks()
    kept = [task for task in tasks if task.id != args.id]
    if len(kept) == len(tasks):
        raise SystemExit(f"No task found with ID {args.id}")
    save_tasks(kept)
    print(f"Removed task {args.id}")
    return 0


def plan_tasks(args: argparse.Namespace) -> int:
    open_tasks = [task for task in load_tasks() if not task.done]
    candidates = sorted(open_tasks, key=task_sort_key)
    chosen: list[Task] = []
    remaining = args.minutes

    for task in candidates:
        if task.minutes <= remaining or not chosen:
            chosen.append(task)
            remaining -= task.minutes
        if remaining <= 0:
            break

    if not chosen:
        print("No open tasks to plan.")
        return 0

    total = sum(task.minutes for task in chosen)
    print(f"Focus plan ({total} min scheduled, {max(remaining, 0)} min left):")
    for index, task in enumerate(chosen, start=1):
        print(f"{index}. {format_task(task)}")
    if remaining < 0:
        print("This plan runs over your time budget, but includes the top task.")
    return 0


def export_tasks(args: argparse.Namespace) -> int:
    tasks = load_tasks()
    fieldnames = [
        "id",
        "title",
        "due",
        "priority",
        "minutes",
        "tags",
        "done",
        "created_at",
        "completed_at",
    ]
    output_file = open(args.output, "w", newline="") if args.output else sys.stdout
    writer = csv.DictWriter(output_file, fieldnames=fieldnames)
    writer.writeheader()
    for task in tasks:
        writer.writerow(
            {
                "id": task.id,
                "title": task.title,
                "due": task.due or "",
                "priority": task.priority,
                "minutes": task.minutes,
                "tags": " ".join(task.tags or []),
                "done": str(task.done).lower(),
                "created_at": task.created_at,
                "completed_at": task.completed_at or "",
            }
        )
    if args.output:
        output_file.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="focusplan",
        description="Capture tasks and generate a practical focus plan.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add = subparsers.add_parser("add", help="add a new task")
    add.add_argument("title")
    add.add_argument("--due", type=parse_due, help="today, tomorrow, or YYYY-MM-DD")
    add.add_argument(
        "--priority",
        choices=sorted(PRIORITY_ORDER, key=PRIORITY_ORDER.get),
        default="medium",
    )
    add.add_argument("--minutes", type=positive_int, default=30)
    add.add_argument("--tag", action="append", default=[])
    add.set_defaults(func=add_task)

    list_cmd = subparsers.add_parser("list", help="list tasks")
    list_cmd.add_argument("--all", action="store_true", help="include completed tasks")
    list_cmd.add_argument("--tag", help="only show tasks with this tag")
    list_cmd.set_defaults(func=list_tasks)

    done = subparsers.add_parser("done", help="mark a task complete")
    done.add_argument("id", type=int)
    done.set_defaults(func=mark_done)

    remove = subparsers.add_parser("remove", help="delete a task")
    remove.add_argument("id", type=int)
    remove.set_defaults(func=remove_task)

    plan = subparsers.add_parser("plan", help="make a plan for available time")
    plan.add_argument("--minutes", type=positive_int, default=120)
    plan.set_defaults(func=plan_tasks)

    export = subparsers.add_parser("export", help="export tasks as CSV")
    export.add_argument("--output", help="write CSV to this file")
    export.set_defaults(func=export_tasks)

    return parser


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be an integer") from error
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
