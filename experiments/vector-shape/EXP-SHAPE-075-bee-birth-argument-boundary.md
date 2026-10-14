---
date: 2026-10-14
status: PASS 4/4 verified BEE_Birth argument sites across AE2025 and AE2026
---
# EXP-SHAPE-075 — BEE_Birth argument setup at Adobe aelib callsites

Using PE unwind function ranges and offline Capstone decode, verify the instruction setup immediately before both genuine aelib -> BEE_Birth IAT calls in each installed AE version.

AE2025: `0x6E272` and `0x6F6CF` use `mov r8d, 0xF0B2603`.
AE2026: `0x70647` and `0x71BC8` use `mov r8d, 0xF118657`.

All four callsites prepare the remaining four-register arguments and check `EAX` after the BEE call. **4/4 PASS**. The constants are not yet semantically identified. The map/strings are not proven to contain arbitrary foreign Layer classes or creator callbacks.

Reproduce via `experiments/vector-shape/probe-src/tools/verify_aelib_bee_birth_argument_gates.py`, dataset `datasets/ae-aelib-bee-birth-argument-gates-2025-2026.json`, research note F-VECTOR-075.

This is E2-L native static evidence only. No host-private execution, Adobe patch, user project changes, or CompNodeAE modifications.
