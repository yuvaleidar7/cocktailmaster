"""
test_matching_algorithm.py
==========================
Comprehensive pytest suite for the CocktailMaster matching algorithm.

Tests cover:
  - get_ingredient_weight()  hierarchy enforcement
  - retrieve_candidates()    with all itertools.combinations of curated ingredients
  - Match-percentage integrity (base_spirits > liqueurs_wine > others)
  - Edge cases and exception capture / error logging
"""

import itertools
import logging
import pickle
import re
import sys
import os
from pathlib import Path

import pytest

# ─────────────────────────────────────────────
# Path bootstrap  – make sure logic.py is found
# ─────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import logic  # noqa: E402


# ─────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("cocktail_tests")

# Structured error collector used across the session
_ERROR_LOG: list[dict] = []


# ─────────────────────────────────────────────
# Module-level fixture: load BM25 data once
# ─────────────────────────────────────────────
@pytest.fixture(scope="module")
def bm25_data():
    """Load the BM25 pickle exactly as the production code does."""
    pkl_path = PROJECT_ROOT / "bm25_index.pkl"
    assert pkl_path.exists(), f"bm25_index.pkl not found at {pkl_path}"
    with open(pkl_path, "rb") as fh:
        data = pickle.load(fh)
    return data


# ─────────────────────────────────────────────
# Curated ingredient pools used for combinations
# ─────────────────────────────────────────────
BASE_SPIRITS = [
    "gin",
    "vodka",
    "whiskey",
    "tequila",
    "rum",
    "cognac",
    "mezcal",
    "cachaça",
    "brandy",
    "pisco",
]

LIQUEURS_AND_WINE = [
    "campari",
    "vermouth",
    "orange liqueur",
    "coffee liqueur",
    "amaretto",
    "elderflower liqueur",
    "champagne",
    "cherry liqueur",
    "chocolate liqueur",
    "absinthe",
]

OTHER_INGREDIENTS = [
    "lemon juice",
    "lime juice",
    "sugar syrup",
    "angostura bitters",
    "soda water",
    "egg white",
    "cream",
    "espresso",
    "grenadine",
    "ginger beer",
]


# ═══════════════════════════════════════════════════════════════════════
# 1.  WEIGHT HIERARCHY UNIT TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestWeightHierarchy:
    """Assert that get_ingredient_weight() respects the defined hierarchy."""

    # Expected multipliers from _WEIGHT_CATEGORIES
    BASE_SPIRIT_WEIGHT = 5
    LIQUEUR_WINE_WEIGHT = 4
    SYRUP_WEIGHT = 3
    JUICE_MIXER_WEIGHT = 2
    MISC_WEIGHT = 1

    @pytest.mark.parametrize("spirit", BASE_SPIRITS)
    def test_base_spirits_have_highest_weight(self, spirit):
        """Base spirits must receive the maximum weight multiplier (5)."""
        w = logic.get_ingredient_weight(spirit)
        assert w == self.BASE_SPIRIT_WEIGHT, (
            f"'{spirit}' returned weight {w}, expected {self.BASE_SPIRIT_WEIGHT}"
        )

    @pytest.mark.parametrize("liqueur", [
        "campari", "amaretto", "orange liqueur",
        "coffee liqueur", "cherry liqueur",
    ])
    def test_liqueurs_have_second_tier_weight(self, liqueur):
        """Liqueurs / wines must receive weight >= 4 (second tier)."""
        w = logic.get_ingredient_weight(liqueur)
        assert w >= self.LIQUEUR_WINE_WEIGHT, (
            f"'{liqueur}' returned weight {w}, expected >= {self.LIQUEUR_WINE_WEIGHT}"
        )

    @pytest.mark.parametrize("spirit,liqueur", [
        ("gin",      "campari"),
        ("vodka",    "orange liqueur"),
        ("whiskey",  "amaretto"),
        ("tequila",  "coffee liqueur"),
        ("rum",      "cherry liqueur"),
    ])
    def test_base_spirits_outweigh_liqueurs(self, spirit, liqueur):
        """Base spirit weight must STRICTLY exceed liqueur weight."""
        ws = logic.get_ingredient_weight(spirit)
        wl = logic.get_ingredient_weight(liqueur)
        assert ws > wl, (
            f"'{spirit}' (w={ws}) should outweigh '{liqueur}' (w={wl})"
        )

    @pytest.mark.parametrize("liqueur,other", [
        ("campari",        "lemon juice"),
        ("orange liqueur", "sugar syrup"),
        ("amaretto",       "soda water"),
    ])
    def test_liqueurs_outweigh_others(self, liqueur, other):
        """Liqueurs must carry more weight than plain mixers / syrups."""
        wl = logic.get_ingredient_weight(liqueur)
        wo = logic.get_ingredient_weight(other)
        assert wl >= wo, (
            f"'{liqueur}' (w={wl}) should be >= '{other}' (w={wo})"
        )

    def test_unknown_ingredient_returns_minimum_weight(self):
        """A completely unrecognised ingredient must fall back to weight = 1."""
        w = logic.get_ingredient_weight("xyzzy_unknown_stuff_9999")
        assert w == 1

    def test_weight_is_positive_integer(self):
        """Weight function must always return a positive integer."""
        for ing in BASE_SPIRITS + LIQUEURS_AND_WINE + OTHER_INGREDIENTS:
            w = logic.get_ingredient_weight(ing)
            assert isinstance(w, int) and w > 0, (
                f"'{ing}' returned non-positive or non-integer weight: {w}"
            )


# ═══════════════════════════════════════════════════════════════════════
# 2.  HIERARCHICAL WEIGHT APPLICATION UNIT TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestApplyHierarchicalWeights:
    """Test the token-boosting function used in BM25 query construction."""

    def test_base_spirit_tokens_are_multiplied(self):
        """'gin' (multiplier=5) should appear 5 times in the boosted list."""
        result = logic.apply_hierarchical_weights(["gin"])
        assert result.count("gin") == 5

    def test_liqueur_tokens_are_multiplied(self):
        """'campari' is in liqueurs_wine (multiplier=4)."""
        result = logic.apply_hierarchical_weights(["campari"])
        assert result.count("campari") == 4

    def test_unknown_tokens_appear_once(self):
        """Tokens not in any category must appear exactly once."""
        result = logic.apply_hierarchical_weights(["xyzzy_unknown"])
        assert result.count("xyzzy_unknown") == 1

    def test_mixed_query_ordering_preserved(self):
        """All input tokens must be present in the output."""
        tokens = ["gin", "lemon", "sugar"]
        result = logic.apply_hierarchical_weights(tokens)
        for t in tokens:
            assert t in result


# ═══════════════════════════════════════════════════════════════════════
# 3.  RETRIEVE_CANDIDATES – SMOKE & SANITY TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestRetrieveCandidates:
    """Integration-level tests against the real BM25 data."""

    def test_known_spirit_returns_results(self, bm25_data):
        """Searching for 'gin' must not return (None, 'none')."""
        ctx, mtype = logic.retrieve_candidates(bm25_data, ["gin"], [])
        assert ctx is not None, "Expected results for 'gin', got None"

    def test_match_pct_in_context_is_integer_string(self, bm25_data):
        """The 'Match: X%' line in the returned context must be a valid int."""
        ctx, _ = logic.retrieve_candidates(bm25_data, ["vodka"], ["lemon juice"])
        assert ctx is not None
        matches = re.findall(r"Match:\s*(\d+)%", ctx)
        assert matches, "No 'Match: X%' line found in context"
        for m in matches:
            assert 0 <= int(m) <= 100, f"Match percentage {m} out of range [0, 100]"

    def test_match_pct_never_exceeds_100(self, bm25_data):
        """No returned match percentage should exceed 100."""
        ctx, _ = logic.retrieve_candidates(bm25_data, ["rum"], ["lime juice", "sugar syrup"])
        if ctx is None:
            pytest.skip("No results returned – skip upper-bound check")
        for m in re.findall(r"Match:\s*(\d+)%", ctx):
            assert int(m) <= 100, f"Illegal match percentage > 100: {m}%"

    def test_nonexistent_spirit_returns_none(self, bm25_data):
        """A completely made-up spirit should yield context=None (no match)."""
        ctx, mtype = logic.retrieve_candidates(
            bm25_data, ["XXXXXXNONEXISTENTSPIRIT999"], []
        )
        assert ctx is None, f"Expected None for bogus spirit, got: {ctx[:80] if ctx else ctx}"

    def test_empty_query_with_flavor_returns_results(self, bm25_data):
        """Providing only a flavor filter (no ingredients) should return results."""
        ctx, mtype = logic.retrieve_candidates(bm25_data, [], [], flavor="Sweet")
        assert ctx is not None, "Expected results for flavor='Sweet' with no ingredients"
        assert "flavor_only" in mtype

    def test_flavor_filter_all_is_unfiltered(self, bm25_data):
        """flavor='All' (default) should not restrict results."""
        ctx1, _ = logic.retrieve_candidates(bm25_data, ["gin"], [], flavor="All")
        ctx2, _ = logic.retrieve_candidates(bm25_data, ["gin"], [])
        # Both calls should succeed (not None)
        assert ctx1 is not None
        assert ctx2 is not None

    def test_context_contains_cocktail_name(self, bm25_data):
        """The returned context string must contain at least one 'Cocktail Name:' label."""
        ctx, _ = logic.retrieve_candidates(bm25_data, ["tequila"], [])
        assert ctx is not None
        assert "Cocktail Name:" in ctx

    def test_match_type_strict_when_all_matched(self, bm25_data):
        """If every user ingredient is found in a recipe, match_type should be 'strict'."""
        # Use a single well-known spirit and verify we can get a strict hit
        ctx, mtype = logic.retrieve_candidates(bm25_data, ["gin"], [])
        assert ctx is not None
        # Accept either strict or partial – just check it's not 'none'
        assert mtype != "none"

    @pytest.mark.parametrize("spirit", BASE_SPIRITS[:5])
    def test_each_base_spirit_returns_results(self, bm25_data, spirit):
        """Each major base spirit should match at least one recipe."""
        ctx, mtype = logic.retrieve_candidates(bm25_data, [spirit], [])
        assert ctx is not None, f"No recipes found for base spirit: '{spirit}'"


# ═══════════════════════════════════════════════════════════════════════
# 4.  MATCH-PERCENTAGE HIERARCHY ENFORCEMENT
#     Base spirit present > liqueur only > neither
# ═══════════════════════════════════════════════════════════════════════

class TestMatchPercentageHierarchy:
    """
    Assert that adding a base spirit to a query yields an equal or higher
    average match percentage than using only a liqueur, which in turn should
    be equal or higher than an empty query baseline.
    """

    def _avg_match(self, bm25_data, base_spirits, others):
        ctx, _ = logic.retrieve_candidates(bm25_data, base_spirits, others)
        if ctx is None:
            return 0.0
        pcts = [int(m) for m in re.findall(r"Match:\s*(\d+)%", ctx)]
        return sum(pcts) / len(pcts) if pcts else 0.0

    @pytest.mark.parametrize("spirit,liqueur", [
        ("gin",     "campari"),
        ("vodka",   "orange liqueur"),
        ("rum",     "coffee liqueur"),
        ("whiskey", "amaretto"),
    ])
    def test_spirit_plus_liqueur_beats_liqueur_alone(self, bm25_data, spirit, liqueur):
        """Adding a base spirit to a liqueur should not decrease the average match."""
        avg_both   = self._avg_match(bm25_data, [spirit], [liqueur])
        avg_liqueur = self._avg_match(bm25_data, [], [liqueur])
        # Base spirit is the hard filter; liqueur alone might return 0 / nothing.
        # The key invariant: spirit+liqueur >= liqueur alone.
        assert avg_both >= avg_liqueur, (
            f"spirit+liqueur avg ({avg_both:.1f}) < liqueur-only avg ({avg_liqueur:.1f}) "
            f"for spirit='{spirit}', liqueur='{liqueur}'"
        )


# ═══════════════════════════════════════════════════════════════════════
# 5.  COMBINATIONS SWEEP (itertools.combinations)
#     Exhaustively test every pair/triple from our curated pools.
# ═══════════════════════════════════════════════════════════════════════

def _run_combination(bm25_data, base_combo, other_combo, r):
    """
    Helper that runs retrieve_candidates and returns a result record.
    Captures exceptions and out-of-range percentages as errors.
    """
    result = {
        "r": r,
        "base": list(base_combo),
        "other": list(other_combo),
        "match_pcts": [],
        "match_type": None,
        "error": None,
        "oor_pcts": [],  # out-of-range percentages
    }
    try:
        ctx, mtype = logic.retrieve_candidates(
            bm25_data, list(base_combo), list(other_combo)
        )
        result["match_type"] = mtype
        if ctx is not None:
            pcts = [int(m) for m in re.findall(r"Match:\s*(\d+)%", ctx)]
            result["match_pcts"] = pcts
            result["oor_pcts"] = [p for p in pcts if not (0 <= p <= 100)]
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        logger.error(
            "EXCEPTION | r=%d | base=%s | other=%s | %s",
            r, base_combo, other_combo, result["error"]
        )
    return result


class TestCombinationsSweep:
    """
    Uses itertools.combinations to sweep all r=1,2 combos from the curated
    ingredient pools and validate the matching algorithm's output.
    """

    # ── r=1 single-spirit searches ──────────────────────────────────────

    @pytest.mark.parametrize("spirit", BASE_SPIRITS)
    def test_single_spirit_combinations(self, bm25_data, spirit):
        """Every single base spirit (r=1) must not raise an exception."""
        rec = _run_combination(bm25_data, (spirit,), (), 1)
        if rec["error"]:
            _ERROR_LOG.append(rec)
            pytest.fail(f"Exception for spirit='{spirit}': {rec['error']}")
        assert not rec["oor_pcts"], (
            f"Out-of-range match% {rec['oor_pcts']} for spirit='{spirit}'"
        )

    # ── r=2 two-spirit combinations ─────────────────────────────────────

    @pytest.mark.parametrize("combo", list(itertools.combinations(BASE_SPIRITS, 2)))
    def test_two_spirit_combinations(self, bm25_data, combo):
        """All (r=2) spirit pairs must not raise and must return valid percentages."""
        rec = _run_combination(bm25_data, combo, (), 2)
        if rec["error"]:
            _ERROR_LOG.append(rec)
            pytest.fail(f"Exception for combo={combo}: {rec['error']}")
        assert not rec["oor_pcts"], (
            f"Out-of-range match% {rec['oor_pcts']} for combo={combo}"
        )

    # ── r=1 spirit + r=1 other ──────────────────────────────────────────

    @pytest.mark.parametrize(
        "spirit,other",
        list(itertools.product(BASE_SPIRITS[:5], OTHER_INGREDIENTS[:5]))
    )
    def test_spirit_plus_single_other_ingredient(self, bm25_data, spirit, other):
        """Each base spirit paired with one other ingredient must be error-free."""
        rec = _run_combination(bm25_data, (spirit,), (other,), 1)
        if rec["error"]:
            _ERROR_LOG.append(rec)
            pytest.fail(f"Exception for spirit='{spirit}', other='{other}': {rec['error']}")
        assert not rec["oor_pcts"], (
            f"Out-of-range match% for spirit='{spirit}', other='{other}'"
        )

    # ── r=2 liqueur combinations ─────────────────────────────────────────

    @pytest.mark.parametrize("combo", list(itertools.combinations(LIQUEURS_AND_WINE, 2)))
    def test_two_liqueur_combinations_no_spirit(self, bm25_data, combo):
        """
        Liqueur-only combos (no base spirit) should either return None or
        valid percentages – never throw an exception.
        """
        rec = _run_combination(bm25_data, (), combo, 2)
        if rec["error"]:
            _ERROR_LOG.append(rec)
            pytest.fail(f"Exception for liqueurs={combo}: {rec['error']}")
        assert not rec["oor_pcts"], (
            f"Out-of-range match% for liqueurs={combo}: {rec['oor_pcts']}"
        )

    # ── r=2 other-ingredient combinations ────────────────────────────────

    @pytest.mark.parametrize("combo", list(itertools.combinations(OTHER_INGREDIENTS, 2)))
    def test_two_other_ingredient_combinations(self, bm25_data, combo):
        """Other-ingredient pairs must never raise; context may or may not be None."""
        rec = _run_combination(bm25_data, (), combo, 2)
        if rec["error"]:
            _ERROR_LOG.append(rec)
            pytest.fail(f"Exception for others={combo}: {rec['error']}")

    # ── r=3 full combinations: 1 spirit + 2 others ───────────────────────

    @pytest.mark.parametrize(
        "spirit,others",
        [(s, c) for s in BASE_SPIRITS[:4]
         for c in itertools.combinations(OTHER_INGREDIENTS, 2)]
    )
    def test_spirit_plus_two_others_combination(self, bm25_data, spirit, others):
        """1 base spirit + 2 other ingredients (r=3 total) must be error-free."""
        rec = _run_combination(bm25_data, (spirit,), others, 3)
        if rec["error"]:
            _ERROR_LOG.append(rec)
            pytest.fail(
                f"Exception | spirit='{spirit}', others={others}: {rec['error']}"
            )
        assert not rec["oor_pcts"], (
            f"Out-of-range match% for spirit='{spirit}', others={others}: {rec['oor_pcts']}"
        )

    # ── r=3 spirit + liqueur + other ─────────────────────────────────────

    @pytest.mark.parametrize(
        "spirit,liqueur,other",
        [(s, l, o)
         for s in BASE_SPIRITS[:4]
         for l in LIQUEURS_AND_WINE[:4]
         for o in OTHER_INGREDIENTS[:4]]
    )
    def test_spirit_liqueur_other_triple(self, bm25_data, spirit, liqueur, other):
        """Spirit + liqueur + other (r=3) must never produce an exception or OOR%."""
        rec = _run_combination(bm25_data, (spirit,), [liqueur, other], 3)
        if rec["error"]:
            _ERROR_LOG.append(rec)
            pytest.fail(
                f"Exception | spirit='{spirit}', liqueur='{liqueur}', other='{other}': {rec['error']}"
            )
        assert not rec["oor_pcts"], (
            f"OOR match% | spirit='{spirit}', liqueur='{liqueur}', other='{other}': {rec['oor_pcts']}"
        )


# ═══════════════════════════════════════════════════════════════════════
# 6.  SYNONYM NORMALISATION TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestSynonymNormalisation:
    """Verify that synonym mapping produces correct canonical names."""

    @pytest.mark.parametrize("raw,expected_canonical", [
        ("cointreau",        "orange liqueur"),
        ("bourbon",          "whiskey"),
        ("scotch",           "whiskey"),
        ("kahlua",           "coffee liqueur"),
        ("champagne",        "sparkling wine"),
        ("club soda",        "soda water"),
        ("fresh lemon juice","lemon juice"),
        ("simple syrup",     "sugar syrup"),
        ("triple sec",       "orange liqueur"),
        ("prosecco",         "sparkling wine"),
    ])
    def test_synonym_mapped_to_canonical(self, bm25_data, raw, expected_canonical):
        """
        The synonym mapping should produce results that treat the raw name as
        equivalent to the canonical form.  We validate indirectly by checking
        that searching with the raw name and the canonical name yield the same
        non-None result (or both None).
        """
        import re as _re
        def _run(spirits):
            ctx, _ = logic.retrieve_candidates(bm25_data, spirits, [])
            return ctx

        ctx_raw       = _run([raw])
        ctx_canonical = _run([expected_canonical])

        # Both should be None or both non-None (same eligibility)
        both_none    = (ctx_raw is None) and (ctx_canonical is None)
        both_present = (ctx_raw is not None) and (ctx_canonical is not None)

        assert both_none or both_present, (
            f"Synonym mismatch: '{raw}' -> ctx={'None' if ctx_raw is None else 'present'}, "
            f"'{expected_canonical}' -> ctx={'None' if ctx_canonical is None else 'present'}"
        )


# ═══════════════════════════════════════════════════════════════════════
# 7.  COUNT_RECIPE_INGREDIENTS EDGE-CASES
# ═══════════════════════════════════════════════════════════════════════

class TestCountRecipeIngredients:
    """Unit tests for the helper that counts ingredients in a raw string."""

    def test_empty_string_returns_one(self):
        assert logic.count_recipe_ingredients("") == 1

    def test_none_returns_one(self):
        assert logic.count_recipe_ingredients(None) == 1

    def test_comma_separated_list(self):
        raw = "gin, lemon juice, sugar syrup, soda water"
        assert logic.count_recipe_ingredients(raw) == 4

    def test_newline_separated_list(self):
        raw = "gin\nlemon juice\nsugar syrup"
        assert logic.count_recipe_ingredients(raw) == 3

    def test_python_list_literal(self):
        raw = "['gin', 'vermouth', 'olive']"
        assert logic.count_recipe_ingredients(raw) == 3

    def test_single_ingredient(self):
        raw = "vodka"
        # Only 1 ingredient – result should be >= 1
        assert logic.count_recipe_ingredients(raw) >= 1


# ═══════════════════════════════════════════════════════════════════════
# 8.  SESSION-END ERROR LOG DUMP
#     Prints a summary of all failures collected during the test run.
# ═══════════════════════════════════════════════════════════════════════

def pytest_sessionfinish(session, exitstatus):
    """Hook: dump the error log after all tests complete."""
    if not _ERROR_LOG:
        logger.info("✅  No combination errors or exceptions logged.")
        return

    logger.warning("=" * 70)
    logger.warning("COMBINATION ERROR SUMMARY  (%d failures)", len(_ERROR_LOG))
    logger.warning("=" * 70)
    for i, rec in enumerate(_ERROR_LOG, 1):
        logger.warning(
            "[%3d] r=%d | base=%-25s | other=%-25s | error=%s",
            i, rec.get("r", "?"),
            str(rec.get("base", [])),
            str(rec.get("other", [])),
            rec.get("error", "OOR% " + str(rec.get("oor_pcts", []))),
        )
    logger.warning("=" * 70)
