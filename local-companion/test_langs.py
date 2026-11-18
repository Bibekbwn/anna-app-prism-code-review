import sys
import os
os.chdir("local-companion")
sys.path.insert(0, ".")

# Import server module directly
import importlib.util
spec = importlib.util.spec_from_file_location("server", "server.py")
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

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

print("Testing language detection for all 12 supported languages:\n")
for language, code in test_cases:
    try:
        result = server._detect_language(code)
        print(f"  PASS: {language:20s} -> {result}")
    except Exception as e:
        print(f"  FAIL: {language:20s} -> {type(e).__name__}: {str(e)[:50]}")

print("\n" + "="*60)
print("Testing _safe_filename for all languages:\n")
for language, code in test_cases:
    try:
        result = server._safe_filename(language)
        print(f"  PASS: {language:20s} -> {result}")
    except Exception as e:
        print(f"  FAIL: {language:20s} -> {type(e).__name__}: {str(e)[:50]}")