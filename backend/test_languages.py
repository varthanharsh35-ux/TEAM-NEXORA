"""Task 3.8: Tests for languages, locale files recovery, and reviewed financial glossary."""

import json
import unittest
from pathlib import Path

from glossary import (
    COMPLETE_LANGUAGES,
    PLANNED_LANGUAGES,
    ALL_LANGUAGES,
    get_term,
    get_glossary,
    is_language_complete,
    is_language_planned,
    protect_financial_terms,
)

ROOT = Path(__file__).resolve().parents[1]
LOCALES_DIR = ROOT / "frontend" / "src" / "locales"
SERVICES_DIR = ROOT / "frontend" / "src" / "services"


class LocaleRecoveryTests(unittest.TestCase):
    """Assert all 8 original locale files are recovered."""

    RECOVERED_LOCALES = ["en", "ta", "hi", "te", "kn", "bn", "mr", "gu"]

    def test_all_eight_locale_files_exist_in_frontend(self):
        for loc in self.RECOVERED_LOCALES:
            path = LOCALES_DIR / f"{loc}.json"
            self.assertTrue(path.exists(), f"Locale file missing: {loc}.json")

    def test_all_locale_files_are_valid_json(self):
        for loc in self.RECOVERED_LOCALES:
            path = LOCALES_DIR / f"{loc}.json"
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertIsInstance(data, dict, f"{loc}.json is not a valid JSON object")
            self.assertGreater(len(data), 0, f"{loc}.json is empty")

    def test_en_ta_hi_are_complete(self):
        """Complete languages have over 500 keys."""
        for loc in COMPLETE_LANGUAGES:
            path = LOCALES_DIR / f"{loc}.json"
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertGreater(len(data), 500, f"{loc}.json is not complete")


class LanguageStatusTests(unittest.TestCase):
    """SPEC.md §8: en/ta/hi complete, others marked as planned."""

    def test_complete_languages_are_three(self):
        self.assertEqual(COMPLETE_LANGUAGES, ["en", "ta", "hi"])
        for lang in ["en", "ta", "hi"]:
            self.assertTrue(is_language_complete(lang))
            self.assertFalse(is_language_planned(lang))

    def test_planned_languages(self):
        for lang in ["te", "kn", "bn", "mr", "gu"]:
            self.assertTrue(is_language_planned(lang))
            self.assertFalse(is_language_complete(lang))


class FinancialGlossaryTests(unittest.TestCase):
    """SPEC.md §8: Financial and legal terms use a reviewed glossary, never machine translation."""

    CRITICAL_TERMS = [
        "moratorium",
        "margin_money",
        "working_capital",
        "term_loan",
        "reducing_balance",
        "capitalised_interest",
        "quarterly_instalment",
        "subsidy",
        "collateral",
        "sanctioning_agency",
    ]

    def test_glossary_has_all_critical_terms(self):
        glossary = get_glossary()
        for term in self.CRITICAL_TERMS:
            self.assertIn(term, glossary, f"Missing critical term in glossary: {term}")

    def test_all_critical_terms_marked_do_not_machine_translate(self):
        glossary = get_glossary()
        for term in self.CRITICAL_TERMS:
            entry = glossary[term]
            self.assertTrue(entry.get("do_not_machine_translate"), f"{term} not marked do_not_machine_translate")

    def test_reviewed_translations_present_for_complete_languages(self):
        for term in self.CRITICAL_TERMS:
            for lang in COMPLETE_LANGUAGES:
                val = get_term(term, lang)
                self.assertIsNotNone(val, f"Missing {lang} translation for {term}")
                self.assertGreater(len(val), 0)

    def test_protect_financial_terms_replaces_moratorium(self):
        input_text = "The loan has a 6-month moratorium period before payments begin."
        protected_ta = protect_financial_terms(input_text, "ta")
        # Should replace 'moratorium period' with reviewed Tamil phrase
        self.assertIn("தவணை இல்லாத சலுகைக் காலம்", protected_ta)

    def test_protect_financial_terms_replaces_margin_money(self):
        input_text = "Applicant must provide 10% margin money."
        protected_hi = protect_financial_terms(input_text, "hi")
        self.assertIn("मार्जिन राशि", protected_hi)


class FrontendServicesTests(unittest.TestCase):
    """Verify Bhashini service and Pluggable translator service files."""

    def test_bhashini_service_recovered(self):
        bhashini_file = SERVICES_DIR / "bhashini.js"
        self.assertTrue(bhashini_file.exists(), "bhashini.js was not recovered to frontend/src/services/")
        content = bhashini_file.read_text(encoding="utf-8")
        self.assertIn("BHASHINI_PIPELINE_URL", content)
        self.assertIn("translateText", content)

    def test_pluggable_translator_service_exists(self):
        translator_file = SERVICES_DIR / "translator.js"
        self.assertTrue(translator_file.exists(), "translator.js missing in frontend/src/services/")
        content = translator_file.read_text(encoding="utf-8")
        self.assertIn("bhashiniProvider", content)
        self.assertIn("googleProvider", content)
        self.assertIn("setProvider", content)
        self.assertIn("applyGlossary", content)


if __name__ == "__main__":
    unittest.main()
