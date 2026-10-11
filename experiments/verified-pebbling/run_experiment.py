"""Reproduce synthetic results without launching or changing After Effects."""
from __future__ import annotations
import copy
import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter
from pathlib import Path

from solver import solve
from verify import verify

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MIB = 1024**2


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def synthetic_replay(model, certificate):
    """Replay pure toy computations; memory accounting is independent of masks.

    The tiny Python values are not allocations of the declared MiB sizes.
    Peak bytes are a mathematical model quantity, not a process measurement.
    """
    specs = {item["id"]: item for item in model["nodes"]}
    resident = {}
    counts = Counter()
    trace = []
    peak = 0
    cost = 0
    source_value = tuple(range(16))

    def evaluate(name):
        if name == "source":
            return source_value
        if name == "analysis":
            return sum(resident["source"])
        if name == "workspace":
            return 7 * resident["analysis"] + 2
        if name == "composite":
            return tuple(x + resident["workspace"] for x in resident["source"])
        raise AssertionError(name)

    for step in certificate["path"]:
        name = step["node"]
        spec = specs[name]
        used = sum(specs[item]["bytes"] for item in resident)
        if step["action"] == "compute":
            assert name not in resident
            assert set(spec["deps"]) <= resident.keys()
            during = used + spec["bytes"] + spec["scratch_bytes"]
            assert during <= model["budget_bytes"]
            peak = max(peak, during)
            resident[name] = evaluate(name)
            counts[name] += 1
            cost += spec["cost"]
        else:
            assert name in resident
            during = used
            del resident[name]
        trace.append(dict(action=step["action"], node=name,
                          peak_during_step_bytes=during,
                          resident_after=sorted(resident), cumulative_cost=cost))
    assert set(model["targets"]) <= resident.keys()
    expected = tuple(x + 7 * sum(source_value) + 2 for x in source_value)
    assert resident["composite"] == expected
    assert cost == certificate["cost"]
    encoded = json.dumps(list(expected), separators=(",", ":")).encode()
    return dict(peak_model_bytes=peak, compute_counts=dict(counts),
                cost_units=cost, output_equal_to_direct=True,
                synthetic_output_sha256=hashlib.sha256(encoded).hexdigest(),
                trace=trace)


def main():
    output = HERE / "results"
    output.mkdir(exist_ok=True)
    test = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover",
                           "-s", str(HERE), "-p", "test_*.py", "-v"],
                          capture_output=True, text=True, encoding="utf-8")
    (output / "tests.txt").write_text(test.stdout + test.stderr, encoding="utf-8")
    if test.returncode:
        print(test.stdout + test.stderr, file=sys.stderr)
        return test.returncode
    fixture = json.loads((HERE / "fixtures/recompute.json").read_text("utf-8"))
    records = []
    for budget in (4, 5, 6, 7):
        model = copy.deepcopy(fixture)
        model["budget_bytes"] = budget * MIB
        certificate = solve(model)
        checked = verify(model, certificate)
        assert checked["valid"], checked
        expected = None if budget == 4 else 29 if budget < 7 else 26
        assert certificate["cost"] == expected
        replay = synthetic_replay(model, certificate) if expected is not None else None
        prefix = "budget-" + str(budget) + "mib"
        for suffix, document in (("model", model), ("certificate", certificate)):
            (output / (prefix + "." + suffix + ".json")).write_text(
                json.dumps(document, indent=2) + "\n", encoding="utf-8")
        records.append(dict(
            budget_bytes=model["budget_bytes"], status=certificate["status"],
            cost_units=certificate["cost"], certificate_verified=checked,
            stats=certificate["stats"], replay=replay,
            model_file=prefix + ".model.json",
            certificate_file=prefix + ".certificate.json"))
    comparisons = []
    for label, branches, goal_cost, branch_cost, expected_old, expected_new in (
            ("expensive-independent-branches", 12, 1, 100, 8192, 1),
            ("cheap-independent-branches", 8, 100, 1, 512, 256)):
        model = {
            "budget_bytes": branches + 1,
            "targets": ["goal"],
            "nodes": [
                {"id": "other-" + str(i), "deps": [], "bytes": 1,
                 "cost": branch_cost, "scratch_bytes": 0}
                for i in range(branches)
            ] + [{"id": "goal", "deps": [], "bytes": 1,
                  "cost": goal_cost, "scratch_bytes": 0}],
        }
        old = solve(model, full_closure=True)
        new = solve(model)
        old_checked, new_checked = verify(model, old), verify(model, new)
        assert old_checked["valid"] and new_checked["valid"]
        assert old["cost"] == new["cost"] == goal_cost
        assert len(old["states"]) == expected_old
        assert len(new["states"]) == expected_new
        model_file = label + ".model.json"
        v1_file = label + ".v1.certificate.json"
        v2_file = label + ".v2.certificate.json"
        for filename, document in ((model_file, model), (v1_file, old),
                                   (v2_file, new)):
            (output / filename).write_text(
                json.dumps(document, indent=2) + "\n", encoding="utf-8")
        cap = 1 if branch_cost > goal_cost else 32
        limited_old = solve(model, max_states=cap, full_closure=True)
        limited_new = solve(model, max_states=cap)
        comparisons.append({
            "case": label, "node_count": len(model["nodes"]),
            "cost_units": goal_cost,
            "v1": {"recorded_states": len(old["states"]),
                   "stats": old["stats"], "verification": old_checked,
                   "certificate_file": v1_file},
            "v2": {"recorded_states": len(new["states"]),
                   "stats": new["stats"], "verification": new_checked,
                   "certificate_file": v2_file},
            "state_limit_comparison": {
                "max_states": cap, "v1_status": limited_old["status"],
                "v2_status": limited_new["status"]},
            "model_file": model_file,
            "timing_claim": False,
        })
    source_paths = [
        HERE / "solver.py", HERE / "verify.py", HERE / "test_solver.py",
        HERE / "test_saturation.py",
        HERE / "run_experiment.py", HERE / "fixtures/recompute.json",
        ROOT / "docs/render-graph/verified-memory-planning.md",
    ]
    sdk = ROOT / "research/external-sources/ae-sdk-25.6-mac/Headers/AE_ComputeCacheSuite.h"
    provenance = {
        "python_version": platform.python_version(),
        "source_sha256": {str(p.relative_to(ROOT)).replace("\\", "/"): digest(p)
                          for p in source_paths},
        "sdk_evidence": {
            "path": str(sdk.relative_to(ROOT)).replace("\\", "/"),
            "available": sdk.is_file(),
            "sha256": digest(sdk) if sdk.is_file() else None,
            "lines": "55-59; 69-75; 99-141",
            "scope": "distributed contract evidence, not private scheduler source",
        },
    }
    summary = {
        "schema_version": 2, "evidence_class": "synthetic finite-model experiment",
        "ae_host_executed": False, "private_scheduler_modified": False,
        "global_open_problem_solved": False,
        "scope": "sequential pure immutable DAG; explicit memory and fixed costs",
        "test_exit_code": test.returncode,
        "exhaustive_dag_budget_cases": 437, "seeded_weighted_cases": 120,
        "v1_v2_oracle_crosscheck_cases": 437,
        "saturation_seeded_weighted_cases": 200,
        "test_methods": 22,
        "provenance": provenance, "results": records,
        "saturation_comparisons": comparisons,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n",
                                       encoding="utf-8")
    for item in records:
        print("budget_MiB=%s status=%s cost=%s verified=%s" % (
            item["budget_bytes"] // MIB, item["status"], item["cost_units"],
            item["certificate_verified"]["valid"]))
    print("Independent oracle: 437 exhaustive + 120 original + 200 saturation weighted cases.")
    for item in comparisons:
        print("%s: v1 recorded=%s v2 recorded=%s cost=%s" % (
            item["case"], item["v1"]["recorded_states"],
            item["v2"]["recorded_states"], item["cost_units"]))
    print("Synthetic results saved to", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
