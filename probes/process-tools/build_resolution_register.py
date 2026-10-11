"""Inventory explicit AEIG boundaries without promoting them to solved.

This is a corpus-scoped register, not a claim to know every AE defect.
Run with --check to detect stale/missing output without changing any sources.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "datasets/aeig-resolution-register.json"
PAGE = ROOT / "docs/reference/radical-resolution-register.md"
SOURCES = [
    ("bug", "research/bug-quirks.csv", "bug_id"),
    ("frontier", "datasets/aeig-unknown-frontier.csv", "subject"),
    ("capability", "datasets/ae-plugin-capability-frontier.csv", "capability"),
]
OPEN_HEADING = re.compile(
    r"^(?:unknown(?: frontier|s)?|open questions?|remaining unknowns?|"
    r"unresolved(?: questions?| boundaries| issues)?|limitations?)(?:\s*[:/-].*)?$",
    re.I)
SELECTED = {
    "BQ-0020": "experiments/sdk-contract-fixes/",
    "BQ-0029": "experiments/sdk-contract-fixes/",
    "BQ-0033": "experiments/sdk-contract-fixes/",
    "BQ-0034": "experiments/sdk-contract-fixes/",
    "BQ-0035": "experiments/smartfx-contract-lab/",
    "BQ-0036": "experiments/sdk-lifecycle-lab/",
    "BQ-0037": "experiments/sdk-hdr-lab/",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def classify(kind, row):
    if kind == "bug":
        state = row["status"]
        if state == "fixed":
            return ("upstream-reported-fixed", "Retest only in the stated affected/fixed version; this import is not a new host validation.")
        if state in {"historical", "historical-compat", "historical-pitfall"}:
            return ("historical-or-compatibility", "Preserve legacy behavior where required; reproduce before changing compatibility code.")
        if state == "source-repair-verified":
            return ("source-repaired-host-unvalidated", "The pinned source repair is tested in its stated laboratory domain; linked plug-in and AE host behavior remain unvalidated.")
        if state == "source-policy-verified":
            return ("source-policy-verified", "An explicit source policy is tested; do not promote it to proof of a production defect or host fix.")
        if state == "source-repair-partial-policy":
            return ("source-partially-repaired", "Enforce the tested safety domain; resolve the documented unsupported semantics and compatibility policy before claiming full behavior support.")
        if state == "sample-pitfall":
            return ("source-repair-candidate", "Pin source bytes; reproduce a counterexample; patch a copy; test both original and corrected code; host integration remains separate.")
        if state in {"active-contract", "active-risk"}:
            return ("contract-obligation", "Implement and test the stated invariant in the caller; absence of a universal host feature is not automatically a host defect.")
        if state in {"known", "known/mitigated"}:
            return ("upstream-known-unresolved", "Confirm current Adobe status and target host reproduction; validate a supported mitigation or vendor fix.")
        return ("needs-manual-classification", "Review the newly encountered source status; do not silently mark it solved.")
    if kind == "frontier":
        category = row["frontier_type"]
        if category == "corpus-boundary":
            return ("evidence-gap", "Obtain authenticated additional corpus or explicitly preserve the provenance/coverage limit.")
        if category == "model-frontier":
            return ("model-needs-falsification", "Define mutually distinguishing observations; run the scoped experiment before promoting a private-implementation claim.")
        return ("capability-needs-contract", "Establish host/version, ABI, context, ownership and cache safety; exported names alone are insufficient.")
    state = row["status"]
    if state == "not-after-effects":
        return ("different-host-scope", "Keep the host exclusion; a Premiere capability is not an After Effects defect or feature.")
    if state.startswith("supported"):
        return ("supported-with-obligations", "Exercise the supported route with its stated context and lifetime requirements; keep remaining runtime predictions open.")
    if state == "experimental-contract":
        return ("contract-needs-runtime-validation", "Run the specified relation/receipt experiment with negative controls and retained host evidence.")
    return ("capability-needs-contract", "Establish current AE-specific supported discovery and invocation behavior before claiming third-party support.")


def explicit_sections(text):
    lines = text.splitlines()
    headings = []
    fence = None
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        marker = re.match(r"^(~{3,}|"+chr(96)+r"{3,})", stripped)
        if marker and len(line) - len(stripped) <= 3:
            run = marker[1]
            if fence is None:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence) and not stripped[len(run):].strip():
                fence = None
            continue
        if fence is not None:
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if match:
            headings.append((index, len(match[1]), match[2]))
    for position, (start, depth, title) in enumerate(headings):
        if not OPEN_HEADING.fullmatch(title):
            continue
        end = next((line for line, level, _ in headings[position + 1:] if level <= depth), len(lines))
        body = "\n".join(lines[start + 1:end]).strip()
        if body:
            yield start + 1, end, title, body


def build():
    rows = []
    hashes = {}
    counts = {}
    for kind, relative, identity in SOURCES:
        data = (ROOT / relative).read_bytes()
        hashes[relative] = sha(data)
        source_rows = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
        counts[relative] = len(source_rows)
        seen = set()
        for row in source_rows:
            key = row[identity]
            if key in seen:
                raise ValueError("duplicate source identity: " + relative + ":" + key)
            seen.add(key)
            classification, gate = classify(kind, row)
            subject = row.get("title", row.get("subject", row.get("capability", "")))
            action = row.get("next_action") or row.get("next_probe") or row.get("workaround_or_rule")
            if not action:
                raise ValueError("missing source next action: " + key)
            rows.append({
                "id": kind + ":" + key, "source_file": relative,
                "source_identity": key, "subject": subject,
                "source_status": row.get("status", row.get("state")),
                "classification": classification,
                "source_next_action": action, "closure_requirement": gate,
                "related_work_package": SELECTED.get(key),
                "resolution_claim": "none-from-inventory",
                "implementation_change_status": "see-scoped-work-package" if key in SELECTED else "not-assessed-by-inventory",
                "host_validation_status": "not-run-by-this-inventory",
                "source_row": row,
            })
    sections = []
    document_count = 0
    for path in sorted((ROOT / "docs").rglob("*.md")):
        if path == PAGE:
            continue
        data = path.read_bytes()
        text = data.decode("utf-8-sig")
        if re.search(r"(?m)^status:\s*(?:generated|reference-generated)\s*$", text):
            continue
        relative = path.relative_to(ROOT).as_posix()
        hashes[relative] = sha(data)
        document_count += 1
        for index, (start, end, title, body) in enumerate(explicit_sections(text)):
            sections.append({
                "id": "section:" + relative + ":" + str(index),
                "source_file": relative, "start_line": start, "end_line": end,
                "heading": title, "text": body,
                "classification": "explicit-author-labelled-boundary",
                "resolution_claim": "none-from-inventory",
            })
    assert len(rows) == sum(counts.values())
    assert len({row["id"] for row in rows}) == len(rows)
    return {
        "schema_version": 1,
        "scope": "All rows of three named registries plus explicitly labelled boundary sections in non-generated documentation.",
        "not_claimed": [
            "all After Effects defects", "all unknowns expressed in arbitrary prose",
            "unique independent issues (sources may overlap)",
            "host validation of imported fixed statuses", "completion by documentation",
        ],
        "registry_counts": counts, "registry_records": len(rows),
        "non_generated_documents_scanned": document_count,
        "explicit_boundary_sections": len(sections),
        "classification_counts": dict(sorted(Counter(r["classification"] for r in rows).items())),
        "source_sha256": hashes, "records": rows, "boundary_sections": sections,
    }


def page(report):
    lines = [
        "---", "status: generated", "last_verified: 2026-09-22", "---",
        "# Radical Resolution Register", "",
        "This register preserves every row in three explicitly named AEIG registries, with its original status, evidence and next action. It also captures explicitly labelled unknown/boundary sections in non-generated documentation. It never infers that a source contract, missing private implementation, historical workaround or upstream-fixed report is an unresolved host defect.", "",
        f"Registry records: **{report['registry_records']}**. Authored/non-generated pages scanned: **{report['non_generated_documents_scanned']}**. Explicit boundary sections: **{report['explicit_boundary_sections']}**.", "",
        "These counts describe records and sections, not unique problems. Some boundaries appear in more than one source. Unknowns phrased elsewhere in free text and undiscovered private-host behavior remain outside this mechanical inventory.", "",
        "## Source coverage", "",
        "| Source | Rows |", "|---|---:|",
    ]
    for source, count in report["registry_counts"].items():
        lines.append(f"| {source} | {count} |")
    lines.extend(["", "## Work classes", "", "| Class | Records |", "|---|---:|"])
    for category, count in report["classification_counts"].items():
        lines.append(f"| {category} | {count} |")
    lines.extend([
        "", "## Current concrete work", "",
        "The SDK contract repair package pins actual sample/guide bytes, demonstrates original failures, and verifies repairs on copies. It is kept separate from claims about Adobe's installed production effects. The mathematical planner now has a bounded proof-certificate route; finite-model optimality is separate from a measured host speedup.", "",
        "- experiments/sdk-contract-fixes/ — source repairs, original counterexamples, corrected regression tests and provenance.",
        "- [Certified memory planning](../render-graph/verified-memory-planning.md) — formal model, exact search and independent verification.",
        "- [Source repair analysis](../host-integration/cpp-sdk/verified-sample-repairs.md) — precise scope, algebraic derivations and host limitations.",
        "", "## Closure policy", "",
        "A source repair closes only the reproduced source-level defect under its declared preconditions. It requires a pinned original, a failing original test, a corrected test result and a reviewable patch. Host closure additionally requires the relevant AE version/build, a supported integration route, reference output, resource/lifetime validation and a controlled runtime reproduction. A corpus gap closes only with stronger provenance or additional authenticated evidence. None is automatically closed by this inventory.", "",
        "Known fixed issues retain the source's affected/fixed versions; they are not rebranded as newly solved here. Active contracts are caller obligations and remain relevant even after one reference implementation is tested. Existing L5 predictions and release gates are untouched.", "",
        "## Reproduction and stale-data detection", "",
        "Machine-readable artifact: datasets/aeig-resolution-register.json. It embeds every original registry row, classified next steps, section text/line locations and SHA-256 identifiers for all scanned source documents.", "",
        "Regenerate with: rtk proxy python probes/process-tools/build_resolution_register.py", "",
        "Check without mutation with: rtk proxy python probes/process-tools/build_resolution_register.py --check", "",
        "The check regenerates the expected register in memory and rejects mismatches. There is no solved-status inference from file existence or from optimistic prose.", "",
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = build()
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    rendered = page(report)
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, expected in
                 ((OUTPUT, encoded), (PAGE, rendered))
                 if not path.exists() or path.read_text(encoding="utf-8") != expected]
        if stale:
            print("STALE:", ", ".join(stale))
            return 1
        print("PASS: register reproduces all source rows and scanned boundaries.")
    else:
        OUTPUT.write_text(encoded, encoding="utf-8")
        PAGE.write_text(rendered, encoding="utf-8")
        print(f"Recorded {report['registry_records']} registry rows and {report['explicit_boundary_sections']} explicit boundary sections.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
