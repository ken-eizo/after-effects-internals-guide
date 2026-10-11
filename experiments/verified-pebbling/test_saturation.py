"""Regression and adversarial tests for saturated-potential certificates.

The original independent Bellman-Ford oracle is reused only as a test oracle;
neither production implementation imports it. No wall-clock claims are made.
"""
import copy
import itertools
import random
import unittest

from solver import model_hash, solve, validate_model
from verify import verify
from test_solver import node, oracle


def independent_branches(count=12, goal_cost=1, branch_cost=100):
    # Put the target last: pruning must not depend on input iteration order.
    return dict(
        budget_bytes=count + 1,
        nodes=[node("other-" + str(i), cost=branch_cost) for i in range(count)]
        + [node("goal", cost=goal_cost)],
        targets=["goal"])


class SaturatedCertificateTests(unittest.TestCase):
    def assert_valid(self, model, cert):
        report = verify(model, cert)
        self.assertTrue(report["valid"], report)

    def test_v1_v2_and_independent_oracle_on_all_small_dags(self):
        count_cases = 0
        for count in range(5):
            edges = list(itertools.combinations(range(count), 2))
            for selection in itertools.product((0, 1), repeat=len(edges)):
                deps = [[] for _ in range(count)]
                for enabled, (source, dest) in zip(selection, edges):
                    if enabled:
                        deps[dest].append(str(source))
                for budget in range(count + 2):
                    model = dict(
                        budget_bytes=budget,
                        nodes=[node(str(i), deps[i]) for i in range(count)],
                        targets=[str(count - 1)] if count else [])
                    old = solve(model, full_closure=True)
                    new = solve(model)
                    expected = oracle(model)
                    self.assert_valid(model, old)
                    self.assert_valid(model, new)
                    self.assertEqual(old["cost"], expected)
                    self.assertEqual(new["cost"], expected)
                    self.assertEqual(new["status"], old["status"])
                    self.assertLessEqual(len(new["states"]), len(old["states"]))
                    self.assertEqual(new["certificate_version"],
                                     1 if expected is None else 2)
                    count_cases += 1
        self.assertEqual(count_cases, 437)

    def test_random_weighted_workspace_and_multiple_targets(self):
        rng = random.Random(20260923)
        for _ in range(200):
            count = rng.randrange(1, 7)
            model = dict(
                budget_bytes=rng.randrange(0, 19),
                targets=rng.sample([str(i) for i in range(count)],
                                   rng.randrange(count + 1)),
                nodes=[node(
                    str(i), [str(j) for j in range(i) if rng.randrange(3) == 0],
                    size=rng.randrange(5), cost=rng.randrange(1, 13),
                    scratch=rng.randrange(5)) for i in range(count)])
            new = solve(model)
            old = solve(model, full_closure=True)
            self.assert_valid(model, new)
            self.assert_valid(model, old)
            self.assertEqual(new["cost"], oracle(model))
            self.assertEqual(new["cost"], old["cost"])

    def test_empty_targets_have_zero_cost_and_no_recorded_states(self):
        model = independent_branches()
        model["targets"] = []
        cert = solve(model, max_states=1)
        self.assert_valid(model, cert)
        self.assertEqual(cert["certificate_version"], 2)
        self.assertEqual(cert["cost"], 0)
        self.assertEqual(cert["states"], [])
        self.assertEqual(cert["path"], [])
        self.assertEqual(cert["goal_state"], 0)
        self.assertEqual(cert["stats"]["states_settled"], 0)
        self.assertEqual(solve(model, max_states=1, full_closure=True)["status"],
                         "inconclusive")

    def test_zero_cost_eviction_successors_cannot_be_omitted(self):
        model = dict(budget_bytes=3, targets=["goal"], nodes=[
            node("a", cost=1), node("b", ["a"], cost=1),
            node("goal", ["b"], cost=20)])
        cert = solve(model)
        self.assert_valid(model, cert)
        self.assertEqual(cert["cost"], 22)
        distances = {r["mask"]: r["distance"] for r in cert["states"]}
        self.assertEqual(distances[3], 2)  # a,b
        self.assertEqual(distances[2], 2)  # b, after free eviction of a
        bad = copy.deepcopy(cert)
        bad["states"] = [row for row in bad["states"] if row["mask"] != 2]
        bad["stats"]["states_settled"] -= 1
        report = verify(model, bad)
        self.assertFalse(report["valid"])
        self.assertIn("saturated Bellman", report["message"])

    def test_cheap_compute_successors_cannot_be_omitted(self):
        model = dict(budget_bytes=2, targets=["b"],
                     nodes=[node("a"), node("b", ["a"], cost=4)])
        cert = solve(model)
        bad = copy.deepcopy(cert)
        bad["states"] = [row for row in bad["states"] if row["mask"] != 1]
        bad["stats"]["states_settled"] -= 1
        report = verify(model, bad)
        self.assertFalse(report["valid"])
        self.assertIn("saturated Bellman", report["message"])

    def test_saturation_and_goal_tampering(self):
        model = dict(budget_bytes=2, targets=["b"],
                     nodes=[node("a"), node("b", ["a"], cost=4)])
        cert = solve(model)
        mutations = []
        for cost in (4, 6, True, -1):
            bad = copy.deepcopy(cert)
            bad["cost"] = cost
            mutations.append(bad)
        bad = copy.deepcopy(cert)
        bad["states"].append(dict(mask=bad["goal_state"], distance=4))
        bad["stats"]["states_settled"] += 1
        bad["stats"]["states_discovered"] += 1
        mutations.append(bad)
        bad = copy.deepcopy(cert)
        bad["states"] = []
        bad["stats"]["states_settled"] = 0
        bad["stats"]["transitions_examined"] = 0
        mutations.append(bad)
        bad = copy.deepcopy(cert)
        bad["states"][1]["distance"] = bad["cost"]
        mutations.append(bad)
        bad = copy.deepcopy(cert)
        bad["certificate_version"] = 1
        mutations.append(bad)
        bad = copy.deepcopy(cert)
        bad["status"] = "infeasible"
        mutations.append(bad)
        bad = copy.deepcopy(cert)
        bad["path"] = bad["path"][:-1]
        mutations.append(bad)
        for bad in mutations:
            with self.subTest(bad=bad):
                self.assertFalse(verify(model, bad)["valid"])

    def test_goal_and_zero_cost_suffix_may_be_omitted(self):
        model = dict(budget_bytes=2, targets=["b"],
                     nodes=[node("a"), node("b", ["a"], cost=4)])
        cert = solve(model)
        self.assertNotIn(cert["goal_state"], [r["mask"] for r in cert["states"]])
        cert["path"].append(dict(action="evict", node="a", state=2))
        cert["goal_state"] = 2
        self.assert_valid(model, cert)

    def test_nonempty_target_cannot_claim_the_zero_cost_certificate(self):
        model = dict(budget_bytes=1, targets=[], nodes=[node("goal")])
        cert = solve(model)
        model["targets"] = ["goal"]
        cert["model_sha256"] = model_hash(validate_model(model))
        self.assertFalse(verify(model, cert)["valid"])

    def test_independent_irrelevant_branches_reduce_recorded_states(self):
        model = independent_branches()
        new = solve(model, max_states=1)
        old = solve(model, full_closure=True)
        self.assert_valid(model, new)
        self.assert_valid(model, old)
        self.assertEqual(new["cost"], old["cost"])
        self.assertEqual(new["cost"], 1)
        self.assertEqual(new["stats"]["states_discovered"], 1)
        self.assertEqual(len(new["states"]), 1)
        self.assertEqual(len(old["states"]), 8192)
        self.assertEqual(old["stats"]["states_settled"], 8192)
        self.assertEqual(solve(model, max_states=1, full_closure=True)["status"],
                         "inconclusive")

    def test_cheap_irrelevant_branches_can_still_require_exponential_states(self):
        # Explicitly retain a worst-case limitation: all 2**8 cheap subsets
        # have distance < 100 and must remain in the saturated certificate.
        model = independent_branches(8, goal_cost=100, branch_cost=1)
        cert = solve(model)
        self.assert_valid(model, cert)
        self.assertEqual(cert["cost"], 100)
        self.assertEqual(len(cert["states"]), 256)
        incomplete = solve(model, max_states=32)
        self.assertEqual(incomplete["status"], "inconclusive")
        self.assertFalse(verify(model, incomplete)["valid"])

    def test_handwritten_v1_remains_accepted(self):
        model = dict(budget_bytes=2, targets=["b"],
                     nodes=[node("a"), node("b", ["a"], cost=2)])
        cert = dict(
            certificate_version=1, model_version="aeig-pebbling-v1",
            model_sha256=model_hash(validate_model(model)), status="optimal",
            states=[dict(mask=i, distance=d) for i, d in enumerate((0, 1, 3, 3))],
            path=[dict(action="compute", node="a", state=1),
                  dict(action="compute", node="b", state=3)],
            goal_state=3, cost=3,
            stats=dict(states_discovered=4, states_settled=4,
                       transitions_examined=7))
        self.assert_valid(model, cert)

    def test_full_closure_argument_is_strict(self):
        model = independent_branches(0)
        for value in (0, 1, None, "false"):
            with self.assertRaises(ValueError):
                solve(model, full_closure=value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
