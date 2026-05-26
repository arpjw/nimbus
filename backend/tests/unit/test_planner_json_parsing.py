from __future__ import annotations

import json
import pytest

from agent.planner import Plan, FileChange


def _parse_plan_raw(raw: str) -> Plan:
    import re
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise ValueError(f"Planner did not return valid JSON: {raw[:200]}")
        data = json.loads(match.group())
    changes = [FileChange(**c) for c in data.get("changes", [])]
    return Plan(summary=data.get("summary", ""), changes=changes, raw=raw)


def test_clean_json():
    raw = json.dumps({
        "summary": "Add hello",
        "changes": [{"path": "hello.py", "action": "create", "description": "hello fn", "rationale": "new"}],
    })
    plan = _parse_plan_raw(raw)
    assert plan.summary == "Add hello"
    assert len(plan.changes) == 1
    assert plan.changes[0].path == "hello.py"


def test_json_with_markdown_fences():
    raw = "```json\n" + json.dumps({
        "summary": "Fix bug",
        "changes": [{"path": "main.py", "action": "modify", "description": "fix off-by-one", "rationale": "bug"}],
    }) + "\n```"
    plan = _parse_plan_raw(raw)
    assert plan.summary == "Fix bug"
    assert plan.changes[0].action == "modify"


def test_json_embedded_in_text():
    raw = 'Here is the plan: {"summary": "Refactor", "changes": []} And that is it.'
    plan = _parse_plan_raw(raw)
    assert plan.summary == "Refactor"
    assert plan.changes == []


def test_missing_changes_field():
    raw = json.dumps({"summary": "No changes"})
    plan = _parse_plan_raw(raw)
    assert plan.summary == "No changes"
    assert plan.changes == []


def test_missing_summary_field():
    raw = json.dumps({"changes": []})
    plan = _parse_plan_raw(raw)
    assert plan.summary == ""


def test_malformed_json_raises():
    with pytest.raises((ValueError, json.JSONDecodeError)):
        _parse_plan_raw("not json at all")


def test_partial_json_raises():
    with pytest.raises((ValueError, json.JSONDecodeError)):
        _parse_plan_raw('{"summary": "broken"')


def test_multiple_changes():
    raw = json.dumps({
        "summary": "Multi-file change",
        "changes": [
            {"path": "a.py", "action": "create", "description": "create a", "rationale": "r"},
            {"path": "b.py", "action": "modify", "description": "modify b", "rationale": "r"},
            {"path": "c.py", "action": "delete", "description": "delete c", "rationale": "r"},
        ],
    })
    plan = _parse_plan_raw(raw)
    assert len(plan.changes) == 3
    actions = {c.action for c in plan.changes}
    assert actions == {"create", "modify", "delete"}
