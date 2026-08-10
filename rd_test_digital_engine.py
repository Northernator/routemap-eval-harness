from __future__ import annotations

import contextlib
import io
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import dr_verifier_v1
from dr_residue_engine_v1 import DEFAULT_MODULI
from routemap_digital import (
    NOT_RULED_OUT,
    RULED_OUT_WRONG,
    are_pairwise_coprime,
    fib_mod_via_cycle,
    fingerprint,
    pisano_period,
    pow_mod_via_cycle,
    reconstruct,
    verify,
)
from routemap_digital.cli import main
from routemap_digital.crt import crt_combine
from routemap_digital.parser import parse_expression


def test_crt_round_trip_and_ambiguity() -> None:
    rng = random.Random(202608)
    modulus_product = math.prod(DEFAULT_MODULI)
    for _ in range(40):
        value = rng.randrange(0, modulus_product)
        residues = {modulus: value % modulus for modulus in DEFAULT_MODULI}
        result = reconstruct(residues, upper_bound=modulus_product)
        assert result["value"] == value
        assert result["ambiguous"] is False
    value = modulus_product * 3 + 12345
    result = reconstruct({modulus: value % modulus for modulus in DEFAULT_MODULI})
    assert result["value"] == value % modulus_product
    assert result["ambiguous"] is True


def test_coprime_guard() -> None:
    assert are_pairwise_coprime(DEFAULT_MODULI) is True
    assert math.prod(DEFAULT_MODULI) == 33666633
    try:
        crt_combine({4: 1, 6: 3})
    except ValueError:
        pass
    else:
        raise AssertionError("non-coprime CRT bank should raise")


def test_power_cycle_matches_pow_for_large_exponents() -> None:
    rng = random.Random(99)
    for _ in range(80):
        base = rng.randint(0, 200)
        modulus = rng.randint(2, 80)
        exponent = rng.randint(0, 10**7)
        assert pow_mod_via_cycle(base, exponent, modulus) == pow(base, exponent, modulus)


def test_pisano_and_fib_cycle_match_engine() -> None:
    for modulus in range(2, 20):
        assert pisano_period(modulus) == brute_pisano(modulus)
    for modulus in DEFAULT_MODULI:
        assert fib_mod_via_cycle(10**6 + 123, modulus) == fingerprint(
            {"family": "fibonacci", "n": 10**6 + 123},
            (modulus,),
        )[modulus]


def test_parser_and_engine_residues() -> None:
    expr_spec, modulus = parse_expression("7^1000000 mod 9")
    assert modulus == 9
    assert fingerprint(expr_spec, (modulus,))[modulus] == pow(7, 1000000, 9)
    fib_spec, fib_mod = parse_expression("fib(12345) mod 37")
    assert fingerprint(fib_spec, (fib_mod,))[fib_mod] == fib_mod_via_cycle(12345, 37)
    fact_spec, fact_mod = parse_expression("12! mod 11")
    assert fingerprint(fact_spec, (fact_mod,))[fact_mod] == math.factorial(12) % 11


def test_parser_preserves_power_factorial_and_modulus_grammar() -> None:
    assert parse_expression("-7 ** 3 MOD 11") == (
        {"family": "power", "base": -7, "exponent": 3},
        11,
    )
    assert parse_expression("20!") == ({"family": "factorial", "n": 20}, None)
    assert parse_expression("2 + 3\nmod\t7") == ({"family": "bigsum", "values": [2, 3]}, 7)


def test_parser_handles_long_adversarial_inputs_without_regex_backtracking() -> None:
    malformed = (
        "9" * 100_000 + "^",
        "9" * 100_000 + "x!",
        "a" + " " * 100_000,
    )
    for value in malformed:
        try:
            parse_expression(value)
        except ValueError:
            pass
        else:
            raise AssertionError("malformed expression should be rejected")


def test_engine_matches_python_exact_for_supported_families() -> None:
    rng = random.Random(8)
    for _ in range(80):
        modulus = rng.randint(2, 97)
        family = rng.choice(["power", "factorial", "bigsum", "bigprod"])
        if family == "power":
            spec = {"family": family, "base": rng.randint(-50, 50), "exponent": rng.randint(0, 30)}
            exact = spec["base"] ** spec["exponent"]
        elif family == "factorial":
            spec = {"family": family, "n": rng.randint(0, 20)}
            exact = math.factorial(spec["n"])
        elif family == "bigsum":
            values = [rng.randint(-10000, 10000) for _ in range(rng.randint(2, 8))]
            spec = {"family": family, "values": values}
            exact = sum(values)
        else:
            values = [rng.randint(-20, 20) for _ in range(rng.randint(2, 8))]
            spec = {"family": family, "values": values}
            exact = math.prod(values)
        assert fingerprint(spec, (modulus,))[modulus] == exact % modulus


def test_verify_reexport_matches_existing_verifier() -> None:
    modulus_product = math.prod(DEFAULT_MODULI)
    cases = [
        ({"family": "bigsum", "values": [2, 3]}, 5, NOT_RULED_OUT),
        ({"family": "bigsum", "values": [2, 3]}, 6, RULED_OUT_WRONG),
        ({"family": "bigsum", "values": [2, 3]}, 5 + modulus_product, NOT_RULED_OUT),
    ]
    for spec, answer, expected in cases:
        assert verify(spec, answer) == dr_verifier_v1.verify(spec, answer)
        assert verify(spec, answer)["verdict"] == expected


def test_cli_smoke(tmp_path: Path) -> None:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        assert main(["check", "7^1000000 mod 9"]) == 0
    assert out.getvalue().strip() == "7^1000000 mod 9 = 7"
    claim = tmp_path / "answer.json"
    claim.write_text(json.dumps({"expr": "2+3 mod 7", "claimed_answer": 6}), encoding="utf-8")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        assert main(["verify", "--claim", str(claim)]) == 0
    assert json.loads(out.getvalue())["verdict"] == RULED_OUT_WRONG
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        assert main(["verify", "--claim", str(claim), "--strict"]) == 1


def brute_pisano(modulus: int) -> int:
    previous, current = 0, 1 % modulus
    for period in range(1, modulus * modulus * 2 + 1):
        previous, current = current, (previous + current) % modulus
        if previous == 0 and current == 1 % modulus:
            return period
    raise AssertionError("period not found")
