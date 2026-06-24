"""Re-export shim: the element router scorers are now canonical in
routemap_token.routers. Kept so run_compare, blind_validate, and rt_test_elements
keep importing from routemap_elements unchanged.
"""

from __future__ import annotations

from routemap_token.routers import (
    CODON_LOADBEARING_FLOOR,
    MODES,
    _score_sample,
    classify_element,
    run_comparison,
)

__all__ = ["run_comparison", "MODES", "_score_sample", "CODON_LOADBEARING_FLOOR", "classify_element"]
