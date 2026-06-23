"""Tests for the routemap_matrix route-and-validate core (CPU, numpy-only; no torch required).

The torch decode loop is exercised separately via `python -m routemap_matrix selfcheck` (needs torch).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import numpy as np
from routemap_matrix.importance import PositionImportance, token_class_priors, CLASS_PRIOR, window_mass
from routemap_matrix.policies import keep_indices
from routemap_matrix.guard import Guard, kl_divergence
from routemap_matrix.kv import evict_kv
from routemap_matrix.metrics import answer_hit, reduction


def test_importance_mass_and_score():
    imp = PositionImportance(np.array([1.0, 0.15, 0.8, 0.1]))
    imp.update([0.7, 0.1, 0.1, 0.1]); imp.update([0.6, 0.1, 0.2, 0.1])
    assert imp.mass_scores(4)[0] > 1.0
    assert int(np.argmax(imp.scores(4))) == 0


def test_importance_extend():
    imp = PositionImportance(np.array([0.5, 0.5])); imp.extend(2)
    assert imp.prior.shape[0] == 4 and imp.mass.shape[0] == 4


def test_policies_exact_budget_and_selection():
    seq, budget = 10, 5
    mass = np.array([0, 0, 0, 0, 0, 0, 0, 9, 0, 0.0]); impv = np.arange(10) * 1.0
    assert list(keep_indices("recency_window", seq, budget)) == [5, 6, 7, 8, 9]
    assert len(keep_indices("dense", seq, budget)) == seq
    h = keep_indices("h2o", seq, budget, mass=mass, n_sink=2)
    assert len(h) == budget and 7 in h and 0 in h and 1 in h
    rm = keep_indices("routemap", seq, budget, importance=impv, n_sink=2)
    assert len(rm) == budget and 0 in rm and 1 in rm and 8 in rm and 9 in rm
    assert len(keep_indices("routemap", 3, 5, importance=np.arange(3))) == 3


def test_guard_kl_escalation_and_false_prune():
    g = Guard(kl_threshold=0.1, fp_tau=0.05)
    esc, kl = g.check([0.9, 0.1], [0.9, 0.1]); assert (not esc) and kl < 1e-6
    esc2, kl2 = g.check([0.9, 0.1], [0.1, 0.9]); assert esc2 and kl2 > 0.1
    assert g.count_false_prunes([0.1, 0.1, 0.8, 0.0], [0, 1, 3], 4) == 1
    assert g.summary()["guard_triggers"] == 1 and g.summary()["false_prunes"] == 1


def test_guard_confidence_check():
    g = Guard()
    low, conf = g.confidence_check([0.05, 0.05, 0.9], threshold=0.15)
    assert (not low) and abs(conf - 0.9) < 1e-9
    low2, _ = g.confidence_check([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.3], threshold=0.35)
    assert low2 and g.triggers == 1


def test_kv_eviction_shrinks_seq_dim():
    layers = [(np.zeros((1, 2, 10, 4)), np.ones((1, 2, 10, 4))) for _ in range(3)]
    new = evict_kv(layers, np.array([0, 1, 7, 8, 9]), seq_dim=2)
    assert len(new) == 3 and all(k.shape[2] == 5 and v.shape[2] == 5 for k, v in new)


def test_metrics():
    assert answer_hit("The code is BLUE-42 indeed", "blue-42") and not answer_hit("nope", "blue-42")
    assert abs(reduction(100, 25) - 0.75) < 1e-9


def test_token_class_priors_shape():
    pr = token_class_priors(["the", "island", "OpenAI"])
    assert pr.shape[0] == 3 and pr.min() >= 0.0 and pr.max() <= 1.0


def test_window_mass_observation_window():
    import numpy as np
    # two layers, each [W=2, K=2]; sum over W then mean over layers
    m = window_mass([np.array([[0.5, 0.5], [0.1, 0.9]]), np.array([[0.4, 0.6], [0.2, 0.8]])])
    assert np.allclose(m, [0.6, 1.4])
    # key that the window attends to most gets the highest mass
    assert int(np.argmax(window_mass([np.array([[0.1, 0.8, 0.1]])]))) == 1
