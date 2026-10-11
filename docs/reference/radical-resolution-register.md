---
status: generated
last_verified: 2026-09-22
---
# Radical Resolution Register

This register preserves every row in three explicitly named AEIG registries, with its original status, evidence and next action. It also captures explicitly labelled unknown/boundary sections in non-generated documentation. It never infers that a source contract, missing private implementation, historical workaround or upstream-fixed report is an unresolved host defect.

Registry records: **84**. Authored/non-generated pages scanned: **190**. Explicit boundary sections: **96**.

These counts describe records and sections, not unique problems. Some boundaries appear in more than one source. Unknowns phrased elsewhere in free text and undiscovered private-host behavior remain outside this mechanical inventory.

## Source coverage

| Source | Rows |
|---|---:|
| research/bug-quirks.csv | 32 |
| datasets/aeig-unknown-frontier.csv | 28 |
| datasets/ae-plugin-capability-frontier.csv | 24 |

## Work classes

| Class | Records |
|---|---:|
| capability-needs-contract | 12 |
| contract-needs-runtime-validation | 1 |
| contract-obligation | 10 |
| different-host-scope | 1 |
| evidence-gap | 15 |
| historical-or-compatibility | 3 |
| model-needs-falsification | 7 |
| source-repair-candidate | 2 |
| supported-with-obligations | 16 |
| upstream-known-unresolved | 2 |
| upstream-reported-fixed | 15 |

## Current concrete work

The SDK contract repair package pins actual sample/guide bytes, demonstrates original failures, and verifies repairs on copies. It is kept separate from claims about Adobe's installed production effects. The mathematical planner now has a bounded proof-certificate route; finite-model optimality is separate from a measured host speedup.

- experiments/sdk-contract-fixes/ — source repairs, original counterexamples, corrected regression tests and provenance.
- [Certified memory planning](../render-graph/verified-memory-planning.md) — formal model, exact search and independent verification.
- [Source repair analysis](../host-integration/cpp-sdk/verified-sample-repairs.md) — precise scope, algebraic derivations and host limitations.

## Closure policy

A source repair closes only the reproduced source-level defect under its declared preconditions. It requires a pinned original, a failing original test, a corrected test result and a reviewable patch. Host closure additionally requires the relevant AE version/build, a supported integration route, reference output, resource/lifetime validation and a controlled runtime reproduction. A corpus gap closes only with stronger provenance or additional authenticated evidence. None is automatically closed by this inventory.

Known fixed issues retain the source's affected/fixed versions; they are not rebranded as newly solved here. Active contracts are caller obligations and remain relevant even after one reference implementation is tested. Existing L5 predictions and release gates are untouched.

## Reproduction and stale-data detection

Machine-readable artifact: datasets/aeig-resolution-register.json. It embeds every original registry row, classified next steps, section text/line locations and SHA-256 identifiers for all scanned source documents.

Regenerate with: rtk proxy python probes/process-tools/build_resolution_register.py

Check without mutation with: rtk proxy python probes/process-tools/build_resolution_register.py --check

The check regenerates the expected register in memory and rejects mismatches. There is no solved-status inference from file existence or from optimistic prose.
