"""Meaningful timing and validation tests; run: python -m unittest -v test_timeline."""

import copy
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from timeline import TimelineError, audit, parse_easing, threshold


class ThresholdTests(unittest.TestCase):
    def test_css_bezier_inverts_progress_then_evaluates_time(self):
        # y(.5)=.5 and x(.5)=.125: elapsed time is not 50%.
        result = threshold(start_ms=100, duration_ms=400, progress=.5, easing="cubic-bezier(0,0,0,1)")
        self.assertAlmostEqual(result["linear_time_fraction"], .125, places=12)
        self.assertAlmostEqual(result["actual_trigger_ms"], 150, places=10)

    def test_linear_and_exact_endpoints(self):
        for progress in (0, .95, 1):
            result = threshold(start_ms=100, duration_ms=300, progress=progress, easing="linear")
            self.assertAlmostEqual(result["actual_trigger_ms"], 100 + 300 * progress)
        self.assertEqual(threshold(start_ms=10, duration_ms=0, progress=.5, easing="linear")["actual_trigger_ms"], 10)

    def test_unknown_named_easing_is_not_guessed(self):
        for easing in ("ease-out", "ease-in-out", "ease"):
            with self.subTest(easing=easing), self.assertRaises(TimelineError) as caught:
                threshold(start_ms=0, duration_ms=300, progress=.9, easing=easing)
            self.assertEqual(caught.exception.kind, "unresolved")

    def test_nonmonotonic_and_invalid_beziers(self):
        for easing in ("cubic-bezier(.25,1.5,.75,-.5)", "cubic-bezier(-1,0,1,1)", "cubic-bezier(0,NaN,1,1)", "cubic-bezier(0,0,1)"):
            with self.subTest(easing=easing), self.assertRaises(TimelineError):
                parse_easing(easing)

    def test_monotonic_y_controls_outside_unit_interval_can_be_valid(self):
        curve = parse_easing("cubic-bezier(.2,1.1,.8,.9)")
        self.assertLess(curve.time_at_progress(.5), curve.time_at_progress(.9))

    def test_invalid_numeric_inputs_and_overflow(self):
        for key, value in (("duration_ms", -1), ("duration_ms", math.nan), ("duration_ms", True), ("progress", 1.1), ("start_ms", math.inf)):
            kwargs = dict(start_ms=0, duration_ms=100, progress=.5, easing="linear")
            kwargs[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(TimelineError):
                threshold(**kwargs)
        with self.assertRaises(TimelineError):
            threshold(start_ms=1e308, duration_ms=1e308, progress=1, easing="linear")


class AuditTests(unittest.TestCase):
    def assertIssue(self, result, code):
        self.assertIn(code, [issue["code"] for issue in result["issues"]])
        self.assertFalse(result["complete"])

    def test_two_level_actual_progress_dependencies(self):
        spec = {"events": [
            {"id": "line", "start_ms": 100, "duration_ms": 400, "easing": "cubic-bezier(0,0,0,1)"},
            {"id": "appear", "trigger": {"event": "line", "at": "progress", "progress": .5}, "duration_ms": 200, "easing": "linear"},
            {"id": "rotate", "trigger": {"event": "appear", "at": "progress", "progress": .9, "delay_ms": 10}, "duration_ms": 20},
        ]}
        result = audit(spec)
        self.assertTrue(result["complete"], result["issues"])
        self.assertAlmostEqual(result["events"][1]["start_ms"], 150)
        self.assertAlmostEqual(result["events"][2]["start_ms"], 340)
        self.assertAlmostEqual(result["resolved_total_ms"], 500)
        # A duration change must shift every dependent start, not only the parent.
        changed = copy.deepcopy(spec)
        changed["events"][0]["duration_ms"] = 800
        updated = audit(changed)
        self.assertTrue(updated["complete"])
        self.assertAlmostEqual(updated["events"][1]["start_ms"], 200)
        self.assertAlmostEqual(updated["events"][2]["start_ms"], 390)
        self.assertAlmostEqual(updated["resolved_total_ms"], 900)

    def test_end_trigger_and_parallel_total_need_no_easing(self):
        result = audit({"events": [
            {"id": "body", "start_ms": 0, "duration_ms": 500},
            {"id": "line", "start_ms": 300, "duration_ms": 250},
            {"id": "blink", "trigger": {"event": "line", "at": "end", "delay_ms": 100}, "duration_ms": 403},
        ], "declared_total_ms": 1053})
        self.assertTrue(result["complete"])
        self.assertEqual(result["events"][2]["start_ms"], 650)
        self.assertEqual(result["resolved_total_ms"], 1053)
        self.assertEqual(result["declared_total_difference_ms"], 0)

    def test_missing_parent_easing_leaves_progress_child_unresolved(self):
        result = audit({"events": [
            {"id": "line", "start_ms": 0, "duration_ms": 300},
            {"id": "head", "trigger": {"event": "line", "at": "progress", "progress": .95}, "duration_ms": 162},
        ], "declared_total_ms": 500})
        self.assertIssue(result, "missing_progress_easing")
        self.assertIsNone(result["events"][1]["start_ms"])
        self.assertEqual(result["resolved_total_ms"], 300)
        self.assertTrue(result["resolved_total_is_partial"])
        self.assertIsNone(result["declared_total_difference_ms"])

    def test_declared_unknown_curve_never_claims_complete(self):
        result = audit({"events": [{"id": "line", "start_ms": 0, "duration_ms": 300, "easing": "ease-out"}]})
        self.assertIssue(result, "unknown_easing")
        self.assertEqual(result["events"][0]["end_ms"], 300)

    def test_cycle_is_reported_without_recursing_forever(self):
        result = audit({"events": [
            {"id": "a", "duration_ms": 100, "trigger": {"event": "b", "at": "end"}},
            {"id": "b", "duration_ms": 100, "trigger": {"event": "a", "at": "end"}},
        ]})
        self.assertIssue(result, "dependency_cycle")
        self.assertIsNone(result["resolved_total_ms"])

    def test_duplicate_ids_are_ambiguous_including_for_dependents(self):
        result = audit({"events": [
            {"id": "a", "start_ms": 0, "duration_ms": 100},
            {"id": "a", "start_ms": 50, "duration_ms": 100},
            {"id": "b", "duration_ms": 100, "trigger": {"event": "a", "at": "end"}},
        ]})
        self.assertIssue(result, "duplicate_id")
        self.assertIssue(result, "ambiguous_dependency")
        self.assertTrue(all(event["end_ms"] is None for event in result["events"]))

    def test_missing_dependency_negative_delay_and_invalid_durations(self):
        cases = [
            ({"id": "x", "duration_ms": 10, "trigger": {"event": "missing", "at": "end"}}, "missing_dependency"),
            ({"id": "x", "duration_ms": -1, "start_ms": 0}, "invalid_number"),
            ({"id": "x", "duration_ms": math.nan, "start_ms": 0}, "invalid_number"),
            ({"id": "x", "duration_ms": 10, "trigger": {"event": "parent", "at": "end", "delay_ms": -1}}, "invalid_number"),
            ({"id": "x", "duration_ms": 10, "start_ms": 0, "trigger": {"event": "parent", "at": "end"}}, "invalid_start"),
        ]
        for event, code in cases:
            with self.subTest(event=event):
                result = audit({"events": [{"id": "parent", "duration_ms": 100, "start_ms": 0}, event]})
                self.assertIssue(result, code)
                json.dumps(result, allow_nan=False)  # Invalid NaN must not leak into output.

    def test_declared_total_difference_has_explicit_sign(self):
        result = audit({"events": [{"id": "a", "start_ms": 0, "duration_ms": 940}], "declared_total_ms": 1155.5})
        self.assertIssue(result, "declared_total_mismatch")
        self.assertTrue(result["resolution_complete"])
        self.assertFalse(result["resolved_total_is_partial"])
        self.assertEqual(result["declared_total_difference_ms"], -215.5)

    def test_empty_or_malformed_spec(self):
        for spec in (None, [], {}, {"events": []}, {"events": [None]}):
            with self.subTest(spec=spec):
                self.assertFalse(audit(spec)["complete"])


class CliTests(unittest.TestCase):
    def invoke(self, *args):
        run = subprocess.run([sys.executable, str(Path(__file__).with_name("timeline.py")), *args], capture_output=True, text=True, check=False)
        return run, json.loads(run.stdout)

    def test_threshold_cli_returns_values_usage_limits_and_exit_status(self):
        run, result = self.invoke("threshold", "--start-ms", "100", "--duration-ms", "400", "--progress", ".5", "--easing", "cubic-bezier(0,0,0,1)")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertAlmostEqual(result["actual_trigger_ms"], 150)
        self.assertIn("audit", result["usage"])
        self.assertTrue(result["limits"])
        run, result = self.invoke("threshold", "--start-ms", "0", "--duration-ms", "300", "--progress", ".95", "--easing", "ease-out")
        self.assertEqual(run.returncode, 2)
        self.assertIsNone(result["actual_trigger_ms"])

    def test_audit_cli_rejects_nonfinite_json_and_unresolved_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spec.json"
            path.write_text('{"events":[{"id":"a","start_ms":0,"duration_ms":NaN}]}')
            run, result = self.invoke("audit", str(path))
            self.assertEqual(run.returncode, 2)
            self.assertEqual(result["issues"][0]["code"], "invalid_json_number")
            path.write_text(json.dumps({"events": [
                {"id": "a", "start_ms": 0, "duration_ms": 100},
                {"id": "b", "duration_ms": 20, "trigger": {"event": "a", "at": "progress", "progress": .9}},
            ]}))
            run, result = self.invoke("audit", str(path))
            self.assertEqual(run.returncode, 2)
            self.assertFalse(result["complete"])


if __name__ == "__main__":
    unittest.main()
