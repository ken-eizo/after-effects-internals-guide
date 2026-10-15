---
status: generated-editorial-audit; not proof of every page claim
last_verified: 2026-10-16
---

# AEIG SDK Terminology and Host-context Classification Coverage

**Documents classified:** 296. **Owner sections:** 19.
Official API name-origin: **50**; observed private implementation: **72**; AEIG research model: **174**.

The CSV inventory: `datasets/aeig-sdk-taxonomy-inventory.csv`.
Every document is assigned a function owner and name provenance. This is not a certification that the documentation or host behavior was tested.

## Navigation ownership

| API family / observed host context | Documents |
| --- | ---: |
| Observed Native Implementation (AEIG Research) | 77 |
| Reference | 44 |
| Observed Render, Cache & Execution (AEIG Research) | 36 |
| Introduction | 25 |
| Research & Evidence | 21 |
| Effect UI & Events | 17 |
| Observed Project, Media & Persistence (AEIG Research) | 14 |
| Premiere Pro & Other Hosts | 13 |
| SmartFX | 9 |
| Effect Details | 8 |
| AEGPs | 7 |
| Extension Host Interfaces (Distinct APIs) | 6 |
| Scripting (ExtendScript DOM) | 5 |
| Audio | 3 |
| Command Line (aerender) | 3 |
| AEIOs | 3 |
| Artisans | 3 |
| Effect Basics | 1 |
| Expressions (AE Host API) | 1 |

## Known collision classes and decisions

| Collision | Editorial resolution |
| --- | --- |
| Custom ECW UI / Custom Comp UI | Two official Effect UI purposes, separated by PF_Window_EFFECT vs PF_Window_COMP/LAYER |
| Drawbot shared API | Shared drawing suite, never feature owner of both UIs |
| AEGP Stream suites / TDB-BEE | Public suite in AEGPs; private factory and Stream objects in Observed Native Implementation |
| SmartFX GPU / Drawbot | Pixel renderer vs host-managed effect UI drawing |
| FLT/PIN postload / Effect Details | Private native module lifecycle, not public PF extension API |
| CEP / UXP | Host panel scripting bridge vs version-scoped UXP runtime observation |
| Effect Preview Media (Effects Panel) / Effect Controls Window | Adobe's Effect Preview Media applies to Premiere Pro Beta 27.0+ only (Aug 2026), NOT After Effects; Custom ECW UI is AE Effect UI |

## Scope and limitations

- This generated inventory records each Markdown H1, path, functional owner and declared evidence status.
- Unknown directories fail classification; source code: `probes/process-tools/sdk_taxonomy.py`.
- Existing evidence or programmatic test outcomes are not upgraded by moving pages or renaming site navigation.
- Private functions may retain exact native symbol names from installed AE versions; they cannot be given invented Adobe public API names.
- To regenerate: `python probes/process-tools/audit_sdk_taxonomy.py`; use `--check` to verify the stored inventory.

See [Official names and contextual scope](../foundations/sdk-nomenclature-and-context.md).
