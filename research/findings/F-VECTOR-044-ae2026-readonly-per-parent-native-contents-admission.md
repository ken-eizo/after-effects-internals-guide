---
status: AE2026-host-verified-readonly
last_verified: 2026-10-12
evidence: E2-X
versions: AE2026 public AEGP Suite; bounded selected Shape Layer
---

# F-VECTOR-044 — Real AE2026 owner tree confirms parent-specific native child type admission

## New host result

A user-manually-executed `CNLNativeOwnerAdmission.aex` returned an actual 610-line read-only TSV. The analyzer programmatically validated the real host-produced data, not the UI message shown in a screenshot. It measured **186 stream nodes**, **33 parent groups**, **198 AEGP_CanAddStream queries**, and **five confirmed positive admission responses**. The StreamRef root succeeded with `root_stream_error=0`. The selected layer object type was 4, native `ADBE Vector Layer`.

Two different host native parent types gave distinct positive responses:

- `ADBE Root Vectors Group`: standard Fill, Trim Paths and vector/group candidates were admissible.
- `ADBE Effect Parade`: `ADBE Slider Control` was admissible.

All **33** bounded parent-group requests for the unregistered candidate `CNL Native Independent Group` returned `can_add=0, A_Err=0`. These results are NOT a global denial of future registered CNL types: only the six exact candidate names and the observed tree to depth 4 (maximum 240 nodes) were tested. `CanAddStream=TRUE` for a hypothetical vector-prefix candidate also does NOT mean its eventual native constructor would succeed.

The existing tree contained genuine `ADBE Layer Styles` with actual `dropShadow/enabled`, `innerShadow/enabled`, `outerGlow/enabled`, and other style children. This provides real AE2026 host corroboration for a separate native Layer Style group hierarchy, independently traced in F-VECTOR-045.

No native stream was created. No private registration was called. The project was not modified by this probe. The screenshot of `CNLNativeVectorHostProbe` separately showing `active_item_not_root` is expected when a layer is active; it does not contradict this successful, selected-layer read-only owner trace.

## Private data handling and evidence

The complete user project tree is retained **locally** in the developer's TEMP and ShapeLayerAE research context only, not copied to the public research repository. The checked-in artifact includes only anonymous aggregate metrics and standard Adobe type names. No custom installed project effect names were copied into the public dataset.

Source: `experiments/vector-shape/probe-src/tools/verify_host_owner_admission_capture.py`.
Aggregate: `datasets/ae2026-owner-admission-host-aggregate-20261012.json`.
Experiment: `EXP-SHAPE-045`.

This validates per-parent admission. It does not prove native independent Contents ownership, save/reopen, AE Pen editing, or BEE_VectorArt rendering.
