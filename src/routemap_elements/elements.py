"""Re-export shim: the element tagger is now canonical in routemap_token.elements.

Kept so the experiment scripts (run_compare, blind_validate) and rt_test_elements
keep importing from routemap_elements unchanged.
"""

from __future__ import annotations

from routemap_token.elements import ELEMENT_WEIGHT, best_codon_value, classify_element, codon_value

__all__ = ["classify_element", "ELEMENT_WEIGHT", "codon_value", "best_codon_value"]
