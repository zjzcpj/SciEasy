#!/usr/bin/env python3
"""
SciEasy Workflow Gate — Enforces gated development workflow.

This is the single entry point for all workflow state transitions.
AI agents and developers MUST use this CLI to advance through stages.
No stage can be entered without completing all prerequisites.

Usage:
    python gate.py start <issue_title>              # Initialize a new workflow
    python gate.py advance <task_id> <stage_id>      # Advance to next stage
    python gate.py status <task_id>                  # Show current status
    python gate.py list                              # List all active workflows
    python gate.py validate <task_id> <stage_id>     # Check if stage is reachable
    python gate.py abort <task_id> [--reason TEXT]    # Abort a workflow
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ─── Paths ──────────────────────────────────────────────────────────────────

WORKFLOW_DIR = Path(__file__).parent
SCHEMA_PATH = WORKFLOW_DIR / "schema.json"
ACTIVE_DIR = WORKFLOW_DIR / "active"


# ─── Schema Loading ─────────────────────────────────────────────────────────

def load_schema() -> dict:
    """Load and validate the workflow schema."""
    if not SCHEMA_PATH.exists():
        print("ERROR: schema.json not found.", file=sys.stderr)
        sys.exit(1)
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def get_stage_map(schema: dict) -> dict[str, dict]:
    """Build a lookup map of stage_id -> stage_definition."""
    return {s["id"]: s for s in schema["stages"]}


def get_stage_order(schema: dict) -> list[str]:
    """Return ordered list of stage IDs."""
    return [s["id"] for s in schema["stages"]]


# ─── State File Operations ──────────────────────────────────────────────────

def state_path(task_id: str) -> Path:
    return ACTIVE_DIR / f"{task_id}.json"


def load_state(task_id: str) -> dict:
    """Load a task's state file."""
    path = state_path(task_id)
    if not path.exists():
        print(f"ERROR: No active workflow found for '{task_id}'.", file=sys.stderr)
        print(f"  Run `python gate.py list` to see active workflows.", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def save_state(task_id: str, state: dict) -> None:
    """Save a task's state file."""
    ACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    path = state_path(task_id)
    with open(path, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


# ─── Core Logic ─────────────────────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_task_id(title: str) -> str:
    """Generate a task ID from the title."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    slug = slug[:40].rstrip("-")
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{ts}-{slug}"


def check_prerequisites(
    schema: dict, state: dict, target_stage: str
) -> tuple[bool, list[str]]:
    """
    Check if all prerequisites for target_stage are satisfied.
    Returns (can_proceed, list_of_blocking_reasons).
    """
    stage_map = get_stage_map(schema)

    if target_stage not in stage_map:
        return False, [f"Unknown stage: {target_stage}"]

    stage_def = stage_map[target_stage]
    completed = {s["stage_id"] for s in state.get("completed_stages", [])}
    blockers: list[str] = []

    for req in stage_def["requires"]:
        if req not in completed:
            req_name = stage_map.get(req, {}).get("name", req)
            blockers.append(
                f"BLOCKED: Stage '{req_name}' ({req}) must be completed first."
            )

    if target_stage in completed:
        blockers.append(f"Stage '{stage_def['name']}' is already completed.")

    if state.get("status") == "aborted":
        blockers.append("This workflow has been aborted.")

    return len(blockers) == 0, blockers


def format_status(schema: dict, state: dict) -> str:
    """Format a human-readable status of the workflow."""
    stage_order = get_stage_order(schema)
    stage_map = get_stage_map(schema)
    completed = {s["stage_id"] for s in state.get("completed_stages", [])}

    lines = [
        "=" * 62,
        f"  Workflow: {state['title']}",
        f"  Task ID:  {state['task_id']}",
        f"  Status:   {state['status']}",
        f"  Created:  {state['created_at'][:19]}",
        "-" * 62,
    ]

    current_found = False
    for stage_id in stage_order:
        stage = stage_map[stage_id]
        if stage_id in completed:
            comp = next(
                s for s in state["completed_stages"] if s["stage_id"] == stage_id
            )
            marker = "[DONE]"
            extra = f"  (at {comp['completed_at'][:19]})"
        elif not current_found:
            marker = "[NEXT]"
            extra = "  <-- CURRENT"
            current_found = True
        else:
            marker = "[LOCK]"
            extra = ""

        lines.append(f"  {marker} {stage['name']:<35}{extra}")

    lines.append("=" * 62)
    return "\n".join(lines)


# ─── Commands ───────────────────────────────────────────────────────────────

def cmd_start(args: argparse.Namespace) -> None:
    """Start a new workflow."""
    schema = load_schema()
    title = " ".join(args.title)
    task_id = generate_task_id(title)

    state = {
        "task_id": task_id,
        "title": title,
        "status": "active",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "completed_stages": [],
        "history": [
            {
                "event": "workflow_started",
                "timestamp": now_iso(),
                "title": title,
            }
        ],
    }

    save_state(task_id, state)
    print(f"Workflow started.")
    print(f"  Task ID: {task_id}")
    print(f"  Title:   {title}")
    print()
    print(f"Next step: complete 'create_issue' stage by running:")
    print(f"  python .workflow/gate.py advance {task_id} create_issue \\")
    print(f'    --data \'{{"issue_number": 42, "issue_url": "https://..."}}\'')


def cmd_advance(args: argparse.Namespace) -> None:
    """Advance a workflow to the next stage."""
    schema = load_schema()
    state = load_state(args.task_id)
    target = args.stage_id

    # ── GATE CHECK ──────────────────────────────────────────────────────
    can_proceed, blockers = check_prerequisites(schema, state, target)

    if not can_proceed:
        print("=" * 60, file=sys.stderr)
        print("  WORKFLOW GATE: ADVANCEMENT BLOCKED", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        for b in blockers:
            print(f"  X {b}", file=sys.stderr)
        print("", file=sys.stderr)
        print("  You must complete prerequisite stages first.", file=sys.stderr)
        print(f"  Run: python .workflow/gate.py status {args.task_id}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(1)
    # ── END GATE CHECK ──────────────────────────────────────────────────

    # Parse the artifacts data
    artifacts: dict[str, Any] = {}
    if args.data:
        try:
            artifacts = json.loads(args.data)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in --data: {e}", file=sys.stderr)
            sys.exit(1)

    # Validate required artifacts
    stage_map = get_stage_map(schema)
    stage_def = stage_map[target]
    missing = [a for a in stage_def["artifacts"] if a not in artifacts]
    if missing:
        print(f"ERROR: Missing required artifacts: {missing}", file=sys.stderr)
        print(f"  Required: {stage_def['artifacts']}", file=sys.stderr)
        print(f"  Provided: {list(artifacts.keys())}", file=sys.stderr)
        sys.exit(1)

    # Record completion
    completion_record = {
        "stage_id": target,
        "stage_name": stage_def["name"],
        "completed_at": now_iso(),
        "artifacts": artifacts,
    }

    state["completed_stages"].append(completion_record)
    state["updated_at"] = now_iso()
    state["history"].append(
        {
            "event": "stage_completed",
            "stage_id": target,
            "timestamp": now_iso(),
            "artifacts": artifacts,
        }
    )

    # Check if all stages are done
    all_stages = set(get_stage_order(schema))
    completed = {s["stage_id"] for s in state["completed_stages"]}
    if all_stages == completed:
        state["status"] = "completed"
        state["completed_at"] = now_iso()
        state["history"].append(
            {"event": "workflow_completed", "timestamp": now_iso()}
        )

    save_state(args.task_id, state)

    print(f"[DONE] Stage '{stage_def['name']}' completed.")
    print()

    # Show what's next
    stage_order = get_stage_order(schema)
    remaining = [s for s in stage_order if s not in completed]
    if remaining:
        next_stage = remaining[0]
        next_name = stage_map[next_stage]["name"]
        print(f"Next step: {next_name} ({next_stage})")
        print(f"  python .workflow/gate.py advance {args.task_id} {next_stage} \\")
        print(f"    --data '{{...}}'")
    else:
        print("All stages completed! Workflow finished.")


def cmd_status(args: argparse.Namespace) -> None:
    """Show workflow status."""
    schema = load_schema()
    state = load_state(args.task_id)
    print(format_status(schema, state))


def cmd_list(args: argparse.Namespace) -> None:
    """List all active workflows."""
    ACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(ACTIVE_DIR.glob("*.json"))

    if not files:
        print("No active workflows.")
        return

    schema = load_schema()
    stage_count = len(schema["stages"])

    print(f"{'Task ID':<35} {'Status':<12} {'Progress':<12} {'Title'}")
    print("-" * 90)
    for f in files:
        with open(f) as fh:
            state = json.load(fh)
        done = len(state.get("completed_stages", []))
        progress = f"{done}/{stage_count}"
        print(
            f"{state['task_id']:<35} {state['status']:<12} {progress:<12} {state['title']}"
        )


def generate_task_id(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    slug = slug[:40].rstrip("-")
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{ts}-{slug}"


def check_prerequisites(
    schema: dict, state: dict, target_stage: str
) -> tuple[bool, list[str]]:
    """Check if all prerequisites for target_stage are satisfied."""
    stage_map = get_stage_map(schema)
    if target_stage not in stage_map:
        return False, [f"Unknown stage: {target_stage}"]

    stage_def = stage_map[target_stage]
    completed = {s["stage_id"] for s in state.get("completed_stages", [])}
    blockers: list[str] = []

    for req in stage_def["requires"]:
        if req not in completed:
            req_name = stage_map.get(req, {}).get("name", req)
            blockers.append(
                f"BLOCKED: Stage '{req_name}' ({req}) must be completed first."
            )
    if target_stage in completed:
        blockers.append(f"Stage '{stage_def['name']}' is already completed.")
    if state.get("status") == "aborted":
        blockers.append("This workflow has been aborted.")
    return len(blockers) == 0, blockers


def cmd_validate(args: argparse.Namespace) -> None:
    """Check if a stage is reachable."""
    schema = load_schema()
    state = load_state(args.task_id)
    can_proceed, blockers = check_prerequisites(schema, state, args.stage_id)

    if can_proceed:
        print(f"[OK] Stage '{args.stage_id}' is reachable. You may proceed.")
    else:
        print(f"[BLOCKED] Stage '{args.stage_id}' is BLOCKED:")
        for b in blockers:
            print(f"  X {b}")
        sys.exit(1)


def cmd_abort(args: argparse.Namespace) -> None:
    """Abort a workflow."""
    state = load_state(args.task_id)
    state["status"] = "aborted"
    state["updated_at"] = now_iso()
    state["history"].append(
        {
            "event": "workflow_aborted",
            "timestamp": now_iso(),
            "reason": args.reason or "No reason provided",
        }
    )
    save_state(args.task_id, state)
    print(f"Workflow '{args.task_id}' aborted.")


# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="SciEasy Workflow Gate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # start
    p_start = sub.add_parser("start", help="Start a new workflow")
    p_start.add_argument("title", nargs="+", help="Task title / description")

    # advance
    p_advance = sub.add_parser("advance", help="Advance to next stage")
    p_advance.add_argument("task_id", help="Task ID")
    p_advance.add_argument("stage_id", help="Target stage ID")
    p_advance.add_argument("--data", help="JSON string of artifacts")

    # status
    p_status = sub.add_parser("status", help="Show workflow status")
    p_status.add_argument("task_id", help="Task ID")

    # list
    sub.add_parser("list", help="List all active workflows")

    # validate
    p_validate = sub.add_parser("validate", help="Check if stage is reachable")
    p_validate.add_argument("task_id", help="Task ID")
    p_validate.add_argument("stage_id", help="Target stage ID")

    # abort
    p_abort = sub.add_parser("abort", help="Abort a workflow")
    p_abort.add_argument("task_id", help="Task ID")
    p_abort.add_argument("--reason", help="Reason for aborting")

    args = parser.parse_args()
    commands = {
        "start": cmd_start,
        "advance": cmd_advance,
        "status": cmd_status,
        "list": cmd_list,
        "validate": cmd_validate,
        "abort": cmd_abort,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
