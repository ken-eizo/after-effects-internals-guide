# Archived v4 lifecycle observation

This archive preserves the operator run captured under canonical v4 AEX SHA-256 `884E9CB19AF32AFA1DBFB11A4777E66107C71B13C16A759FBB9B299572382792` and Static RC `AE42FE2F62722BCB151A7321F0DEF268A53C61521B32A11183208D3144FC3DE1`.

The JSX fixture completed WARMUP, pass A, Blur `10 -> 75`, pass B, and `SCRIPT_EXIT`; A/B AVI outputs were materialized and differed. Receipt, host-trace, trace-control, and artisan-stage canonical files were present but zero bytes after the post-WARMUP reset, so the run was verified as incomplete and was not promoted.

A diagnostic executed only after the canonical package had already moved to v5 reports a canonical hash/fingerprint mismatch; that mismatch is temporal and does not retroactively invalidate the preserved v4 session metadata. The original verification and raw environment/session files in this archive retain the v4 values.