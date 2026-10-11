---
status: active
last_verified: 2026-09-22
evidence: distributed SDK contract, established complexity results, proved finite model, synthetic executable experiment
---
# Certified Memory-Bounded Recomputation

This research connects an actual SDK contract to a precisely bounded algorithmic problem: which intermediate results should remain resident, and which should be recomputed, when a dependency graph must execute within a memory budget? It supplies an exact planner, a separately implemented certificate checker, and an independent small-instance oracle.

**Claim boundary:** this is a solution for an explicit finite model. It is neither a solution of a previously unsolved mathematical problem nor a replacement for Adobe's private scheduler. No live After Effects speedup has been measured. “The world's hardest problem” has no established ordering against which this work could be certified. The requested absolute condition has therefore not been achieved.

## Implementation evidence and the actual unknown

The distributed AE 25.6 header AE_ComputeCacheSuite.h provides unusually direct evidence:

| Header lines | Contract | Consequence for this research |
|---|---|---|
| 55–59 | A cache key accounts for every input needed to identify its computed value. Layer state represents render inputs. | Dependency completeness is a prerequisite, not something the planner discovers. |
| 69–75 | The value's total memory footprint informs a purge heuristic; deletion releases owned resources. | Residency and recomputation have a real memory tradeoff. The footprint API is approximate, not a hard reservation. |
| 99–141 | Checkout distinguishes missing, in-flight and resident values, and supports waiting for concurrent work. Receipts must be checked in. | Concurrency and pin lifetimes matter, but are outside this sequential model. |

The repository preserves a corresponding SDK copy at research/external-sources/ae-sdk-25.6-mac/Headers/AE_ComputeCacheSuite.h. The experiment records its SHA-256 when that local corpus is available. The [public SDK Guide](https://ae-plugins.docsforadobe.dev/effect-details/compute-cache-api/) documents the same cache interface. [Adobe's memory documentation](https://helpx.adobe.com/after-effects/desktop/memory-storage-performance/memory-and-storage/memory-storage1.html) independently establishes that rendering and residency are constrained by available memory.

These facts identify a real design pressure, not a demonstrated defect in the host's current eviction policy. The precise policy, its optimality, and a supported way to obtain and control the complete private render DAG remain unknown. An unidentified internal algorithm is not automatically an unsolved mathematical problem.

Related evidence: [Compute Cache](../cache-system/compute-cache.md), [Memory Pressure](../memory-system/runtime-architecture.md), [Render Graph Model](render-graph-model.md), and [cache integration](../capability-recipes/compute-cache-deduplicate-work.md).

## Mathematical classification

This problem connects to computational complexity, graph pebbling, time–space tradeoffs, and verification by finite transition systems.

Gilbert, Lengauer and Tarjan proved the standard pebbling decision problem PSPACE-complete in 1980. Chan, Lauria, Nordström and Vinyals give explicit modern game definitions and further approximation-hardness results. Those are established results, not discoveries made here.

Our unbounded family contains standard black pebbling: assign one byte per vertex, zero scratch, unit computation cost, and choose the single sink as the target. A value can be produced only while all direct predecessors are resident, and any resident value can be discarded. Reaching the sink is equivalent to reaching a state containing only the sink, since surplus values can then be discarded freely. Thus even feasibility of the general mathematical family contains the known PSPACE-hard problem.

This does **not** establish that actual AE graphs span that entire family or that AE solves it optimally. The software's defensive limits also restrict its accepted instances; the complexity statement concerns the mathematical family as graph size grows.

A polynomial-time exact algorithm for every instance of that general family would imply P = PSPACE (and hence P = NP). The present exponential algorithm makes no such claim. The elementary finite-model theorems below apply known shortest-path principles; no novelty priority is claimed.

## Explicit model and assumptions

Let G = (V, E) be a finite directed acyclic graph. Each node v has:

- direct dependencies pred(v);
- a nonnegative integer resident footprint b(v), in bytes;
- a nonnegative integer temporary footprint s(v), in bytes;
- a positive integer computation cost c(v), in declared abstract units.

Let B be the available budget and T the target set. All targets must be resident simultaneously at completion. The initial resident set is empty. A state S is a subset of V with M(S) = sum of b(v) over resident v.

The legal operations are exactly:

1. **Evict v:** if v is resident, transition to S without v, at zero cost.
2. **Compute v:** if v is absent, every predecessor is resident, and
   M(S) + b(v) + s(v) <= B,
   transition to S union {v}, at cost c(v).

The output allocation overlaps all resident inputs and temporary work during computation. Temporary storage is released on completion. This is not an in-place “slide a pebble from input to output” model.

These conditions are essential:

- Inputs and external state belong to one immutable snapshot; all temporal and external dependencies have already been expanded into the graph.
- Recomputing a node is deterministic and has no repeated side effects. A node identifier denotes one semantic computation, not just an effect name.
- Owned allocations are disjoint or conservatively accounted for. There are no unmodelled persistent allocations, allocation fragmentation failures, GPU allocations or device transfers.
- No concurrent caller retains or pins values between operations. Every eviction is legally available to the executor.
- The budget reserves space separately for the host, allocator overhead, planner and certificate. The planner's own memory is not included in the execution budget.
- Costs are fixed additive model weights. They are not inferred milliseconds or a prediction of MFR wall-clock time.
- There are no disk transfers, multiple devices, asynchronous computations, dynamic graph expansion, in-place overwrites or changes of identity during the plan.

Exact footprints establish exact capacity feasibility for this model. Conservative upper bounds establish safety but can exclude physically feasible schedules; their optimum is only the optimum among schedules admitted by those bounds. Merely supplying approximate SDK footprint reports does not establish a physical memory guarantee.

## Theorem 1: state correspondence and capacity safety

For the operations just defined, legal execution prefixes correspond exactly to paths starting at the empty state in the finite state graph.

**Proof.** Initially both representations have no resident values. For an eviction, both remove the same present node and consume no computation cost. For a computation, both require the same resident predecessors and test the same peak-memory expression. Both then add the same output and discard its scratch allocation. Induction on the operation count establishes resident-state equality, equal cumulative cost, and the budget bound at every computation and between computations. Conversely, every state-graph edge specifies one of these legal operations. QED.

The theorem concerns the supplied model. It does not establish that a model extracted from an arbitrary plug-in is complete or that arbitrary plug-in code obeys its declared allocation bounds.

## Theorem 2: complete finite-model solution

There are at most 2^|V| resident subsets. Each has at most |V| outgoing edges because each node admits at most one operation in a given state. All edge costs are nonnegative, including zero-cost eviction.

Dijkstra's algorithm from the empty state therefore terminates on this finite graph if no resource limit intervenes. The least distance among reachable target-containing states equals the minimum total computation cost of any legal execution by Theorem 1. If no reachable state contains T, the model is infeasible.

The default implementation now stops when a known legal goal path of cost C matches the lower bound: every queued state with distance below C has been settled. It retains a sparse map and emits the saturated certificate proved below. The optional --full-closure mode preserves version 1 for comparison and compatibility. An infeasibility claim still requires completing the reachable closure. A state limit returns **inconclusive** unless a valid optimality certificate has already been established. Exhausted resources never become a proof of infeasibility.

The state cap counts discovered states, including expensive candidates found before the best goal cost was known; it is not only a limit on the final certificate's rows. Consequently even a problem with a small eventual certificate may require a larger search budget.

An elementary implementation may take O(|V|^2 2^|V|) transition/queue work in the worst case, ignoring integer bit costs, and O(|V| 2^|V|) worst-case queue storage. The certificate can itself be exponential. This is a small-subgraph research oracle, not a promise of practical scaling to a whole composition.

## Theorem 3: independently checkable optimality

A certificate supplies a finite state set R, distance labels d, and an execution with claimed cost C. The checker reconstructs legal transitions without using the planner's transition generator or its search.

It checks:

- the empty state belongs to R and has label zero;
- every recorded state respects the capacity constraint;
- R is closed under **every** legal outgoing edge, including free evictions;
- for each legal edge S -> U with cost w, d(U) <= d(S) + w;
- every target-containing state in R has label at least C;
- replay of the supplied path is legal, reaches a target-containing state, and costs exactly C.

**Proof.** Closure and the presence of the initial state imply that every reachable state lies in R. For any legal execution, summing the checked edge inequalities from the initial state yields d(final) <= execution cost. Every goal label is at least C; hence every successful execution costs at least C. The supplied legal execution attains C. Therefore it is optimal. QED.

Labels need not themselves encode paths to every state for this lower-bound proof. A realizable witness is required for the claimed optimum. A path alone would prove feasibility, not optimality.

For an infeasibility certificate the checker requires a closed set containing the initial state and no target-containing state. Any successful path would stay within this set and contradict the absence of goals. The same induction proves infeasibility. No missing-state convention is used.

The model hash binds a certificate to canonical model content for reproducibility. It is not a proof that equal finite hashes imply equal AE inputs. The checker also revalidates the model and recomputes all transitions, so it does not trust a hash or producer status in place of the mathematical checks. The verifier imports no producer code; it implements its own parsing, model validation, transition enumeration and certificate checks. This is not a mechanically verified proof assistant implementation.

## Theorem 4: a smaller proof using a saturated potential

Version 2 certificates for optimal plans need not enumerate every reachable state. Let C be the claimed optimum and R the explicitly recorded states. Each recorded state has a nonnegative label strictly below C. Define a potential on the entire state space by

    p(S) = recorded label, if S is in R;
    p(S) = C, otherwise.

The checker requires p(empty) = 0, no goal in R, all legal transitions from R to satisfy p(U) <= p(S) + cost, and a separately replayed legal goal path of cost C. For C = 0, R is empty and the initial state must itself be a goal.

**Proof.** Edges beginning in R are checked explicitly. If an edge starts outside R, its initial potential is C, its ending potential is at most C, and its cost is nonnegative. Its inequality therefore holds automatically. Every goal has potential C. Summing inequalities along any legal successful execution yields C <= its cost; the checked witness attains C. QED.

Zero-cost eviction is particularly important: an edge from a recorded state with p(S) < C to an omitted state would require C <= p(S), and is rejected. Thus cheap omitted successors cannot hide a better path. Unlike version 1, an edge with positive cost may legitimately leave the recorded set if its cost reaches the saturation threshold.

The producer keeps a feasible goal path as an upper bound. Dijkstra settles only the states cheaper than that bound, tests all their legal outgoing edges, and halts once no cheaper unsettled state remains. Within each expansion it considers goal-reaching edges before retaining avoidable expensive candidates. The checker does not rely on the producer having computed true shortest-path labels: the global potential argument alone proves the lower bound.

This is a certificate-size and search-work improvement, not a polynomial-time solution to general pebbling. In a reproducible 13-node fixture with one cost-1 target and twelve independent cost-100 nodes, version 1 settles and records 8192 states; version 2 settles and records 1. Both certify cost 1, and version 2 succeeds with a one-state cap. These are synthetic state counts, not AE render-time measurements.

A deliberately adverse fixture reverses the cost ordering: eight cost-1 independent branches and a cost-100 target still require 256 states below the threshold. A 32-state cap returns inconclusive. This test preserves the exponential worst-case limitation instead of hiding it behind a favourable benchmark.

The model version and input hash remain unchanged. The verifier accepts old version 1 certificates; completed infeasibility certificates still use version 1. --full-closure explicitly requests that earlier search/certificate policy.

## Reproducible forced-recomputation example

The supplied fixture is **synthetic**. Its names are illustrative and do not identify traced AE nodes.

| Node | Dependencies | Resident MiB | Scratch MiB | Cost units |
|---|---|---:|---:|---:|
| source | none | 2 | 0 | 3 |
| analysis | source | 1 | 0 | 5 |
| workspace | analysis | 1 | 3 | 7 |
| composite | source, workspace | 1 | 0 | 11 |

With B = 5 MiB, workspace needs analysis + its output + scratch = 5 MiB. Keeping source would raise this to 7 MiB, so source must first be evicted. Composite later needs source again. Every successful plan therefore computes source at least twice. All four nodes are required, giving a lower bound 2*3 + 5 + 7 + 11 = 29.

A matching execution is: compute source; compute analysis; evict source; compute workspace; evict analysis; compute source; compute composite. Its peak is 5 MiB and its cost is 29.

With B = 4 MiB the mandatory workspace operation cannot fit. With B = 7 MiB a one-pass plan costs 26, the sum of the four necessary computations. A policy that bans recomputation fails at 5 MiB, while the exact planner succeeds. This is a proved counterexample to that policy in the model, not an observed defect in AE.

## Artifacts and validation

The self-contained package is experiments/verified-pebbling:

- solver.py: validated model, exact search and certificate production;
- verify.py: independent transition reconstruction, closure, lower-bound and witness checks;
- test_solver.py: a set-based Bellman–Ford oracle, exhaustive small DAGs, weighted random cases, invalid models and adversarial certificates;
- test_saturation.py: saturated-potential adversarial tests, old/new oracle comparison and favourable/adverse search fixtures;
- run_experiment.py: reproducible certificates, replayed synthetic values, memory/cost frontier, certificate-size comparisons and provenance;
- results/: generated certificates and measured **model** results;
- README.md: Japanese reading guide and exact commands.

Tests include all 76 order-respecting DAGs on zero through four vertices with several budgets (437 model/budget cases), plus 320 seeded weighted instances across the base and saturation suites. The saturation suite also compares version 1 and version 2 on all 437 small DAG/budget cases. Fixing a topological order still covers every DAG up to some relabelling; this is not every labelled graph. Exhaustive finite testing checks implementation consistency on these cases; it does not replace the theorems or verify real host behavior.

Use the package's README to regenerate the report and check each saved certificate. No existing L5 prediction, raw host observation or release status is promoted by this synthetic experiment.

## How this can be applied responsibly

For a plug-in-owned deterministic analysis pipeline, explicitly define each computation and its dependencies; measure or prove allocation bounds; freeze semantic inputs; then solve a small subgraph offline. Use the returned plan only in an executor that owns the relevant memory and can satisfy the eviction assumptions.

A real integration must independently check final image equivalence, peak allocations, cancellation/error cleanup, receipt lifetimes, and CPU/GPU/context restrictions under the target AE version. The Compute Cache suite leaves purge decisions with the host; this package neither bypasses that ownership nor exposes an undocumented private API.

For host research, a stronger next experiment would capture a concrete repeated computation and allocation trace, construct the corresponding bounded model, compare its optimum with the measured schedule, and confirm that a supported plug-in change realizes the improvement. That work has not been performed here.

## Primary references

1. Gilbert, Lengauer, Tarjan. *The Pebbling Problem is Complete in Polynomial Space*. SIAM Journal on Computing 9(3), 513–524, 1980. [DOI](https://doi.org/10.1137/0209038).
2. Chan, Lauria, Nordström, Vinyals. *Hardness of Approximation in PSPACE and Separation Results for Pebble Games*. See definitions in §2.3. [Author manuscript](https://arxiv.org/html/2305.19104v1).
3. Dijkstra. *A note on two problems in connexion with graphs*. Numerische Mathematik 1, 269–271, 1959. [DOI](https://doi.org/10.1007/BF01386390).
4. [Compute Cache API, public After Effects C++ SDK Guide](https://ae-plugins.docsforadobe.dev/effect-details/compute-cache-api/), checked 2026-09-22.
5. [Adobe Memory and storage in After Effects](https://helpx.adobe.com/after-effects/desktop/memory-storage-performance/memory-and-storage/memory-storage1.html), checked 2026-09-22.
