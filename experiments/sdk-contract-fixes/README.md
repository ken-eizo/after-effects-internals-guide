# Verified SDK sample repairs

This package repairs four precise source-level problems in **local copies**.
It does not modify the installed SDK, Adobe binaries, projects or plug-ins.

| Issue | Original source | Reproduced behavior | Repair |
|---|---|---|---|
| SDK-ALPHA16 | SmartyPants.cpp:553 | Alpha 0, blend 0 produces 32640 rather than the 16-bit maximum 32768 | Use the complement 256 - blend |
| SDK-ALPHA32 | SmartyPants.cpp:695 | Alpha 0.25, blend 128 produces 0.75 rather than 0.5 | Apply the same alpha interpolation as the 8/16-bit paths |
| BQ-0029 | SmartyPants.cpp:1100 | Alpha query erases unrelated mask bits and retains the bit intended to be cleared | Clear only DOESNT_NEED_EMPTY_PIXELS with &= ~FLAG |
| BQ-0020 | retained Guide HTML:14208-14209 | Pointer-sized count consumes 8 of the 11 seed characters on this machine | Use a character array and its length excluding NUL |

The principal functional repairs are SDK-ALPHA16 and SDK-ALPHA32.
The empty-pixel flag is obsolete for SmartFX in the current Guide, and SmartyPants
is a SmartFX sample. Mask mutation is reproduced, but an AE runtime consequence
has not been demonstrated. The Guide seed is fixed text; hashing a prefix is not
proof of a wrong cache result or a memory error. That repair implements the
explicit full-literal seed policy. Other semantic inputs still need to be mixed.

## Alpha contract and reachable counterexamples

The source's slider spans 0..100 and ActuallyRender computes
blend = trunc(2.56 * slider). Its 100-percent path (blend == 256) calls PF_COPY
before any pixel kernel. Consequently the regression tests of the kernels use
only blend 0..255. The counterexamples above use slider 0 and 50, respectively,
and reach the actual affected branches.

Let b be this integer blend weight and M the maximum channel value.
The intended alpha is:

    alpha_out = (b * alpha_in + (256 - b) * (M - alpha_in)) / 256

At zero blend this is inversion; at weight 256 it is the original image.
Integer depths use floor, as in the original 8-bit right shift, over their
nonnegative channel domain (8-bit 0..255, AE 16-bit 0..32768).
The integer numerator is at most 256*32768, so signed 32-bit arithmetic suffices.
Float uses M=1 with a final conversion to float. The regression oracle uses an
independently written interpolation form and checks 1025 binary-fraction alpha
values in [0,1] for every reachable blend weight. This is finite test coverage,
not a proof about every floating-point encoding or arbitrary out-of-range data.
RGB is preserved by the Alpha branch in every tested case.

## Reproduce

From the AEIG repository root, with the locked SDK present:

    rtk proxy python -B experiments/sdk-contract-fixes/repair.py prepare
    rtk proxy python -B experiments/sdk-contract-fixes/repair.py apply
    rtk proxy python -B experiments/sdk-contract-fixes/test_repair.py
    rtk proxy python -B experiments/sdk-contract-fixes/repair.py regress
    rtk proxy python -B experiments/sdk-contract-fixes/syntax_check.py

Use prepare --sdk-root PATH for the same byte-identical SDK at another location.
syntax_check.py uses the SDK location recorded in source-lock.json.
The regression runner finds clang++ or g++, or accepts --compiler PATH.

To undo only the managed copy edits:

    rtk proxy python -B experiments/sdk-contract-fixes/repair.py revert

Re-applying/reverting is idempotent. Unknown edits and changed source hashes
are rejected. All patch preimages are checked before any working copy is changed.
This is not a crash-atomic transaction across multiple files. Interrupted writes
are rejected on the next invocation and need review; original SDK files remain
untouched. Review the minimal diffs in patches/ before transferring changes into
a separately owned plug-in project.

## Evidence

- source-lock.json records hashes of original code and contracts.
- workbench/original and workbench/copy are generated, ignored local copies.
- patches/ contains the minimal source diffs.
- regression.cpp.in extracts the actual three Alpha branches and the complete
  QueryDynamicFlags function, using explicit lightweight SDK callback mocks.
- test_repair.py validates reversible edits, preimage refusal and dispatch context.
- results/regression.json records compiler and source/harness hashes.
- syntax_check.py checks **both complete translation units** against actual SDK
  headers. Its diagnostics and exact command are in results/syntax-check.json
  and syntax-*.log. Existing SDK include/packing warnings remain visible.

With clang 20.1.2, the original 16-bit code disagreed with the integer oracle in
8,356,992 of 8,388,864 cases; repaired: zero. The original float Alpha code
disagreed in 261,120 of 262,400 cases; repaired: zero. The 65,536 8-bit cases and
RGB preservation checks pass before and after. Mask cases: 262,143 failures
before, zero after, out of 1,048,576. Captured hash seed bytes change from
"Level2Hi" (8) to "Level2Histo" (11).

These results establish defects and repairs in the sampled source computations.
They do not establish that Adobe's built-in Invert effect shares this code, that
a shipped plug-in was replaced, or that AE host integration/performance is fixed.
No After Effects host execution, binary linking, deployment or release promotion
has occurred. Full host behavior, cancellation, MFR and output-bounds integration
remain separate verification tasks.
