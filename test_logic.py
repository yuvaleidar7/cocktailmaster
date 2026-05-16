"""
Unit tests for the bilingual ingredient search flow in logic.py.

Covers:
  1. Exact (strict) match — English input.
  2. Typo input (English) — thefuzz corrects and finds the right ingredient.
  3. Hebrew input — fuzzy match + translation to English for BM25.
  4. Non-existent ingredient — fallback with suggestions.
  5. Edge cases.

The BM25 data is mocked with 4 small cocktails so that
tests run instantly and don't require the real pickle/database files.
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock

import logic


# ---------------------------------------------------------------------------
# Mock data — a minimal BM25 dataset with 4 cocktails
# ---------------------------------------------------------------------------

MOCK_DOCS = [
    "Cocktail: Mojito\nGlassware: Highball\nIngredients:\n- 45 ml White Rum\n- 20 ml Fresh Lime Juice\n- 6 Mint Leaves\n- 2 tsp Sugar\n- Soda Water\n\nPreparation:\nMuddle mint and sugar, add rum and lime, top with soda.",

    "Cocktail: Margarita\nGlassware: Margarita Glass\nIngredients:\n- 50 ml Tequila\n- 25 ml Triple Sec\n- 15 ml Fresh Lime Juice\n\nPreparation:\nShake all ingredients with ice, strain into glass.",

    "Cocktail: Moscow Mule\nGlassware: Copper Mug\nIngredients:\n- 45 ml Vodka\n- 10 ml Fresh Lime Juice\n- 120 ml Ginger Beer\n\nPreparation:\nPour vodka and lime into mug, add ice, top with ginger beer.",

    "Cocktail: Cosmopolitan\nGlassware: Cocktail Glass\nIngredients:\n- 40 ml Vodka\n- 15 ml Cointreau\n- 15 ml Fresh Lime Juice\n- 30 ml Cranberry Juice\n\nPreparation:\nShake all ingredients with ice, strain into chilled glass.",
]

MOCK_METADATAS = [
    {
        "name": "Mojito",
        "glassware": "Highball",
        "ingredients_raw": "- 45 ml White Rum\n- 20 ml Fresh Lime Juice\n- 6 Mint Leaves\n- 2 tsp Sugar\n- Soda Water",
    },
    {
        "name": "Margarita",
        "glassware": "Margarita Glass",
        "ingredients_raw": "- 50 ml Tequila\n- 25 ml Triple Sec\n- 15 ml Fresh Lime Juice",
    },
    {
        "name": "Moscow Mule",
        "glassware": "Copper Mug",
        "ingredients_raw": "- 45 ml Vodka\n- 10 ml Fresh Lime Juice\n- 120 ml Ginger Beer",
    },
    {
        "name": "Cosmopolitan",
        "glassware": "Cocktail Glass",
        "ingredients_raw": "- 40 ml Vodka\n- 15 ml Cointreau\n- 15 ml Fresh Lime Juice\n- 30 ml Cranberry Juice",
    },
]


def _build_mock_bm25_data():
    """
    Build a mock bm25_data dict that mimics the real pickle structure.

    The mock BM25 object returns scores that favour documents whose
    text contains more of the query tokens (a rough bag-of-words proxy).
    """
    bm25_mock = MagicMock()

    def fake_get_scores(tokenized_query):
        """Score each doc by how many query tokens appear in it."""
        scores = []
        for doc in MOCK_DOCS:
            doc_lower = doc.lower()
            score = sum(1.0 for t in tokenized_query if t in doc_lower)
            scores.append(score)
        return np.array(scores)

    bm25_mock.get_scores = fake_get_scores

    return {
        "bm25": bm25_mock,
        "ids": [f"id-{i}" for i in range(len(MOCK_DOCS))],
        "docs": MOCK_DOCS,
        "metadatas": MOCK_METADATAS,
    }


@pytest.fixture
def bm25_data():
    """Provide the mock BM25 dataset to every test that needs it."""
    return _build_mock_bm25_data()


# ===================================================================
# 1. Exact (strict) match — English
# ===================================================================

class TestExactMatch:
    """When every user word appears in at least one cocktail's ingredient list."""

    def test_vodka_lime_returns_strict(self, bm25_data):
        """'vodka lime' should strictly match Moscow Mule and Cosmopolitan."""
        context, match_type = logic.retrieve_candidates(bm25_data, "vodka lime")
        assert match_type == "strict"
        assert context is not None

    def test_strict_context_contains_cocktail_name(self, bm25_data):
        """The returned context string must mention the matched cocktail(s)."""
        context, _ = logic.retrieve_candidates(bm25_data, "vodka lime")
        assert "Moscow Mule" in context or "Cosmopolitan" in context

    def test_single_ingredient_strict(self, bm25_data):
        """A single valid ingredient should still produce a strict match."""
        context, match_type = logic.retrieve_candidates(bm25_data, "tequila")
        assert match_type == "strict"
        assert "Margarita" in context

    def test_rum_mint_strict_finds_mojito(self, bm25_data):
        """'rum mint' should strictly match only the Mojito."""
        context, match_type = logic.retrieve_candidates(bm25_data, "rum mint")
        assert match_type == "strict"
        assert "Mojito" in context


# ===================================================================
# 2. English typo auto-correction (thefuzz)
# ===================================================================

class TestEnglishTypoCorrection:
    """Ensure correct_query fixes English typos via thefuzz."""

    def test_correct_query_fixes_vodca(self):
        """'vodca' should be corrected to 'vodka' (score >= 80)."""
        result = logic.correct_query("vodca")
        assert result == "vodka"

    def test_correct_query_fixes_limee(self):
        """'limee' (typo for lime) should be corrected to 'lime'."""
        result = logic.correct_query("limee")
        assert result == "lime"

    def test_correct_query_preserves_valid_words(self):
        """Already-correct words should pass through unchanged."""
        result = logic.correct_query("vodka lime")
        assert result == "vodka lime"

    def test_debug_message_on_correction(self, capsys):
        """A [תיקון] debug line should be printed for every correction."""
        logic.correct_query("vodca")
        captured = capsys.readouterr()
        assert "[תיקון]" in captured.out
        assert "'vodca'" in captured.out
        assert "'vodka'" in captured.out

    def test_typo_still_finds_strict_match(self, bm25_data):
        """
        End-to-end: 'vodca limee' → thefuzz → 'vodka lime' → strict match.
        """
        corrected = logic.correct_query("vodca limee")
        assert "vodka" in corrected
        assert "lime" in corrected

        context, match_type = logic.retrieve_candidates(bm25_data, corrected)
        assert match_type == "strict"
        assert "Moscow Mule" in context or "Cosmopolitan" in context


# ===================================================================
# 3. Hebrew input — fuzzy match + translation to English
# ===================================================================

class TestHebrewCorrection:
    """Hebrew ingredient input: fuzzy match → translate → English for BM25."""

    def test_exact_hebrew_translates_to_english(self):
        """'וודקה' (vodka in Hebrew) should translate to 'vodka'."""
        result = logic.correct_query("וודקה")
        assert "vodka" in result

    def test_hebrew_typo_corrected_and_translated(self):
        """'וודקא' (typo for וודקה) should correct and translate to 'vodka'."""
        result = logic.correct_query("וודקא")
        assert "vodka" in result

    def test_multi_word_hebrew_ingredient(self):
        """'מיץ לימון' (lemon juice) should translate to English."""
        result = logic.correct_query("מיץ לימון")
        assert "lemon" in result

    def test_hebrew_debug_message(self, capsys):
        """Hebrew correction should print a [תרגום] or [תיקון] debug message."""
        logic.correct_query("וודקה")
        captured = capsys.readouterr()
        assert "[תרגום]" in captured.out or "[תיקון]" in captured.out

    def test_hebrew_vodka_lime_finds_strict_match(self, bm25_data):
        """End-to-end: 'וודקה מיץ ליים' → translate → 'vodka lime juice' → strict."""
        corrected = logic.correct_query("וודקה מיץ ליים")
        assert "vodka" in corrected
        assert "lime" in corrected

        context, match_type = logic.retrieve_candidates(bm25_data, corrected)
        assert match_type == "strict"

    def test_hebrew_prefix_stripping(self):
        """Hebrew prefix (ה) should be stripped: 'הוודקה' → 'וודקה' → 'vodka'."""
        result = logic.correct_query("הוודקה")
        assert "vodka" in result

    def test_hebrew_preserves_english_words(self):
        """English words in a Hebrew query should not be mangled."""
        # If user mixes languages, English parts should survive
        result = logic.correct_query("vodka")
        # No Hebrew detected → uses English path
        assert result == "vodka"

    def test_contains_hebrew_detection(self):
        """_contains_hebrew correctly identifies Hebrew text."""
        assert logic._contains_hebrew("וודקה") is True
        assert logic._contains_hebrew("vodka") is False
        assert logic._contains_hebrew("וודקה vodka") is True


# ===================================================================
# 4. Non-existent ingredient → fallback with suggestions
# ===================================================================

class TestFallbackLogic:
    """When NO user word appears in any cocktail's ingredient list."""

    def test_nonsense_triggers_fallback(self, bm25_data):
        """A completely made-up ingredient should trigger the fallback path."""
        context, match_type = logic.retrieve_candidates(bm25_data, "xyzzberry")
        assert match_type.startswith("fallback")

    def test_fallback_returns_context_not_none(self, bm25_data):
        """Even on fallback, the function must return context (not None)."""
        context, _ = logic.retrieve_candidates(bm25_data, "dragonfruit guarana")
        assert context is not None
        assert len(context) > 0

    def test_fallback_contains_suggestions(self, bm25_data):
        """The match_type string should include pipe-separated suggestions."""
        _, match_type = logic.retrieve_candidates(bm25_data, "xyzzberry")
        assert "|" in match_type
        suggestions_str = match_type.split("|")[1]
        suggestions = [s.strip() for s in suggestions_str.split(",")]
        assert len(suggestions) >= 1  # at least one suggestion
        assert len(suggestions) <= 3  # at most three

    def test_fallback_suggestions_are_real_ingredients(self, bm25_data):
        """Suggested alternatives must be actual ingredient words from the mock DB."""
        all_ingredient_text = " ".join(
            m["ingredients_raw"].lower() for m in MOCK_METADATAS
        )
        _, match_type = logic.retrieve_candidates(bm25_data, "xyzzberry")
        suggestions_str = match_type.split("|")[1]
        for suggestion in suggestions_str.split(", "):
            assert suggestion in all_ingredient_text, (
                f"Suggestion '{suggestion}' is not found in any cocktail's ingredients"
            )

    def test_fallback_prints_debug_message(self, bm25_data, capsys):
        """A [Fallback] debug line should be printed when fallback triggers."""
        logic.retrieve_candidates(bm25_data, "xyzzberry")
        captured = capsys.readouterr()
        assert "[Fallback]" in captured.out

    def test_fallback_returns_cocktail_docs(self, bm25_data):
        """Fallback context should still contain formatted cocktail data."""
        context, _ = logic.retrieve_candidates(bm25_data, "xyzzberry")
        assert "Cocktail Name:" in context
        assert "Original Data:" in context


# ===================================================================
# 5. Edge cases
# ===================================================================

class TestEdgeCases:
    """Guard-rails for unusual or empty inputs."""

    def test_empty_query_returns_none(self, bm25_data):
        """An empty string should return (None, 'none')."""
        context, match_type = logic.retrieve_candidates(bm25_data, "")
        assert context is None
        assert match_type == "none"

    def test_numbers_only_returns_none(self, bm25_data):
        """A query of only numbers (no alpha words ≥ 2 chars) → none."""
        context, match_type = logic.retrieve_candidates(bm25_data, "123 456")
        assert context is None
        assert match_type == "none"

    def test_partial_match_when_one_word_missing(self, bm25_data):
        """
        'vodka unicornberry' — vodka exists but unicornberry doesn't.
        Should produce a partial match.
        """
        context, match_type = logic.retrieve_candidates(bm25_data, "vodka unicornberry")
        assert match_type.startswith("partial")
        assert "unicornberry" in match_type

    def test_correct_query_handles_empty_string(self):
        """correct_query should not crash on empty input."""
        result = logic.correct_query("")
        assert result == ""

    def test_strip_hebrew_prefix_only_on_hebrew(self):
        """_strip_hebrew_prefix should NOT modify English words."""
        assert logic._strip_hebrew_prefix("mint") == "mint"
        assert logic._strip_hebrew_prefix("hello") == "hello"

    def test_strip_hebrew_prefix_removes_prefix(self):
        """_strip_hebrew_prefix should remove ה from 'הוודקה'."""
        result = logic._strip_hebrew_prefix("הוודקה")
        assert result == "וודקה"

    def test_strip_hebrew_prefix_preserves_short_words(self):
        """Single-char or two-char Hebrew words should not be stripped."""
        assert logic._strip_hebrew_prefix("מל") == "מל"  # too short to strip
