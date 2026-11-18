import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quality_metrics import accessibility_findings, category_scores


class AccessibilityChecksTest(unittest.TestCase):
    def test_detects_missing_image_alt_and_form_label(self):
        source = '<img src="hero.png" />\n<input type="email" />'
        findings = accessibility_findings(source, "snippet.tsx", "JavaScript / TypeScript")
        self.assertEqual(
            {finding["rule_id"] for finding in findings},
            {"A11Y-IMG-ALT", "A11Y-FORM-LABEL"},
        )
        self.assertTrue(all(not finding["blocking"] for finding in findings))

    def test_accepts_named_controls_and_buttons(self):
        source = (
            '<img src="hero.png" alt="Team working" />\n'
            '<label htmlFor="email">Email</label><input id="email" />\n'
            '<button aria-label="Close"><svg /></button>'
        )
        self.assertEqual(accessibility_findings(source, "snippet.tsx", "JavaScript / TypeScript"), [])

    def test_flags_nonsemantic_click_target(self):
        source = '<div onClick={save}>Save</div>'
        findings = accessibility_findings(source, "snippet.tsx", "JavaScript / TypeScript")
        self.assertEqual([finding["rule_id"] for finding in findings], ["A11Y-KEYBOARD"])

    def test_non_web_language_is_not_scored_as_accessibility_pass(self):
        scores = category_scores([], {"security", "quality", "test"}, "Python", False)
        self.assertIsNone(scores["accessibility"]["score"])
        self.assertFalse(scores["accessibility"]["assessed"])


class ReviewScoreTest(unittest.TestCase):
    def test_clean_assessed_categories_score_full(self):
        agents = {"security", "quality", "test"}
        scores = category_scores([], agents, "JavaScript / TypeScript", False)
        for category in ("security", "quality", "efficiency", "testing", "accessibility"):
            self.assertEqual(scores[category]["score"], 100)
            self.assertTrue(scores[category]["assessed"])

    def test_security_finding_reduces_security_only(self):
        findings = [{
            "agent": "security",
            "category": "Secret Exposure",
            "severity": "high",
            "confidence": 1.0,
        }]
        scores = category_scores(findings, {"security", "quality", "test"}, "Python", False)
        self.assertLess(scores["security"]["score"], 100)
        self.assertEqual(scores["quality"]["score"], 100)
        self.assertEqual(scores["testing"]["score"], 100)

    def test_unrun_category_is_not_reported_as_perfect(self):
        scores = category_scores([], set(), "Python", False)
        self.assertIsNone(scores["security"]["score"])
        self.assertFalse(scores["security"]["assessed"])


if __name__ == "__main__":
    unittest.main()
