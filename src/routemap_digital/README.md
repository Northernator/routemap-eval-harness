# RouteMap Digital Engine

`routemap_digital` is the named Digital Route engine package. It wraps the validated residue and verifier modules and adds CRT, cycle detection, parsing, and CLI support.

## Public API

```python
from routemap_digital import (
    DEFAULT_MODULI,
    RULED_OUT_WRONG,
    NOT_RULED_OUT,
    are_pairwise_coprime,
    crt_combine,
    fingerprint,
    fingerprint_of_value,
    parse_expression,
    pisano_period,
    pow_mod_via_cycle,
    reconstruct,
    verify,
)
```

`residue.py` is a thin re-export of `dr_residue_engine_v1`. `verify.py` is a thin re-export of `dr_verifier_v1`.

## Honesty Guardrails

CRT reconstructs the integer only when an external upper bound proves the true value is less than or equal to `M`, the product of the coprime modulus bank. For huge expressions it yields the value modulo `M`, not the original integer, and returns `ambiguous=True`. There is no lossless recovery of arbitrary numbers from residues.

Cycle detection works in finite modular state spaces. It answers residue and route-decidable questions; it does not reconstruct full integer values.

## CLI

Canonical invocation:

```powershell
$env:PYTHONPATH='src'
python -m routemap_digital check "7^1000000 mod 9"
python -m routemap_digital verify --claim answer.json
python -m routemap_digital verify --claim answer.json --strict
python -m routemap_digital cycle "7^k mod 9"
```

An optional packaging shim may expose the same app as `routemap`.

Claim JSON:

```json
{"expr": "7^1000000 mod 9", "claimed_answer": 7}
```

or:

```json
{"expr_spec": {"family": "power", "base": 7, "exponent": 1000000}, "claimed_answer": 7, "moduli": [9]}
```
