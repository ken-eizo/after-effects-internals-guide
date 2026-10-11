# EXP-CACHE-002 analysis

- Parsed rows: **2**
- Malformed rows: **0**
- CHECK attempts: **0**
- Successful checks: **0**
- API-error checks: **0**
- Prefix-model matches: **0/0**
- Prefix-model non-matches/errors: **0**
- Mechanical matrix coverage: **INCOMPLETE**
- Outcome counts: `{}`

## Passes


A CHECK API error is retained as an observed outcome rather than discarded. Mechanical completeness is based on attempted key coverage, while prediction truth is evaluated separately.
Prefix prediction: `ALL_EFFECTS (-1)` normalizes to `num_effects`; generated-prefix >= requested-prefix predicts VALID, generated-prefix < requested-prefix predicts VALID_BUT_INCOMPLETE.
