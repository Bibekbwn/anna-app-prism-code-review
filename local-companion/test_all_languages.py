import importlib

spec = importlib.util.spec_from_file_location("server", "local-companion/server.py")
server_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server_module)

# Test all 12 supported languages
test_cases = [
    ("Python", "def main():\n    return 1"),
    ("JavaScript / TypeScript", "const total: number = 1"),
    ("Go", "package main\nfunc main() {}"),
    ("Rust", "fn main() {}"),
    ("Java", "public class Main { public static void main(String[] args) {}}"),
    ("C#", "public static void Main() { return 0; }"),
    ("C", "#include <stdio.h>\nint main() { printf(\"hello\"); return 0; }"),
    ("C++", "#include <iostream>\nint main() { return 0; }"),
    ("Ruby", "def main\n  puts 1\nend"),
    ("PHP", "<?php function main() { return 1; }"),
    ("Kotlin", "fun main() { return 0 }"),
    ("Swift", "func main() { print(1) }"),
]

print("Testing language detection for all 12 supported languages:\n")
for language, code in test_cases:
    try:
        result = server_module.server._detect_language(code)
        print(f"  ✅ {language:20s} -> {result}")
    except Exception as e:
        print(f"  ❌ {language:20s} -> ERROR: {type(e).__name__}: {e}")

print("\n" + "="*60)
print("Testing _safe_filename for all languages:\n")
for language, code in test_cases:
    try:
        result = server_module.server._safe_filename(language)
        print(f"  ✅ {language:20s} -> {result}")
    except Exception as e:
        print(f"  ❌ {language:20s} -> ERROR: {type(e).__name__}: {e}")