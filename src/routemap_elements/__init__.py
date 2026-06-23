"""Experimental: semantic-element + DNA-codon token routing.

Tests whether a richer functional element tagset and 3-token codon context route
better than routemap_token's per-token class prior -- specifically by
context-gating the blanket negation/number/entity force-keep. Reuses the exact
routemap_token TokenRouteQA benchmark for an apples-to-apples, no-leak comparison.
"""

from __future__ import annotations

from .bench_elements import run_comparison
from .elements import ELEMENT_WEIGHT, best_codon_value, classify_element, codon_value

__all__ = ["run_comparison", "classify_element", "codon_value", "best_codon_value", "ELEMENT_WEIGHT"]
