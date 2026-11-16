"""PRISM review engine: deterministic regex agents for code review."""

import re
import os
from typing import List, Dict, Any, Optional

# Language detection by extension
LANG_BY_EXT = {
    ".py": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".cs": "csharp",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hh": "cpp",
    ".hxx": "cpp",
    ".rb": "ruby",
    ".rake": "ruby",
    ".php": "php",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".swift": "swift",
}


def detect_language(filename: str, hint: Optional[str] = None) -> str:
    if hint:
        return hint.lower()
    _, ext = os.path.splitext(filename)
    return LANG_BY_EXT.get(ext.lower(), "text")


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _finding(rule_id: str, file: str, line: int, problem: str, suggestion: str,
             severity: str, confidence: float = 0.95, blocking: bool = False,
             suggested_code: Optional[str] = None) -> Dict[str, Any]:
    return {
        "rule_id": rule_id,
        "file": file,
        "line": line,
        "problem": problem,
        "suggestion": suggestion,
        "severity": severity,
        "confidence": confidence,
        "blocking": blocking,
        "suggested_code": suggested_code,
    }


def _collapse_findings(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collapse duplicate findings on the same (file, line) keeping highest severity."""
    by_key: Dict[str, Dict[str, Any]] = {}
    for f in findings:
        key = f"{f['file']}:{f['line']}:{f['rule_id']}"
        if key not in by_key:
            by_key[key] = f
        else:
            existing = by_key[key]
            if SEVERITY_ORDER.get(f["severity"], 99) < SEVERITY_ORDER.get(existing["severity"], 99):
                by_key[key] = f
            else:
                existing.setdefault("corroborated_by", [])
                if f["rule_id"] not in existing["corroborated_by"]:
                    existing["corroborated_by"].append(f["rule_id"])
    return sorted(by_key.values(), key=lambda f: (SEVERITY_ORDER.get(f["severity"], 99), f["line"]))


# -------------------- Agent 1: security (regex) --------------------

SECURITY_RULES = [
    ("SECU-101", r"\bapi_key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key detected",
     "Move the key to an environment variable or secret manager.", "critical", True,
     "api_key = os.getenv(\"API_KEY\")"),
    ("SECU-102", r"\bpassword\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password detected",
     "Use an environment variable or secrets vault instead of a literal password.", "critical", True,
     "password = os.getenv(\"DB_PASSWORD\")"),
    ("SECU-103", r"\bsecret\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret detected",
     "Store secrets in environment variables or a secrets manager.", "critical", True,
     "secret = os.getenv(\"APP_SECRET\")"),
    ("SECU-104", r"\btoken\s*=\s*['\"][^'\"]+['\"]", "Hardcoded token detected",
     "Use environment variables for authentication tokens.", "critical", True,
     "token = os.getenv(\"AUTH_TOKEN\")"),
    ("SECU-105", r"\beval\s*\(", "Use of eval() detected",
     "Avoid eval(); use ast.literal_eval() or a safe parser instead.", "high", True,
     "ast.literal_eval(user_input)"),
    ("SECU-106", r"\bexec\s*\(", "Use of exec() detected",
     "Avoid exec(); it executes arbitrary code and is a major injection risk.", "high", True,
     "Use a function dictionary or validated dispatch instead."),
    ("SECU-107", r"\bos\.system\s*\(", "Use of os.system() detected",
     "Use subprocess with a list of arguments instead of a shell string.", "high", True,
     "subprocess.run([\"cmd\", \"arg1\"], check=True)"),
    ("SECU-108", r"\bsubprocess\.(call|run|Popen)\([^)]*shell\s*=\s*True", "subprocess with shell=True",
     "Avoid shell=True; pass arguments as a list to prevent shell injection.", "high", True,
     "subprocess.run([\"cmd\", arg1], check=True)"),
    ("SECU-109", r"\b(SELECT|INSERT|UPDATE|DELETE).*\%s|f\".*SELECT|f\".*INSERT", "Possible SQL injection via string formatting",
     "Use parameterized queries instead of string interpolation.", "high", True,
     "cursor.execute(\"SELECT * FROM users WHERE id = %s\", (user_id,))"),
    ("SECU-110", r"\b\.innerHTML\s*=", "Direct innerHTML assignment",
     "Use textContent or sanitize HTML to prevent XSS.", "medium", False,
     "element.textContent = userInput"),
    ("SECU-111", r"\bdocument\.write\s*\(", "Use of document.write()",
     "Avoid document.write(); it can enable XSS and blocks parsing.", "medium", False,
     "Use DOM methods like appendChild or insertAdjacentHTML."),
    ("SECU-112", r"\bpickle\.(loads|load)\(", "Use of pickle.load/loads",
     "Pickle can execute arbitrary code; use JSON or a safe serializer.", "high", True,
     "json.loads(data)"),
    ("SECU-113", r"\byaml\.(load|safe_load)\(", "Use of yaml.load()",
     "Use yaml.safe_load() to avoid arbitrary object instantiation.", "medium", False,
     "yaml.safe_load(data)"),
    ("SECU-114", r"\bmd5\s*\(", "Use of MD5 hash",
     "MD5 is cryptographically broken; use SHA-256 or stronger.", "medium", False,
     "hashlib.sha256(data).hexdigest()"),
    ("SECU-115", r"\bsha1\s*\(", "Use of SHA-1 hash",
     "SHA-1 is deprecated; use SHA-256 or stronger.", "medium", False,
     "hashlib.sha256(data).hexdigest()"),
]


def agent_security(filename: str, content: str, language: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    lines = content.splitlines()
    for rule_id, pattern, problem, suggestion, severity, blocking, suggested_code in SECURITY_RULES:
        for i, line in enumerate(lines, start=1):
            if re.search(pattern, line, re.IGNORECASE):
                findings.append(_finding(
                    rule_id, filename, i, problem, suggestion, severity,
                    blocking=blocking, suggested_code=suggested_code,
                ))
    return findings


# -------------------- Agent 2: quality (regex) --------------------

QUALITY_RULES = [
    ("QUAL-104", r"\b(TODO|FIXME|HACK)\b", "TODO/FIXME/HACK marker found",
     "Resolve or track this marker in an issue tracker.", "low", False, None),
    ("QUAL-105", r".{121,}", "Line exceeds 120 characters",
     "Wrap long lines for readability.", "low", False, None),
    ("QUAL-106", r"\b(\w+)\1\1", "Possible duplicated code block",
     "Extract repeated logic into a shared function.", "medium", False, None),
]


def agent_quality(filename: str, content: str, language: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    lines = content.splitlines()

    # Function length check (rough: count lines in function body)
    if language == "python":
        func_start = None
        func_indent = 0
        for i, line in enumerate(lines, start=1):
            m = re.match(r"(\s*)def\s+(\w+)\s*\([^)]*:", line)
            if m and func_start is None:
                func_start = i
                func_indent = len(m.group(1))
                func_name = m.group(2)
            elif func_start is not None:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    cur_indent = len(line) - len(line.lstrip())
                    if cur_indent <= func_indent:
                        # Function ended
                        length = i - func_start
                        if length > 50:
                            findings.append(_finding(
                                "QUAL-102", filename, func_start,
                                f"Function '{func_name}' is {length} lines long (max 50).",
                                "Break the function into smaller, focused functions.",
                                "medium", False,
                            ))
                        func_start = None

    # TODO/FIXME markers and long lines
    for rule_id, pattern, problem, suggestion, severity, blocking, _ in QUALITY_RULES:
        if rule_id == "QUAL-101":
            continue
        for i, line in enumerate(lines, start=1):
            if re.search(pattern, line):
                findings.append(_finding(
                    rule_id, filename, i, problem, suggestion, severity,
                    blocking=blocking,
                ))

    return findings


# -------------------- Agent 3: policy (regex) --------------------

POLICY_RULES = [
    ("POL-102", r"\bconsole\.log\s*\(", "console.log found in source",
     "Remove debug console.log statements before committing.", "low", False, None),
    ("POL-103", r"\bprint\s*\(", "print() found outside CLI entry point",
     "Use a logging framework instead of print() in library code.", "low", False, None),
    ("POL-104", r"\bTODO\([^)]+\)", "TODO without issue reference",
     "Reference an issue tracker ID in TODO comments (TODO(PROJ-123)).", "low", False, None),
]


def agent_policy(filename: str, content: str, language: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    lines = content.splitlines()

    for rule_id, pattern, problem, suggestion, severity, blocking, _ in POLICY_RULES:
        for i, line in enumerate(lines, start=1):
            if re.search(pattern, line):
                findings.append(_finding(
                    rule_id, filename, i, problem, suggestion, severity,
                    blocking=blocking,
                ))

    # Check for missing license header (first 10 lines)
    header = "\n".join(lines[:10])
    if not re.search(r"(SPDX|License|Copyright)", header, re.IGNORECASE):
        findings.append(_finding(
            "POL-101", filename, 1,
            "No SPDX license or copyright header found.",
            "Add a license header (e.g. SPDX-License-Identifier: MIT).",
            "low", confidence=0.9, blocking=False,
        ))

    return findings


# -------------------- Agent 4: test (regex) --------------------

TEST_RULES = [
    ("TST-101", r"\bassert\s+True\b|\bassert\s+False\b", "Weak assertion (assert True/False)",
     "Assert specific behavior instead of True/False.", "medium", False, None),
    ("TST-104", r"\b\.skip\b|\b@pytest\.skip\b", "Skipped test detected",
     "Review or re-enable skipped tests.", "medium", False, None),
]


def agent_test(filename: str, content: str, language: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    lines = content.splitlines()

    for rule_id, pattern, problem, suggestion, severity, blocking, _ in TEST_RULES:
        for i, line in enumerate(lines, start=1):
            if re.search(pattern, line):
                findings.append(_finding(
                    rule_id, filename, i, problem, suggestion, severity,
                    blocking=blocking,
                ))

    # Check if test file has any assertions
    is_test = "test" in filename.lower() or filename.lower().startswith("test_")
    if is_test and language == "python":
        has_assert = any(re.search(r"\bassert\s+", line) for line in lines)
        if not has_assert:
            findings.append(_finding(
                "TST-105", filename, 1,
                "Test file contains no assertions.",
                "Add assertions to verify expected behavior.", "high", False,
            ))

    return findings


# -------------------- Orchestrator --------------------

AGENTS = {
    "security": agent_security,
    "quality": agent_quality,
    "policy": agent_policy,
    "test": agent_test,
}


def review_text(filename: str, content: str, language: Optional[str] = None) -> List[Dict[str, Any]]:
    """Run all regex agents on a single file's text. Returns collapsed findings."""
    if language is None:
        language = detect_language(filename)
    all_findings: List[Dict[str, Any]] = []
    for name, fn in AGENTS.items():
        try:
            all_findings.extend(fn(filename, content, language))
        except Exception:
            pass
    return _collapse_findings(all_findings)
