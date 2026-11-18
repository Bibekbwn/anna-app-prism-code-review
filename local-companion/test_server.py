import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import server


class ReviewInputTests(unittest.TestCase):
    def test_detects_common_supported_languages(self):
        self.assertEqual(server._detect_language("def main():\n    return 1"), "Python")
        self.assertEqual(server._detect_language("const total: number = 1"), "JavaScript / TypeScript")
        self.assertEqual(server._detect_language("package main\nfunc main() {}"), "Go")

    def test_filename_is_selected_from_supported_language(self):
        self.assertEqual(server._safe_filename("C++"), "snippet.cpp")
        self.assertEqual(server._safe_filename("JavaScript / TypeScript"), "snippet.ts")
        self.assertEqual(server._safe_filename("unknown"), "snippet.py")

    def test_review_input_limits_and_invalid_languages(self):
        with self.assertRaises(ValueError):
            server._validate_review_request({"code": "  ", "language": "Python"})
        with self.assertRaises(ValueError):
            server._validate_review_request({"code": "x" * 40001, "language": "Python"})
        with self.assertRaises(ValueError):
            server._validate_review_request({"code": "print(1)", "language": "Unsupported"})


class LocalSettingsTests(unittest.TestCase):
    def test_settings_round_trip_and_template_filtering(self):
        with tempfile.TemporaryDirectory() as directory:
            settings_path = Path(directory) / "settings.json"
            with patch.object(server, "SETTINGS_FILE", settings_path):
                server._write_settings({
                    "effort": "Lite",
                    "theme": "Light",
                    "showSuggestions": False,
                    "templates": [
                        {"id": "safe", "name": "Safe", "description": "Demo", "code": "print(1)"},
                        {"id": "incomplete"},
                    ],
                })
                saved = server._settings()

        self.assertEqual(saved["effort"], "Lite")
        self.assertEqual(saved["theme"], "Light")
        self.assertFalse(saved["showSuggestions"])
        self.assertEqual([item["id"] for item in saved["templates"]], ["safe"])

    def test_ai_status_never_returns_the_key(self):
        secret = "local-test-key-should-not-leak"
        with patch.dict(os.environ, {"MODEL_PROVIDER": "gemini", "GEMINI_API_KEY": secret}):
            with patch("server.importlib.util.find_spec", return_value=object()):
                status = server._provider_status()
        self.assertTrue(status["configured"])
        self.assertNotIn(secret, json.dumps(status))


if __name__ == "__main__":
    unittest.main()
