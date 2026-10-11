"""Exact bounded sequential black-pebbling solver and certificate producer.

The model requires pure, deterministic, immutable DAG values. It does not
describe arbitrary plug-ins, asynchronous work, or the After Effects host.
"""
from __future__ import annotations
import argparse
import hashlib
import heapq
import json
from pathlib import Path
import sys
from typing import Any

MODEL_VERSION = "aeig-pebbling-v1"
CERTIFICATE_VERSION = 2
DEFAULT_MAX_STATES = 100_000
HARD_MAX_STATES = 250_000
MAX_NODES = 63
MAX_INTEGER = 2**63 - 1
MAX_JSON_BYTES = 64 * 1024 * 1024


def _integer(value: Any, label: str, minimum: int = 0) -> int:
    if type(value) is not int or not minimum <= value <= MAX_INTEGER:
        raise ValueError(f"{label} must be an integer in [{minimum}, {MAX_INTEGER}]")
    return value


def _keys(value: Any, expected: set[str], label: str) -> None:
    if type(value) is not dict or set(value) != expected:
        raise ValueError(f"{label} must have exactly these keys: {sorted(expected)}")


def _identifier(value: Any, label: str) -> str:
    if type(value) is not str or not 1 <= len(value) <= 256:
        raise ValueError(f"{label} must be a nonempty string of at most 256 characters")
    return value


def _identifiers(value: Any, label: str) -> list[str]:
    if type(value) is not list or len(value) > MAX_NODES:
        raise ValueError(f"{label} must be a list of at most {MAX_NODES} identifiers")
    result = [_identifier(item, label) for item in value]
    if len(set(result)) != len(result):
        raise ValueError(f"{label} contains duplicate identifiers")
    return result


def validate_model(raw: Any) -> dict[str, Any]:
    """Return a canonical model, rejecting unsupported or ambiguous inputs."""
    _keys(raw, {"nodes", "budget_bytes", "targets"}, "model")
    budget = _integer(raw["budget_bytes"], "budget_bytes")
    if type(raw["nodes"]) is not list or len(raw["nodes"]) > MAX_NODES:
        raise ValueError(f"nodes must be a list of at most {MAX_NODES} nodes")
    nodes = []
    known = set()
    for index, node in enumerate(raw["nodes"]):
        label = f"nodes[{index}]"
        _keys(node, {"id", "deps", "bytes", "cost", "scratch_bytes"}, label)
        node_id = _identifier(node["id"], f"{label}.id")
        if node_id in known:
            raise ValueError(f"duplicate node id: {node_id!r}")
        known.add(node_id)
        nodes.append({
            "id": node_id,
            "deps": sorted(_identifiers(node["deps"], f"{label}.deps")),
            "bytes": _integer(node["bytes"], f"{label}.bytes"),
            "cost": _integer(node["cost"], f"{label}.cost", 1),
            "scratch_bytes": _integer(node["scratch_bytes"], f"{label}.scratch_bytes"),
        })
    targets = sorted(_identifiers(raw["targets"], "targets"))
    if any(target not in known for target in targets):
        raise ValueError("targets contains an unknown node id")
    for node in nodes:
        if any(dep not in known for dep in node["deps"]):
            raise ValueError(f"node {node['id']!r} has an unknown dependency")
    # Kahn's algorithm also rejects self dependencies.
    indegree = {node["id"]: len(node["deps"]) for node in nodes}
    children: dict[str, list[str]] = {node["id"]: [] for node in nodes}
    for node in nodes:
        for dep in node["deps"]:
            children[dep].append(node["id"])
    ready = [node_id for node_id, count in indegree.items() if count == 0]
    visited = 0
    while ready:
        node_id = ready.pop()
        visited += 1
        for child in children[node_id]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    if visited != len(nodes):
        raise ValueError("dependency graph must be acyclic")
    return {"nodes": nodes, "budget_bytes": budget, "targets": targets}


def model_hash(model: dict[str, Any]) -> str:
    payload = {"model_version": MODEL_VERSION, "model": model}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def solve(raw: Any, max_states: int = DEFAULT_MAX_STATES, *,
          full_closure: bool = False) -> dict[str, Any]:
    """Find an exact goal path and certify a saturated distance potential.

    By default only states at distance strictly below the best known goal cost
    need expansion. An optimal v2 certificate assigns every omitted state that
    goal cost. All zero-cost eviction successors below the cutoff are retained.
    With full_closure=True, reproduce v1 full reachable-graph certificates.
    Failure to complete within max_states is inconclusive, never infeasible.

    State bits follow input-node order. Computing requires resident dependencies
    and memory for all residents, the new output and transient workspace.
    No input is overwritten. Eviction is a separate zero-cost transition.
    """
    model = validate_model(raw)
    if type(max_states) is not int or not 1 <= max_states <= HARD_MAX_STATES:
        raise ValueError(f"max_states must be an integer in [1, {HARD_MAX_STATES}]")
    if type(full_closure) is not bool:
        raise ValueError("full_closure must be a bool")
    nodes = model["nodes"]
    indices = {node["id"]: index for index, node in enumerate(nodes)}
    dependencies = [sum(1 << indices[dep] for dep in node["deps"]) for node in nodes]
    target_mask = sum(1 << indices[target] for target in model["targets"])
    base = {
        "certificate_version": 1 if full_closure else CERTIFICATE_VERSION,
        "model_version": MODEL_VERSION,
        "model_sha256": model_hash(model),
    }
    distance = {0: 0}
    predecessor: dict[int, tuple[int, str, int]] = {}
    queue = [(0, 0)]
    settled = set()
    transition_count = 0
    cutoff = 0 if not full_closure and target_mask == 0 else None
    goal = 0 if cutoff == 0 else None
    goal_link = None

    while queue:
        current_cost, state = heapq.heappop(queue)
        if state in settled or distance[state] != current_cost:
            continue
        # Every remaining frontier distance is at least this value. A path
        # attaining cutoff has already been retained, including its last edge.
        if not full_closure and cutoff is not None and current_cost >= cutoff:
            break
        settled.add(state)
        resident_bytes = sum(node["bytes"] for i, node in enumerate(nodes) if state & (1 << i))
        transitions = []
        for i, node in enumerate(nodes):
            bit = 1 << i
            if state & bit:
                transitions.append((state ^ bit, 0, "evict", i))
            elif (state & dependencies[i]) == dependencies[i] and (
                resident_bytes + node["bytes"] + node["scratch_bytes"] <= model["budget_bytes"]
            ):
                transitions.append((state | bit, node["cost"], "compute", i))
        transition_count += len(transitions)

        # Inspect all goal edges before storing this expansion's frontier.
        # Otherwise unrelated expensive nodes earlier in the input order could
        # exhaust the state cap before the same expansion discovers a goal.
        if not full_closure:
            for following, weight, action, node_index in transitions:
                proposed = current_cost + weight
                if (following & target_mask) == target_mask and (
                    cutoff is None or proposed < cutoff or
                    (proposed == cutoff and following < goal)
                ):
                    cutoff, goal = proposed, following
                    goal_link = (state, action, node_index)

        for following, weight, action, node_index in transitions:
            proposed = current_cost + weight
            if not full_closure and cutoff is not None and proposed >= cutoff:
                continue
            if following not in distance:
                if len(distance) >= max_states:
                    return {
                        **base,
                        "status": "inconclusive",
                        "reason": "state_limit",
                        "max_states": max_states,
                        "stats": {
                            "states_discovered": len(distance),
                            "states_settled": len(settled),
                            "transitions_examined": transition_count,
                        },
                    }
                distance[following] = proposed
                predecessor[following] = (state, action, node_index)
                heapq.heappush(queue, (proposed, following))
            elif proposed < distance[following]:
                distance[following] = proposed
                predecessor[following] = (state, action, node_index)
                heapq.heappush(queue, (proposed, following))

    if full_closure:
        goals = [state for state in distance if (state & target_mask) == target_mask]
        goal = min(goals, key=lambda state: (distance[state], state)) if goals else None
        cutoff = distance[goal] if goal is not None else None
    path = []
    cursor = goal
    if goal_link is not None:
        previous, action, node_index = goal_link
        path.append({"action": action, "node": nodes[node_index]["id"], "state": goal})
        cursor = previous
    while cursor is not None and cursor != 0:
        previous, action, node_index = predecessor[cursor]
        path.append({"action": action, "node": nodes[node_index]["id"], "state": cursor})
        cursor = previous
    path.reverse()
    # No incumbent and an exhausted queue imply a complete reachable closure.
    # Infeasibility therefore continues to use the original v1 certificate.
    version = 1 if full_closure or goal is None else CERTIFICATE_VERSION
    recorded = distance if version == 1 else settled
    return {
        **base,
        "certificate_version": version,
        "status": "optimal" if goal is not None else "infeasible",
        "states": [{"mask": state, "distance": distance[state]} for state in sorted(recorded)],
        "path": path,
        "goal_state": goal,
        "cost": cutoff,
        "stats": {
            "states_discovered": len(distance),
            "states_settled": len(settled),
            "transitions_examined": transition_count,
        },
    }


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def read_json(path: str | Path) -> Any:
    with open(path, "rb") as stream:
        data = stream.read(MAX_JSON_BYTES + 1)
    if len(data) > MAX_JSON_BYTES:
        raise ValueError(f"JSON input exceeds {MAX_JSON_BYTES} bytes")
    return json.loads(data, object_pairs_hook=_unique_object)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="model JSON file")
    parser.add_argument("--output", help="certificate/report JSON (default stdout)")
    parser.add_argument("--max-states", type=int, default=DEFAULT_MAX_STATES)
    parser.add_argument("--full-closure", action="store_true",
                        help="generate the original v1 full-graph certificate")
    args = parser.parse_args(argv)
    try:
        result = solve(read_json(args.input), args.max_states, full_closure=args.full_closure)
        encoded = json.dumps(result, indent=2, ensure_ascii=True) + "\n"
        if len(encoded.encode("utf-8")) > MAX_JSON_BYTES:
            raise ValueError("result exceeds bounded JSON output size; reduce --max-states")
        if args.output:
            Path(args.output).write_text(encoded, encoding="utf-8")
        else:
            sys.stdout.write(encoded)
        return 3 if result["status"] == "inconclusive" else 0
    except (ValueError, OSError, RecursionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
