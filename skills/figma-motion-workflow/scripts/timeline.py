#!/usr/bin/env python3
"""Resolve animation timing dependencies without guessing easing control points.

Usage:
  python timeline.py threshold --start-ms 100 --duration-ms 300 --progress .95 \
      --easing 'cubic-bezier(0,0,0.58,1)'
  python timeline.py audit spec.json

Only linear and explicitly specified, monotonic cubic-bezier progress is sampled.
An omitted easing is sufficient for start/end timing, but never implies linear.
Named ease-out/ease-in-out are unresolved until their control points are supplied.
This tool does not measure video, inspect Figma, or verify rendered path geometry.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
import sys
from typing import Any


USAGE = {
    "threshold": "python timeline.py threshold --start-ms 100 --duration-ms 300 --progress .95 --easing 'cubic-bezier(0,0,0.58,1)'",
    "audit": "python timeline.py audit spec.json",
}
LIMITS = [
    "Only linear or explicit cubic-bezier(x1,y1,x2,y2) can resolve actual progress; named easings are not guessed.",
    "Bezier x control points must be in [0,1]; the y curve must be monotonic nondecreasing (numerical tolerance 1e-12).",
    "Progress describes the parent's animated property value, not elapsed-time percentage; start/end timing alone needs no easing.",
    "resolved_total_ms is the maximum end among resolved events; when resolved_total_is_partial is true it is only a partial bound.",
    "complete is false for invalid or unresolved inputs, or a declared total differing by more than 1e-6 ms; exit status is 2.",
    "This tool computes declared timings only; it does not inspect Figma, measure video, or verify geometry or path-length fidelity.",
]
NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
BEZIER = re.compile(r"cubic-bezier\(\s*(" + NUMBER + r")\s*,\s*(" + NUMBER + r")\s*,\s*(" + NUMBER + r")\s*,\s*(" + NUMBER + r")\s*\)")


class TimelineError(ValueError):
    def __init__(self, code: str, message: str, kind: str = "invalid"):
        super().__init__(message)
        self.code, self.kind = code, kind


def number(value: Any, name: str, *, maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TimelineError("invalid_number", f"{name} must be a finite number, not {type(value).__name__}.")
    try:
        result = float(value)
    except (OverflowError, ValueError):
        raise TimelineError("invalid_number", f"{name} must be finite.") from None
    if not math.isfinite(result) or result < 0 or (maximum is not None and result > maximum):
        interval = f"[0,{maximum:g}]" if maximum is not None else "[0,infinity)"
        raise TimelineError("invalid_number", f"{name} must be finite and in {interval}.")
    return result


@dataclass(frozen=True)
class Easing:
    controls: tuple[float, float, float, float] | None = None

    def time_at_progress(self, progress: float) -> float:
        """Invert y(s), then evaluate x(s): CSS time is x, not parameter s."""
        if self.controls is None or progress in (0.0, 1.0):
            return progress
        x1, y1, x2, y2 = self.controls

        def cubic(s: float, a: float, b: float) -> float:
            return 3 * (1 - s) ** 2 * s * a + 3 * (1 - s) * s * s * b + s ** 3

        low, high = 0.0, 1.0
        for _ in range(80):
            middle = (low + high) / 2
            if cubic(middle, y1, y2) < progress:
                low = middle
            else:
                high = middle
        return cubic((low + high) / 2, x1, x2)


def parse_easing(value: Any) -> Easing:
    if not isinstance(value, str):
        raise TimelineError("invalid_easing", "easing must be linear or an explicit cubic-bezier string.")
    value = value.strip()
    if value == "linear":
        return Easing()
    match = BEZIER.fullmatch(value)
    if not match:
        if value.startswith("cubic-bezier"):
            raise TimelineError("invalid_easing", "Malformed cubic-bezier; provide four finite numeric control points.")
        raise TimelineError("unknown_easing", f"Cannot resolve easing {value!r}; supply its actual cubic-bezier control points.", "unresolved")
    x1, y1, x2, y2 = (float(v) for v in match.groups())
    if not all(math.isfinite(v) for v in (x1, y1, x2, y2)):
        raise TimelineError("invalid_easing", "Bezier control points must be finite.")
    if not (0 <= x1 <= 1 and 0 <= x2 <= 1):
        raise TimelineError("invalid_easing", "Bezier x1 and x2 must be in [0,1].")
    # y'(s)/3 = A*s^2 + B*s + C. Checking its minimum also permits
    # valid monotonic curves whose y control points lie outside [0,1].
    a, b, c = 3 * y1 - 3 * y2 + 1, -4 * y1 + 2 * y2, y1
    if not all(math.isfinite(v) for v in (a, b, c)):
        raise TimelineError("invalid_easing", "Bezier coefficients exceed the supported finite numeric range.")
    derivatives = [y1, 1 - y2]
    if a > 0:
        vertex = -b / (2 * a)
        if 0 < vertex < 1:
            derivatives.append((a * vertex + b) * vertex + c)
    if min(derivatives) < -1e-12:
        raise TimelineError("nonmonotonic_easing", "Bezier progress is not monotonic; a unique actual-progress trigger is unsupported.")
    return Easing((x1, y1, x2, y2))


def finite_sum(left: float, right: float, name: str) -> float:
    result = left + right
    if not math.isfinite(result):
        raise TimelineError("numeric_overflow", f"{name} exceeds the supported finite numeric range.")
    return result


def threshold(*, start_ms: Any, duration_ms: Any, progress: Any, easing: Any) -> dict[str, Any]:
    start = number(start_ms, "start_ms")
    duration = number(duration_ms, "duration_ms")
    progress = number(progress, "progress", maximum=1)
    fraction = parse_easing(easing).time_at_progress(progress)
    return {
        "complete": True,
        "actual_trigger_ms": finite_sum(start, duration * fraction, "actual_trigger_ms"),
        "linear_time_fraction": fraction,
        "property_progress": progress,
        "issues": [],
    }


def audit(spec: Any) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    issue_keys: set[tuple[Any, ...]] = set()

    def issue(error: TimelineError, event: str | None = None) -> None:
        key = (event, error.kind, error.code, str(error))
        if key not in issue_keys:
            issues.append({"event": event, "kind": error.kind, "code": error.code, "message": str(error)})
            issue_keys.add(key)

    if not isinstance(spec, dict) or not isinstance(spec.get("events"), list) or not spec["events"]:
        issue(TimelineError("invalid_spec", "spec must contain a nonempty events array."))
        return {"complete": False, "resolution_complete": False, "events": [], "resolved_total_ms": None, "resolved_total_is_partial": True, "issues": issues}

    records: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    duplicate_ids: set[str] = set()
    for index, event in enumerate(spec["events"]):
        label = f"events[{index}]"
        record: dict[str, Any] = {"id": None, "duration_ms": None, "start_ms": None, "end_ms": None, "easing_status": "omitted", "valid": True, "curve": None, "trigger": None}
        records.append(record)
        if not isinstance(event, dict):
            record["valid"] = False
            issue(TimelineError("invalid_event", f"{label} must be an object."), label)
            continue
        event_id = event.get("id")
        if not isinstance(event_id, str) or not event_id.strip():
            record["valid"] = False
            issue(TimelineError("invalid_id", f"{label}.id must be a nonempty string."), label)
        else:
            record["id"] = event_id
            label = event_id
            if event_id in by_id:
                duplicate_ids.add(event_id)
                issue(TimelineError("duplicate_id", f"Duplicate event id {event_id!r}; its timing is ambiguous."), event_id)
            else:
                by_id[event_id] = record
        try:
            record["duration_ms"] = number(event.get("duration_ms"), f"{label}.duration_ms")
            if ("start_ms" in event) == ("trigger" in event):
                raise TimelineError("invalid_start", f"{label} needs exactly one of start_ms or trigger.")
            if "start_ms" in event:
                record["absolute_start"] = number(event["start_ms"], f"{label}.start_ms")
            else:
                trigger = event["trigger"]
                if not isinstance(trigger, dict) or not isinstance(trigger.get("event"), str) or not trigger["event"].strip():
                    raise TimelineError("invalid_trigger", f"{label}.trigger needs a nonempty parent event id.")
                at = trigger.get("at")
                if at not in ("end", "progress"):
                    raise TimelineError("invalid_trigger", f"{label}.trigger.at must be end or progress.")
                if at == "end" and "progress" in trigger:
                    raise TimelineError("invalid_trigger", f"{label}: end trigger must not contain progress.")
                record["trigger"] = {
                    "event": trigger["event"], "at": at,
                    "delay_ms": number(trigger.get("delay_ms", 0), f"{label}.trigger.delay_ms"),
                }
                if at == "progress":
                    record["trigger"]["progress"] = number(trigger.get("progress"), f"{label}.trigger.progress", maximum=1)
        except TimelineError as error:
            record["valid"] = False
            issue(error, label)
        if "easing" in event:
            try:
                record["curve"] = parse_easing(event["easing"])
                record["easing_status"] = "known"
            except TimelineError as error:
                record["easing_status"] = error.kind
                issue(error, label)

    for record in records:
        event_id, trigger = record["id"], record["trigger"]
        if event_id in duplicate_ids:
            record["valid"] = False
        if trigger:
            parent_id = trigger["event"]
            if parent_id not in by_id:
                record["valid"] = False
                issue(TimelineError("missing_dependency", f"Parent event {parent_id!r} does not exist."), event_id)
            elif parent_id in duplicate_ids:
                record["valid"] = False
                issue(TimelineError("ambiguous_dependency", f"Parent event {parent_id!r} has a duplicate id."), event_id)

    states: dict[str, str] = {}
    stack: list[str] = []
    cycle_members: set[str] = set()

    def resolve(event_id: str) -> float | None:
        record = by_id[event_id]
        state = states.get(event_id)
        if state == "done":
            return record["end_ms"]
        if state == "visiting":
            cycle = stack[stack.index(event_id):] + [event_id]
            cycle_members.update(cycle)
            issue(TimelineError("dependency_cycle", "Dependency cycle: " + " -> ".join(cycle)), event_id)
            return None
        if not record["valid"]:
            states[event_id] = "done"
            return None
        states[event_id] = "visiting"
        stack.append(event_id)
        try:
            trigger = record["trigger"]
            if not trigger:
                start = record["absolute_start"]
            else:
                parent_id = trigger["event"]
                parent_end = resolve(parent_id)
                if parent_end is None:
                    if event_id not in cycle_members:
                        issue(TimelineError("dependency_unresolved", f"Parent event {parent_id!r} has no resolved end.", "unresolved"), event_id)
                    return None
                if trigger["at"] == "end":
                    start = parent_end
                else:
                    parent = by_id[parent_id]
                    if parent["curve"] is None:
                        raise TimelineError("missing_progress_easing", f"Actual-progress trigger needs a known easing on parent {parent_id!r}; no linear assumption is made.", "unresolved")
                    fraction = parent["curve"].time_at_progress(trigger["progress"])
                    start = finite_sum(parent["start_ms"], parent["duration_ms"] * fraction, f"{event_id}.start_ms")
                start = finite_sum(start, trigger["delay_ms"], f"{event_id}.start_ms")
            end = finite_sum(start, record["duration_ms"], f"{event_id}.end_ms")
            record["start_ms"], record["end_ms"] = start, end
            return end
        except TimelineError as error:
            issue(error, event_id)
            return None
        finally:
            stack.pop()
            states[event_id] = "done"

    try:
        for event_id in by_id:
            resolve(event_id)
    except RecursionError:
        issue(TimelineError("dependency_depth", "Dependency chain exceeds Python's recursion limit; split the timeline into smaller dependency groups."))

    ends = [r["end_ms"] for r in records if r["end_ms"] is not None]
    resolved_total = max(ends) if ends else None
    resolution_complete = all(r["end_ms"] is not None for r in records)
    result: dict[str, Any] = {
        "complete": False,
        "resolution_complete": resolution_complete,
        "events": [{k: r[k] for k in ("id", "duration_ms", "start_ms", "end_ms", "easing_status")} for r in records],
        "resolved_total_ms": resolved_total,
        "resolved_total_is_partial": not resolution_complete,
        "issues": issues,
    }
    if "declared_total_ms" in spec:
        result["declared_total_ms"] = None
        result["declared_total_difference_ms"] = None
        try:
            declared = number(spec["declared_total_ms"], "declared_total_ms")
            result["declared_total_ms"] = declared
            if resolution_complete:
                difference = resolved_total - declared
                result["declared_total_difference_ms"] = difference
                if abs(difference) > 1e-6:
                    issue(TimelineError("declared_total_mismatch", f"Resolved total minus declared total is {difference:g} ms."))
        except TimelineError as error:
            issue(error)
    result["complete"] = resolution_complete and not issues
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, epilog="Limits:\n- " + "\n- ".join(LIMITS))
    commands = parser.add_subparsers(dest="command", required=True)
    sample = commands.add_parser("threshold", help="Compute when an animated property reaches an actual-progress threshold.")
    for flag in ("start-ms", "duration-ms", "progress"):
        sample.add_argument("--" + flag, type=float, required=True)
    sample.add_argument("--easing", required=True, help="linear or explicit cubic-bezier(x1,y1,x2,y2); named easings remain unresolved")
    check = commands.add_parser("audit", help="Resolve events, dependencies, totals, and optional declared_total_ms from a JSON spec.")
    check.add_argument("spec", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "threshold":
            result = threshold(start_ms=args.start_ms, duration_ms=args.duration_ms, progress=args.progress, easing=args.easing)
        else:
            def reject_constant(value: str) -> None:
                raise TimelineError("invalid_json_number", f"JSON contains nonfinite number {value}; use finite numeric values.")
            spec = json.loads(args.spec.read_text(encoding="utf-8"), parse_constant=reject_constant)
            result = audit(spec)
    except (TimelineError, OSError, UnicodeError, json.JSONDecodeError) as error:
        result = {"complete": False, "issues": [{"event": None, "kind": getattr(error, "kind", "invalid"), "code": getattr(error, "code", "input_error"), "message": str(error)}]}
        if args.command == "threshold":
            result.update(actual_trigger_ms=None, linear_time_fraction=None)
    result.update(command=args.command, usage=USAGE, limits=LIMITS)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if result["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
