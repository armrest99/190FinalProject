from __future__ import annotations

import json

from focusplan import cli


def test_add_and_list_task(tmp_path, monkeypatch, capsys):
    db = tmp_path / "tasks.json"
    monkeypatch.setenv("FOCUSPLAN_DB", str(db))

    assert cli.main(["add", "Write project README", "--priority", "high"]) == 0
    assert cli.main(["list"]) == 0

    output = capsys.readouterr().out
    assert "Added task 1" in output
    assert "Write project README" in output
    assert "high" in output


def test_plan_prioritizes_due_date_and_priority(tmp_path, monkeypatch, capsys):
    db = tmp_path / "tasks.json"
    monkeypatch.setenv("FOCUSPLAN_DB", str(db))
    db.write_text(
        json.dumps(
            [
                {
                    "id": 1,
                    "title": "Later low priority",
                    "due": "2026-06-20",
                    "priority": "low",
                    "minutes": 30,
                    "tags": [],
                    "done": False,
                    "created_at": "",
                    "completed_at": None,
                },
                {
                    "id": 2,
                    "title": "Soon high priority",
                    "due": "2026-06-11",
                    "priority": "high",
                    "minutes": 30,
                    "tags": [],
                    "done": False,
                    "created_at": "",
                    "completed_at": None,
                },
            ]
        )
    )

    assert cli.main(["plan", "--minutes", "30"]) == 0

    output = capsys.readouterr().out
    assert "Soon high priority" in output
    assert "Later low priority" not in output


def test_add_accepts_iso_due_date(tmp_path, monkeypatch, capsys):
    db = tmp_path / "tasks.json"
    monkeypatch.setenv("FOCUSPLAN_DB", str(db))

    assert cli.main(["add", "Turn in repo URL", "--due", "2026-06-11"]) == 0

    saved = json.loads(db.read_text())
    assert saved[0]["due"] == "2026-06-11"
    assert "Added task 1" in capsys.readouterr().out


def test_done_and_remove_update_task_file(tmp_path, monkeypatch, capsys):
    db = tmp_path / "tasks.json"
    monkeypatch.setenv("FOCUSPLAN_DB", str(db))

    assert cli.main(["add", "Draft final report"]) == 0
    assert cli.main(["done", "1"]) == 0
    assert cli.main(["list"]) == 0

    output = capsys.readouterr().out
    assert "Completed task 1" in output
    assert output.rstrip().endswith("No tasks found.")

    assert cli.main(["list", "--all"]) == 0
    assert "[x] Draft final report" in capsys.readouterr().out

    assert cli.main(["remove", "1"]) == 0
    saved = json.loads(db.read_text())
    assert saved == []


def test_export_quotes_csv_fields(tmp_path, monkeypatch, capsys):
    db = tmp_path / "tasks.json"
    monkeypatch.setenv("FOCUSPLAN_DB", str(db))

    assert (
        cli.main(
            [
                "add",
                "Read chapter 1, section 2",
                "--tag",
                "school",
                "--tag",
                "reading",
            ]
        )
        == 0
    )
    capsys.readouterr()

    assert cli.main(["export"]) == 0

    output = capsys.readouterr().out
    assert "id,title,due,priority,minutes,tags,done,created_at,completed_at" in output
    assert '"Read chapter 1, section 2"' in output
    assert "school reading" in output


def test_positive_int_rejects_non_positive_values():
    try:
        cli.positive_int("0")
    except Exception as error:
        assert "greater than zero" in str(error)
    else:
        raise AssertionError("positive_int accepted zero")
