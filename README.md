# FocusPlan

FocusPlan is a small command-line planner for students who want one place to
capture assignments, chores, deadlines, and study tasks. It stores tasks in a
local JSON file, then helps you sort them by due date, priority, and estimated
work time so you can decide what to do next. It is useful when you have several
competing tasks and need a quick, terminal-friendly way to choose a realistic
focus session.

## Usage

Install from GitHub with `uv`:

```bash
uv add "git+https://github.com/armrest99/190FinalProject.git"
```

After installation, run commands through `uv run focusplan`.

Add tasks:

```bash
uv run focusplan add "Finish DSC 190 final project" --due today --priority high --minutes 90 --tag school
uv run focusplan add "Review lecture notes" --due 2026-06-11 --priority medium --minutes 45 --tag studying
uv run focusplan add "Submit repo_url.txt" --due tomorrow --priority high --minutes 10 --tag school
```

List open tasks:

```bash
uv run focusplan list
```

Generate a plan for the time you have available:

```bash
uv run focusplan plan --minutes 120
```

Summarize your current workload:

```bash
uv run focusplan summary --by-priority
```

Complete or remove tasks by ID:

```bash
uv run focusplan done 1
uv run focusplan remove 2
```

Show completed tasks too:

```bash
uv run focusplan list --all
```

Export your task history to CSV:

```bash
uv run focusplan export --output tasks.csv
```

By default, FocusPlan stores data at
`~/.local/share/focusplan/tasks.json`. For testing or separate task lists, set
`FOCUSPLAN_DB` to another path:

```bash
FOCUSPLAN_DB=/tmp/my-tasks.json uv run focusplan add "Try FocusPlan"
```

For development, run the test suite with:

```bash
uv run pytest
```
