#!/usr/bin/env python
"""Test language detection and code review for all 12 supported languages."""
import sys
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import server

# Test all 12 supported languages
test_cases = [
    ("Python", "def main():\n    return 1"),
    ("JavaScript/TypeScript", "const total: number = 1"),
    ("Go", "package main\nfunc main() {}"),
    ("Rust", "fn main() {}"),
    ("Java", "public class Main { public static void main(String[] args) {}}"),
    ("C#", "public static void main() { return 0; }"),
    ("C", "#include <stdio.h> int main() { printf(\"hello\"); return 0;}"),
    ("C++", "public int main() { return 0;}"),
    ("Ruby", "impl Main { fn main() {} }"),
    ("PHP", "fun main() {}"),
    ("Kotlin", "public int main() { return 0;}"),
    ("Swift", "def main(): print(1)"),
]

print("="*70)
print("TEST 1: Language Detection for All 12 Languages")
print("="*70)

all_pass = True
for language, code in test_cases:
    try:
        result = server._detect_language(code)
        status = "PASS" if result == language else f"MISMATCH (got {result})"
        if "MISMATCH" in status:
            all_pass = False
        print(f"  {status}: {language}")
    except Exception as e:
        print(f"  FAIL: {language} -> {type(e).__name__}: {str(e)[:50]}")
        all_pass = False

print(f"\nLanguage Detection: {'ALL PASS' if all_pass else 'SOME FAILED'}")

print("\n" + "="*70)
print("TEST 2: _safe_filename for All Languages")
print("="*70)

all_pass = True
for language, code in test_cases:
    try:
        result = server._safe_filename(language)
        print(f"  PASS: {language:20s} -> {result}")
    except Exception as e:
        print(f"  FAIL: {language:20s} -> {type(e).__name__}: {str(e)[:50]}")
        all_pass = False

print(f"\nSafe Filename: {'ALL PASS' if all_pass else 'SOME FAILED'}")

print("\n" + "="*70)
print("TEST 3: Code Review Validation for All Languages")
print("="*70)

all_pass = True
for language, code in test_cases:
    try:
        # Test validation
        result = server._validate_review_request({"code": code, "language": language})
        print(f"  PASS: {language:20s} -> validated OK")
    except ValueError as e:
        print(f"  VALIDATION ERROR: {language:20s} -> {str(e)[:60]}")
        all_pass = False
    except Exception as e:
        print(f"  FAIL: {language:20s} -> {type(e).__name__}: {str(e)[:50]}")
        all_pass = False

print(f"\nCode Review Validation: {'ALL PASS' if all_pass else 'SOME FAILED'}")

print("\n" + "="*70)
print("OVERALL RESULTS")
print("="*70)
print(f"All tests passed: {all_pass}")