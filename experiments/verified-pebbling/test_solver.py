"""Adversarial and independent-oracle tests for the bounded research model.

Run: rtk proxy python experiments/verified-pebbling/test_solver.py
No Adobe application is launched or modified.
"""
import copy
import itertools
import json
import random
import unittest
from pathlib import Path

from solver import solve, validate_model
from verify import verify


HERE = Path(__file__).resolve().parent


def node(name, deps=(), size=1, cost=1, scratch=0):
    return dict(id=name, deps=list(deps), bytes=size, cost=cost,
                scratch_bytes=scratch)


def oracle(model, forbid_recompute=False):
    """Independent exhaustive Bellman-Ford on sets, including one-shot history.

    No solver/verifier validation, masks, transitions or shortest-path code is
    reused here. Inputs to this oracle are deliberately valid, tiny instances.
    """
    nodes = {n["id"]: n for n in model["nodes"]}
    names = tuple(nodes)
    resident_sets = [
        frozenset(names[i] for i in range(len(names)) if bits[i])
        for bits in itertools.product((0, 1), repeat=len(names))
    ]
    targets = set(model["targets"])
    budget = model["budget_bytes"]
    start = (frozenset(), frozenset())
    distances = {start: 0}
    # Reachability and relaxation terminate: a finite state graph, >= 0 costs.
    changed = True
    while changed:
        changed = False
        for (resident, computed), distance in list(distances.items()):
            successors = []
            for item in resident:
                successors.append(((resident - {item}, computed), 0))
            used = sum(nodes[x]["bytes"] for x in resident)
            for item, spec in nodes.items():
                if item in resident or (forbid_recompute and item in computed):
                    continue
                if not set(spec["deps"]) <= resident:
                    continue
                if used + spec["bytes"] + spec["scratch_bytes"] > budget:
                    continue
                history = computed | {item} if forbid_recompute else frozenset()
                successors.append(((resident | {item}, history), spec["cost"]))
            for state, weight in successors:
                candidate = distance + weight
                if state not in distances or candidate < distances[state]:
                    distances[state] = candidate
                    changed = True
    # Separately enumerate the goal subsets; do not import solver goal logic.
    goals = {s for s in resident_sets if targets <= s}
    costs = [d for (resident, _), d in distances.items() if resident in goals]
    return min(costs) if costs else None


class CertifiedPlannerTests(unittest.TestCase):
    def assert_matches_oracle(self, model):
        expected = oracle(model)
        certificate = solve(model)
        report = verify(model, certificate)
        self.assertTrue(report["valid"], report)
        self.assertEqual(certificate["status"],
                         "infeasible" if expected is None else "optimal")
        self.assertEqual(certificate["cost"], expected)
        return certificate

    def fixture(self):
        return json.loads((HERE / "fixtures" / "recompute.json").read_text("utf-8"))

    def test_every_ordered_dag_through_four_nodes(self):
        cases = 0
        for count in range(5):
            edges = list(itertools.combinations(range(count), 2))
            for selection in itertools.product((0, 1), repeat=len(edges)):
                deps = [[] for _ in range(count)]
                for present, (source, dest) in zip(selection, edges):
                    if present:
                        deps[dest].append(str(source))
                for budget in range(count + 2):
                    model = dict(
                        budget_bytes=budget,
                        targets=[str(count - 1)] if count else [],
                        nodes=[node(str(i), deps[i]) for i in range(count)])
                    self.assert_matches_oracle(model)
                    cases += 1
        self.assertEqual(cases, 437)

    def test_random_weighted_workspace_multiple_targets(self):
        rng = random.Random(20260922)
        for _ in range(120):
            count = rng.randrange(1, 7)
            model = dict(
                budget_bytes=rng.randrange(0, 18),
                targets=rng.sample([str(i) for i in range(count)],
                                   rng.randrange(count + 1)),
                nodes=[node(
                    str(i), [str(j) for j in range(i) if rng.randrange(3) == 0],
                    size=rng.randrange(5), cost=rng.randrange(1, 10),
                    scratch=rng.randrange(5)) for i in range(count)])
            self.assert_matches_oracle(model)

    def test_recomputation_is_necessary(self):
        model = self.fixture()
        self.assertIsNone(oracle(model, forbid_recompute=True))
        certificate = self.assert_matches_oracle(model)
        self.assertEqual(certificate["cost"], 29)
        source_calls = [s for s in certificate["path"]
                        if s["action"] == "compute" and s["node"] == "source"]
        self.assertEqual(len(source_calls), 2)
        model["budget_bytes"] = 7 * 1024**2
        self.assertEqual(self.assert_matches_oracle(model)["cost"], 26)
        self.assertEqual(oracle(model, forbid_recompute=True), 26)

    def test_workspace_and_output_overlap(self):
        model = self.fixture()
        model["budget_bytes"] = 4 * 1024**2
        self.assertEqual(self.assert_matches_oracle(model)["status"], "infeasible")
        model = dict(budget_bytes=3, targets=["b"],
                     nodes=[node("a", size=2), node("b", ["a"], size=2)])
        self.assertEqual(self.assert_matches_oracle(model)["status"], "infeasible")
        model["budget_bytes"] = 4
        self.assertEqual(self.assert_matches_oracle(model)["cost"], 2)

    def test_zero_memory_and_empty_targets(self):
        self.assert_matches_oracle(dict(budget_bytes=0, targets=[],
                                        nodes=[]))
        self.assert_matches_oracle(dict(budget_bytes=0, targets=["b"],
                                        nodes=[node("a", size=0),
                                               node("b", ["a"], size=0)]))

    def test_input_order_does_not_change_optimum(self):
        model = self.fixture()
        expected = solve(model)["cost"]
        model["nodes"].reverse()
        self.assertEqual(self.assert_matches_oracle(model)["cost"], expected)

    def test_limit_is_inconclusive_even_if_goal_exists(self):
        model = self.fixture()
        certificate = solve(model, max_states=1)
        self.assertEqual(certificate["status"], "inconclusive")
        self.assertFalse(verify(model, certificate)["valid"])
        model["targets"] = []  # The initial state is already a goal.
        certificate = solve(model, max_states=1, full_closure=True)
        self.assertEqual(certificate["status"], "inconclusive")
        self.assertFalse(verify(model, certificate)["valid"])

    def test_certificate_tampering(self):
        model = self.fixture()
        valid = solve(model)
        self.assertTrue(verify(model, valid)["valid"])
        mutations = []
        bad = copy.deepcopy(valid)
        bad["cost"] = 28
        mutations.append(bad)
        bad = copy.deepcopy(valid)
        bad["model_sha256"] = "0" * 64
        mutations.append(bad)
        bad = copy.deepcopy(valid)
        bad["states"] = [s for s in bad["states"] if s["mask"] != 0]
        mutations.append(bad)
        bad = copy.deepcopy(valid)
        bad["states"] = [s for s in bad["states"] if s["mask"] != 1]
        mutations.append(bad)
        bad = copy.deepcopy(valid)
        bad["states"].append(copy.deepcopy(bad["states"][0]))
        mutations.append(bad)
        bad = copy.deepcopy(valid)
        bad["states"][0]["distance"] = True
        mutations.append(bad)
        bad = copy.deepcopy(valid)
        bad["path"][0]["node"] = "composite"
        mutations.append(bad)
        bad = copy.deepcopy(valid)
        bad["path"] = bad["path"][:-1]
        mutations.append(bad)
        bad = copy.deepcopy(valid)
        bad["status"] = "infeasible"
        bad["path"] = []
        bad["cost"] = None
        bad["goal_state"] = None
        mutations.append(bad)
        for bad in mutations:
            self.assertFalse(verify(model, bad)["valid"], bad)
        changed_model = copy.deepcopy(model)
        changed_model["budget_bytes"] += 1
        self.assertFalse(verify(changed_model, valid)["valid"])

    def test_bellman_and_closure_checks_not_just_metadata(self):
        model = self.fixture()
        valid = solve(model, full_closure=True)
        inflated = copy.deepcopy(valid)
        for row in inflated["states"]:
            if row["mask"] == 1:
                row["distance"] = 1000
        report = verify(model, inflated)
        self.assertFalse(report["valid"])
        self.assertIn("Bellman", report["message"])
        missing = copy.deepcopy(valid)
        missing["states"] = [r for r in missing["states"] if r["mask"] != 1]
        count = len(missing["states"])
        missing["stats"]["states_discovered"] = count
        missing["stats"]["states_settled"] = count
        report = verify(model, missing)
        self.assertFalse(report["valid"])
        self.assertIn("closed", report["message"])

    def test_invalid_models_fail_closed(self):
        valid = self.fixture()
        invalid = []
        for key, value in [
                ("budget_bytes", True), ("budget_bytes", -1),
                ("budget_bytes", 3.5), ("targets", ["missing"]),
                ("targets", ["composite", "composite"]),
                ("unexpected", "ignored?")]:
            bad = copy.deepcopy(valid)
            bad[key] = value
            invalid.append(bad)
        for key, value in [
                ("bytes", True), ("bytes", -1), ("cost", 0), ("cost", 2.5),
                ("scratch_bytes", -1), ("deps", ["missing"]),
                ("deps", ["source"]), ("id", "")]:
            bad = copy.deepcopy(valid)
            bad["nodes"][0][key] = value
            invalid.append(bad)
        bad = copy.deepcopy(valid)
        bad["nodes"][1]["deps"] = ["source", "source"]
        invalid.append(bad)
        bad = copy.deepcopy(valid)
        bad["nodes"][0]["deps"] = ["composite"]
        invalid.append(bad)
        bad = copy.deepcopy(valid)
        bad["nodes"].append(copy.deepcopy(bad["nodes"][0]))
        invalid.append(bad)
        bad = copy.deepcopy(valid)
        del bad["nodes"][0]["scratch_bytes"]
        invalid.append(bad)
        for bad in invalid:
            with self.assertRaises(ValueError, msg=repr(bad)):
                validate_model(bad)
            self.assertFalse(verify(bad, {})["valid"])
        for limit in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                solve(valid, max_states=limit)


if __name__ == "__main__":
    unittest.main(verbosity=2)
