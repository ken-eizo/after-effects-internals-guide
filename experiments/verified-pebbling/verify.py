"""Independent checker for aeig-pebbling-v1 finite-state certificates.

This module does not import the producer. It reconstructs every legal outgoing
transition from recorded states and checks Bellman inequalities and a goal path.
Version 1 uses full closure. Version 2 saturates every omitted state's potential
at the certified goal cost; its omitted outgoing inequalities are automatic.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

MODEL_VERSION = "aeig-pebbling-v1"
MAX_NODES = 63
MAX_STATES = 250_000
MAX_INTEGER = 2**63 - 1
MAX_DISTANCE = MAX_INTEGER * MAX_STATES
MAX_JSON_BYTES = 64 * 1024 * 1024


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _is_int(value: Any, minimum: int = 0, maximum: int = MAX_INTEGER) -> bool:
    return type(value) is int and minimum <= value <= maximum


def _id_list(value: Any, label: str) -> list[str]:
    _require(type(value) is list and len(value) <= MAX_NODES, f"invalid {label} list")
    _require(all(type(item) is str and 1 <= len(item) <= 256 for item in value), f"invalid {label} identifier")
    _require(len(set(value)) == len(value), f"duplicate {label} identifier")
    return sorted(value)


def _validated_model(raw: Any) -> dict[str, Any]:
    _require(type(raw) is dict and set(raw) == {"nodes", "budget_bytes", "targets"}, "invalid model schema")
    _require(_is_int(raw["budget_bytes"]), "invalid budget_bytes")
    _require(type(raw["nodes"]) is list and len(raw["nodes"]) <= MAX_NODES, "invalid nodes list")
    nodes = []
    ids = set()
    for node in raw["nodes"]:
        _require(type(node) is dict and set(node) == {"id", "deps", "bytes", "cost", "scratch_bytes"}, "invalid node schema")
        _require(type(node["id"]) is str and 1 <= len(node["id"]) <= 256, "invalid node id")
        _require(node["id"] not in ids, "duplicate node id")
        ids.add(node["id"])
        _require(_is_int(node["bytes"]) and _is_int(node["scratch_bytes"]), "invalid memory quantity")
        _require(_is_int(node["cost"], minimum=1), "invalid compute cost")
        nodes.append({**node, "deps": _id_list(node["deps"], "dependency")})
    targets = _id_list(raw["targets"], "target")
    _require(all(target in ids for target in targets), "unknown target")
    _require(all(dep in ids for node in nodes for dep in node["deps"]), "unknown dependency")
    # Separate acyclicity check: eliminate nodes whose parents are done.
    done = set()
    while len(done) < len(nodes):
        additions = {node["id"] for node in nodes if node["id"] not in done and set(node["deps"]) <= done}
        _require(bool(additions), "dependency cycle")
        done.update(additions)
    return {"nodes": nodes, "budget_bytes": raw["budget_bytes"], "targets": targets}


def _check(raw: Any, certificate: Any) -> dict[str, Any]:
    model = _validated_model(raw)
    _require(type(certificate) is dict, "certificate must be an object")
    if certificate.get("status") == "inconclusive":
        raise ValueError("inconclusive search report is not a proof certificate")
    expected_keys = {"certificate_version", "model_version", "model_sha256", "status", "states", "path", "goal_state", "cost", "stats"}
    _require(set(certificate) == expected_keys, "invalid certificate schema")
    version = certificate["certificate_version"]
    _require(type(version) is int and version in (1, 2), "unsupported certificate version")
    saturated = version == 2
    _require(certificate["model_version"] == MODEL_VERSION, "unsupported model version")
    canonical = json.dumps({"model_version": MODEL_VERSION, "model": model}, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    _require(certificate["model_sha256"] == digest, "model hash mismatch")
    _require(certificate["status"] in ("optimal", "infeasible"), "unknown certificate status")
    if saturated:
        _require(certificate["status"] == "optimal", "version 2 supports optimal certificates only")
        _require(_is_int(certificate["cost"], maximum=MAX_DISTANCE), "invalid saturation cost")
    cutoff = certificate["cost"] if saturated else None
    stats = certificate["stats"]
    _require(type(stats) is dict and set(stats) == {"states_discovered", "states_settled", "transitions_examined"}, "invalid stats schema")
    _require(all(_is_int(value) for value in stats.values()), "invalid stats value")
    rows = certificate["states"]
    _require(type(rows) is list and (0 if saturated else 1) <= len(rows) <= MAX_STATES, "invalid certificate state count")
    nodes = model["nodes"]
    universe = (1 << len(nodes)) - 1
    locations = {node["id"]: index for index, node in enumerate(nodes)}
    target_bits = sum(1 << locations[node_id] for node_id in model["targets"])
    distances = {}
    for row in rows:
        _require(type(row) is dict and set(row) == {"mask", "distance"}, "invalid state row")
        state, distance = row["mask"], row["distance"]
        _require(_is_int(state, maximum=universe), "invalid state mask")
        _require(_is_int(distance, maximum=MAX_DISTANCE), "invalid distance")
        _require(state not in distances, "duplicate state mask")
        _require(sum(node["bytes"] for i, node in enumerate(nodes) if (state >> i) & 1) <= model["budget_bytes"], "state exceeds resident memory budget")
        if saturated:
            _require(distance < cutoff, "Bellman potential must be strictly below saturation cost")
        distances[state] = distance
    if saturated:
        _require(distances.get(0, cutoff) == 0, "empty state must have potential zero")
        # Discovery count is bounded diagnostic metadata, not a proof premise.
        # Only the settled count and outgoing-edge count can be reconstructed.
        _require(max(1, len(rows)) <= stats["states_discovered"] <= MAX_STATES, "invalid discovered state count")
        _require(stats["states_settled"] == len(rows), "settled state count mismatch")
    else:
        _require(0 in distances and distances[0] == 0, "empty state must have distance zero")
        _require(stats["states_discovered"] == len(rows) and stats["states_settled"] == len(rows), "state count mismatch")

    legal_transition_count = 0
    goal_states = []
    for state, source_distance in distances.items():
        resident = {node["id"] for i, node in enumerate(nodes) if (state >> i) & 1}
        occupied = sum(node["bytes"] for node in nodes if node["id"] in resident)
        if state & target_bits == target_bits:
            _require(not saturated, "a recorded goal must have saturated potential")
            goal_states.append(state)
        for i, node in enumerate(nodes):
            if node["id"] in resident:
                successor, edge_cost = state & ~(1 << i), 0
            else:
                if not all(dep in resident for dep in node["deps"]):
                    continue
                available = model["budget_bytes"] - occupied
                if node["bytes"] + node["scratch_bytes"] > available:
                    continue
                successor, edge_cost = state | (1 << i), node["cost"]
            legal_transition_count += 1
            if saturated:
                following_potential = distances.get(successor, cutoff)
                _require(following_potential <= source_distance + edge_cost,
                         f"saturated Bellman inequality violated: {state} -> {successor}; state set must be closed below cutoff")
            else:
                _require(successor in distances, f"state set is not closed: {state} -> {successor}")
                _require(distances[successor] <= source_distance + edge_cost, f"Bellman inequality violated: {state} -> {successor}")
    _require(stats["transitions_examined"] == legal_transition_count, "transition count mismatch")
    if certificate["status"] == "infeasible":
        _require(not goal_states, "infeasible certificate contains a target state")
        _require(certificate["path"] == [] and certificate["goal_state"] is None and certificate["cost"] is None, "invalid infeasible witness fields")
        return {"valid": True, "status": "infeasible", "cost": None, "message": "closed state set contains start and no goal"}

    path = certificate["path"]
    _require(type(path) is list and len(path) <= MAX_STATES, "invalid path length")
    _require(_is_int(certificate["goal_state"], maximum=universe), "invalid goal_state")
    _require(_is_int(certificate["cost"], maximum=MAX_DISTANCE), "invalid goal cost")
    if not saturated:
        _require(bool(goal_states), "optimal certificate contains no target state")
    current = 0
    path_cost = 0
    for step in path:
        _require(type(step) is dict and set(step) == {"action", "node", "state"}, "invalid path step")
        _require(type(step["node"]) is str and step["node"] in locations, "unknown path node")
        _require(_is_int(step["state"], maximum=universe), "invalid path state")
        index = locations[step["node"]]
        node = nodes[index]
        bit = 1 << index
        if step["action"] == "evict":
            _require(bool(current & bit), "cannot evict an absent node")
            following = current & ~bit
        elif step["action"] == "compute":
            _require(not current & bit, "cannot compute an already resident node")
            _require(all(current & (1 << locations[dep]) for dep in node["deps"]), "path computation has absent dependencies")
            memory = sum(item["bytes"] for i, item in enumerate(nodes) if current & (1 << i))
            _require(memory + node["bytes"] + node["scratch_bytes"] <= model["budget_bytes"], "path computation exceeds memory budget")
            following = current | bit
            path_cost += node["cost"]
        else:
            raise ValueError("unknown path action")
        _require(step["state"] == following, "incorrect path destination")
        if not saturated:
            _require(following in distances, "path destination is outside the closed state set")
        current = following
    _require(current == certificate["goal_state"] and (current & target_bits) == target_bits, "path does not end at the declared goal")
    lower_bound = cutoff if saturated else min(distances[state] for state in goal_states)
    _require(path_cost == certificate["cost"] == lower_bound, "path cost does not meet certified lower bound")
    return {"valid": True, "status": "optimal", "cost": path_cost,
            "message": "legal goal path meets the saturated Bellman lower bound" if saturated else "legal goal path meets the Bellman lower bound"}


def verify(raw: Any, certificate: Any) -> dict[str, Any]:
    """Return a result; malformed inputs never count as valid certificates."""
    try:
        return _check(raw, certificate)
    except (ValueError, TypeError, KeyError, RecursionError, OverflowError) as exc:
        return {"valid": False, "status": "invalid", "cost": None, "message": str(exc)}


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
    _require(len(data) <= MAX_JSON_BYTES, "JSON input exceeds size limit")
    return json.loads(data, object_pairs_hook=_unique_object)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="model JSON file")
    parser.add_argument("certificate", help="certificate JSON file")
    args = parser.parse_args(argv)
    try:
        result = verify(read_json(args.input), read_json(args.certificate))
    except (ValueError, OSError, RecursionError) as exc:
        result = {"valid": False, "status": "invalid", "cost": None, "message": str(exc)}
    print(json.dumps(result, ensure_ascii=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
