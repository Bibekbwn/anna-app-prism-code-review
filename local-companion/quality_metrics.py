import re
from html import unescape

SEVERITY_PENALTIES = {
    "critical": 35,
    "high": 22,
    "medium": 12,
    "low": 5,
    "info": 1,
}
WEB_LANGUAGE = "JavaScript / TypeScript"

# Language-specific accessibility check levels
# "full" = all checks (JS/TS), "basic" = core checks only (all other languages)
LANGUAGE_ACCESSIBILITY_LEVEL = {
    "Python": "basic",
    "JavaScript / TypeScript": "full",
    "Go": "basic",
    "Rust": "basic",
    "Java": "basic",
    "C#": "basic",
    "C": "basic",
    "C++": "basic",
    "Ruby": "basic",
    "PHP": "basic",
    "Kotlin": "basic",
    "Swift": "basic",
}


def _line_number(source, position):
    return source.count("\n", 0, position) + 1


def _issue(rule_id, severity, category, message, suggestion, filename, position, agent="accessibility"):
    return {
        "agent": agent,
        "severity": severity,
        "category": category,
        "problem": message,
        "file": filename,
        "line": _line_number(position[0], position[1]),
        "suggestion": suggestion,
        "suggested_code": None,
        "confidence": 0.95,
        "rule_id": rule_id,
        "corroborated_by": [],
        "blocking": False,
    }


def _image_issues(source, filename):
    findings = []
    for match in re.finditer(r"<img\b([^>]*)>", source, re.I | re.S):
        if not re.search(r"\balt\s*=", match.group(1), re.I):
            findings.append(_issue(
                "A11Y-IMG-ALT", "high", "Image alternative text",
                "Image is missing an alt attribute.",
                "Add concise alt text, or use alt=\"\" when the image is decorative.",
                filename, (source, match.start()),
            ))
    return findings


def _inside_label(source, position):
    prefix = source[:position].lower()
    return prefix.rfind("<label") > prefix.rfind("</label>")


def _control_has_label(source, match):
    attributes = match.group(2)
    if re.search(r"\baria-(?:label|labelledby)\s*=|\btitle\s*=", attributes, re.I):
        return True

    element_id = re.search(r"\bid\s*=\s*([\"'])(.*?)\1", attributes, re.I)
    if element_id:
        escaped_id = re.escape(element_id.group(2))
        label_for = re.compile(
            r"<label\b[^>]*\b(?:for|htmlFor)\s*=\s*([\"'])" + escaped_id + r"\1",
            re.I,
        )
        if label_for.search(source):
            return True
    return _inside_label(source, match.start())


def _form_issues(source, filename):
    findings = []
    pattern = re.compile(r"<(input|select|textarea)\b([^>]*)>", re.I | re.S)
    for match in pattern.finditer(source):
        if not _control_has_label(source, match):
            findings.append(_issue(
                "A11Y-FORM-LABEL", "high", "Form labels",
                "Form control has no programmatic label.",
                "Associate a visible label or add aria-label/aria-labelledby.",
                filename, (source, match.start()),
            ))
    return findings


def _button_name_issues(source, filename):
    findings = []
    pattern = re.compile(r"<button\b([^>]*)>(.*?)</button\s*>", re.I | re.S)
    for match in pattern.finditer(source):
        attributes, content = match.group(1), match.group(2)
        has_explicit_name = re.search(
            r"\b(?:aria-label|aria-labelledby|title)\s*=", attributes, re.I
        )
        content = re.sub(r"<title\b[^>]*>(.*?)</title>", r"\1", content, flags=re.I | re.S)
        visible_text = unescape(re.sub(r"<[^>]*>", "", content)).strip()
        if not has_explicit_name and not visible_text:
            findings.append(_issue(
                "A11Y-BUTTON-NAME", "high", "Accessible names",
                "Button has no discernible accessible name.",
                "Add visible text or an aria-label that describes the action.",
                filename, (source, match.start()),
            ))
    return findings


def _keyboard_issues(source, filename):
    findings = []
    pattern = re.compile(r"<(div|span|li)\b([^>]*)\bonClick\s*=", re.I | re.S)
    for match in pattern.finditer(source):
        attributes = match.group(2)
        has_button_role = re.search(r"\brole\s*=\s*([\"'])button\1", attributes, re.I)
        has_tab_stop = re.search(r"\btabIndex\s*=\s*\{?0", attributes, re.I)
        has_keyboard_handler = re.search(r"\bonKey(?:Down|Up|Press)\s*=", attributes, re.I)
        if not (has_button_role and has_tab_stop and has_keyboard_handler):
            findings.append(_issue(
                "A11Y-KEYBOARD", "high", "Keyboard operation",
                "Clickable non-interactive element may not be keyboard accessible.",
                "Use a native button/link, or provide button semantics, tabIndex=0, and a keyboard handler.",
                filename, (source, match.start()),
            ))
    return findings


def accessibility_findings(source, filename, language):
    """Check common HTML/JSX accessibility contracts without executing code."""
    language_level = LANGUAGE_ACCESSIBILITY_LEVEL.get(language, "basic")
    
    if language_level == "basic":
        # Core checks for all languages: image alt text + button names
        return (
            _image_issues(source, filename)
            + _button_name_issues(source, filename)
        )
    else:
        # Full checks for JavaScript/TypeScript: all accessibility checks
        return (
            _image_issues(source, filename)
            + _form_issues(source, filename)
            + _button_name_issues(source, filename)
            + _keyboard_issues(source, filename)
        )


# Language-specific security check patterns
# Each pattern: (rule_id, severity, category, message, suggestion, regex)
SECURITY_PATTERNS = {
    "Swift": [
        (
            "SWIFT-SEC-HARDCODED_SECRET",
            "high",
            "Hardcoded secrets",
            "Possible hardcoded secret or credential detected.",
            "Use Keychain or secure environment variables instead of hardcoding secrets.",
            r"""(?i)(password|passwd|pwd|secret|api[_-]?key|token|auth[_-]?token|private[_-]?key|access[_-]?token)\s*[:=]\s*["'][^"']{4,}["']""",
        ),
        (
            "SWIFT-SEC-INSECURE-HTTP",
            "high",
            "Insecure network connection",
            "Insecure HTTP URL detected; use HTTPS instead.",
            "Use https:// URLs and enable App Transport Security (ATS).",
            r"""(?i)https?://[^\s"'<>]+""",
        ),
        (
            "SWIFT-SEC-FORCE_UNWRAP",
            "medium",
            "Force unwrap optional",
            "Force-unwrapping an optional with ! may crash at runtime if nil.",
            "Use optional binding (if let / guard let) or nil coalescing (??) instead of !.",
            r"!\s*[\.;,\)\}]",
        ),
        (
            "SWIFT-SEC-FORCE_TRY",
            "medium",
            "Force try",
            "Force-try (try!) may crash if an error is thrown.",
            "Use do/catch or try? to handle errors gracefully.",
            r"\btry!",
        ),
        (
            "SWIFT-SEC-WEAK_CRYPTO",
            "medium",
            "Weak cryptographic algorithm",
            "Weak or deprecated cryptographic hash detected (MD5/SHA1).",
            "Use SHA-256 or stronger via CryptoKit (e.g., SHA256.hash(data:)).",
            r"""(?i)\b(MD5|SHA1|SHA-1|CC_MD5|CC_SHA1)\b""",
        ),
        (
            "SWIFT-SEC-INSECURE_RANDOM",
            "medium",
            "Insecure random number generation",
            "arc4random_uniform is not cryptographically secure.",
            "Use SecureRandom or CryptoKit for security-sensitive randomness.",
            r"\barc4random_uniform\b",
        ),
        (
            "SWIFT-SEC-KEYCHAIN_ALWAYS",
            "high",
            "Insecure keychain accessibility",
            "kSecAttrAccessibleAlways allows keychain access even when locked.",
            "Use kSecAttrAccessibleWhenUnlocked or kSecAttrAccessibleAfterFirstUnlock.",
            r"\bkSecAttrAccessibleAlways\b",
        ),
        (
            "SWIFT-SEC-ATS_BYPASS",
            "medium",
            "App Transport Security bypass",
            "NSAllowsArbitraryLoads disables ATS, permitting insecure connections.",
            "Keep ATS enabled; use NSExceptionDomains for specific domains if needed.",
            r"\bNSAllowsArbitraryLoads\b",
        ),
    ],
    "JavaScript / TypeScript": [
        (
            "JS-SEC-HARDCODED_SECRET",
            "high",
            "Hardcoded secrets",
            "Possible hardcoded secret or credential detected.",
            "Use environment variables or secret management instead of hardcoding secrets.",
            r"""(?i)(password|passwd|pwd|secret|api[_-]?key|token|auth[_-]?token|private[_-]?key|access[_-]?token)\s*[:=]\s*["'][^"']{4,}["']""",
        ),
        (
            "JS-SEC-INSECURE-HTTP",
            "high",
            "Insecure network connection",
            "Insecure HTTP URL detected; use HTTPS instead.",
            "Use https:// URLs for all network requests.",
            r"""(?i)https?://[^\s"'<>]+""",
        ),
        (
            "JS-SEC-EVAL",
            "high",
            "Dangerous eval usage",
            "eval() or similar function executes arbitrary code.",
            "Avoid eval(); use JSON.parse() or safer alternatives.",
            r"\b(eval|setTimeout|setInterval|Function)\s*\(\s*[\"']",
        ),
        (
            "JS-SEC-INNER_HTML",
            "medium",
            "Potential XSS via innerHTML",
            "innerHTML can introduce cross-site scripting vulnerabilities.",
            "Use textContent or DOM methods instead of innerHTML with untrusted data.",
            r"\.innerHTML\s*=",
        ),
        (
            "JS-SEC-WEAK_CRYPTO",
            "medium",
            "Weak cryptographic algorithm",
            "Weak or deprecated cryptographic hash detected (MD5/SHA1).",
            "Use SHA-256 or stronger via Node.js crypto module.",
            r"""(?i)\b(MD5|SHA1|SHA-1)\b""",
        ),
        (
            "JS-SEC-INSECURE_RANDOM",
            "medium",
            "Insecure random number generation",
            "Math.random() is not cryptographically secure.",
            "Use crypto.randomBytes() or crypto.getRandomValues() for security-sensitive randomness.",
            r"\bMath\.random\(\)",
        ),
    ],
    "Python": [
        (
            "PY-SEC-HARDCODED_SECRET",
            "high",
            "Hardcoded secrets",
            "Possible hardcoded secret or credential detected.",
            "Use environment variables or secret management instead of hardcoding secrets.",
            r"""(?i)(password|passwd|pwd|secret|api[_-]?key|token|auth[_-]?token|private[_-]?key|access[_-]?token)\s*[:=]\s*["'][^"']{4,}["']""",
        ),
        (
            "PY-SEC-INSECURE-HTTP",
            "high",
            "Insecure network connection",
            "Insecure HTTP URL detected; use HTTPS instead.",
            "Use https:// URLs for all network requests.",
            r"""(?i)https?://[^\s"'<>]+""",
        ),
        (
            "PY-SEC-EVAL_EXEC",
            "high",
            "Dangerous eval/exec usage",
            "eval() or exec() executes arbitrary code.",
            "Avoid eval() and exec(); use ast.literal_eval() or safer alternatives.",
            r"\b(eval|exec)\s*\(",
        ),
        (
            "PY-SEC-PICKLE",
            "medium",
            "Unsafe deserialization with pickle",
            "pickle.loads() can execute arbitrary code during deserialization.",
            "Use json or other safe serialization formats for untrusted data.",
            r"\bpickle\.(loads|load)\s*\(",
        ),
        (
            "PY-SEC-WEAK_CRYPTO",
            "medium",
            "Weak cryptographic algorithm",
            "Weak or deprecated cryptographic hash detected (MD5/SHA1).",
            "Use hashlib.sha256() or stronger.",
            r"""(?i)\b(MD5|sha1|sha_1)\b""",
        ),
        (
            "PY-SEC-SUBPROCESS_SHELL",
            "medium",
            "Shell injection via subprocess",
            "subprocess with shell=True can lead to shell injection.",
            "Use subprocess with a list of arguments and shell=False.",
            r"\bsubprocess\.(run|call|Popen|check_output)\s*\([^)]*shell\s*=\s*True",
        ),
    ],
    "Java": [
        (
            "JAVA-SEC-HARDCODED_SECRET",
            "high",
            "Hardcoded secrets",
            "Possible hardcoded secret or credential detected.",
            "Use environment variables or secret management instead of hardcoding secrets.",
            r"""(?i)(password|passwd|pwd|secret|api[_-]?key|token|auth[_-]?token|private[_-]?key|access[_-]?token)\s*[:=]\s*["'][^"']{4,}["']""",
        ),
        (
            "JAVA-SEC-INSECURE-HTTP",
            "high",
            "Insecure network connection",
            "Insecure HTTP URL detected; use HTTPS instead.",
            "Use https:// URLs for all network requests.",
            r"""(?i)https?://[^\s"'<>]+""",
        ),
        (
            "JAVA-SEC-WEAK_CRYPTO",
            "medium",
            "Weak cryptographic algorithm",
            "Weak or deprecated cryptographic hash detected (MD5/SHA1/DES).",
            "Use SHA-256 or stronger via java.security.MessageDigest.",
            r"""(?i)\b(MD5|SHA1|SHA-1|DES)\b""",
        ),
        (
            "JAVA-SEC-RUNTIME_EXEC",
            "medium",
            "Runtime exec command injection",
            "Runtime.exec() can execute arbitrary commands.",
            "Validate and sanitize all input before passing to Runtime.exec().",
            r"\bRuntime\.getRuntime\(\)\.exec\s*\(",
        ),
    ],
    "C#": [
        (
            "CS-SEC-HARDCODED_SECRET",
            "high",
            "Hardcoded secrets",
            "Possible hardcoded secret or credential detected.",
            "Use environment variables or secret management instead of hardcoding secrets.",
            r"""(?i)(password|passwd|pwd|secret|api[_-]?key|token|auth[_-]?token|private[_-]?key|access[_-]?token)\s*[:=]\s*["'][^"']{4,}["']""",
        ),
        (
            "CS-SEC-INSECURE-HTTP",
            "high",
            "Insecure network connection",
            "Insecure HTTP URL detected; use HTTPS instead.",
            "Use https:// URLs for all network requests.",
            r"""(?i)https?://[^\s"'<>]+""",
        ),
        (
            "CS-SEC-WEAK_CRYPTO",
            "medium",
            "Weak cryptographic algorithm",
            "Weak or deprecated cryptographic hash detected (MD5/SHA1/DES).",
            "Use SHA256 or stronger via System.Security.Cryptography.",
            r"""(?i)\b(MD5|SHA1|SHA-1|DESCryptoServiceProvider)\b""",
        ),
        (
            "CS-SEC-EVAL",
            "medium",
            "Dynamic code execution",
            "Eval or dynamic compilation can execute arbitrary code.",
            "Avoid dynamic code execution with untrusted input.",
            r"\b(Eval|Compile|Execute)\s*\(",
        ),
    ],
    "Go": [
        (
            "GO-SEC-HARDCODED_SECRET",
            "high",
            "Hardcoded secrets",
            "Possible hardcoded secret or credential detected.",
            "Use environment variables or secret management instead of hardcoding secrets.",
            r"""(?i)(password|passwd|pwd|secret|api[_-]?key|token|auth[_-]?token|private[_-]?key|access[_-]?token)\s*[:=]\s*["'][^"']{4,}["']""",
        ),
        (
            "GO-SEC-INSECURE-HTTP",
            "high",
            "Insecure network connection",
            "Insecure HTTP URL detected; use HTTPS instead.",
            "Use https:// URLs for all network requests.",
            r"""(?i)https?://[^\s"'<>]+""",
        ),
        (
            "GO-SEC-WEAK_CRYPTO",
            "medium",
            "Weak cryptographic algorithm",
            "Weak or deprecated cryptographic hash detected (MD5/SHA1).",
            "Use crypto/sha256 or stronger.",
            r"""(?i)\b(MD5|sha1|sha1\.New)\b""",
        ),
        (
            "GO-SEC-EXEC_COMMAND",
            "medium",
            "Command injection via os/exec",
            "exec.Command with untrusted input can lead to command injection.",
            "Validate and sanitize all input before passing to exec.Command.",
            r"\bexec\.Command\s*\(",
        ),
    ],
    "Rust": [
        (
            "RUST-SEC-HARDCODED_SECRET",
            "high",
            "Hardcoded secrets",
            "Possible hardcoded secret or credential detected.",
            "Use environment variables or secret management instead of hardcoding secrets.",
            r"""(?i)(password|passwd|pwd|secret|api[_-]?key|token|auth[_-]?token|private[_-]?key|access[_-]?token)\s*[:=]\s*["'][^"']{4,}["']""",
        ),
        (
            "RUST-SEC-INSECURE-HTTP",
            "high",
            "Insecure network connection",
            "Insecure HTTP URL detected; use HTTPS instead.",
            "Use https:// URLs for all network requests.",
            r"""(?i)https?://[^\s"'<>]+""",
        ),
        (
            "RUST-SEC-UNSAFE_BLOCK",
            "medium",
            "Unsafe code block",
            "unsafe blocks bypass Rust's safety guarantees.",
            "Minimize unsafe code and audit it thoroughly.",
            r"\bunsafe\b",
        ),
        (
            "RUST-SEC-WEAK_CRYPTO",
            "medium",
            "Weak cryptographic algorithm",
            "Weak or deprecated cryptographic hash detected (MD5/SHA1).",
            "Use SHA-256 or stronger via sha2 crate.",
            r"""(?i)\b(MD5|Sha1|Sha-1)\b""",
        ),
    ],
    "C": [
        (
            "C-SEC-HARDCODED_SECRET",
            "high",
            "Hardcoded secrets",
            "Possible hardcoded secret or credential detected.",
            "Use environment variables or secret management instead of hardcoding secrets.",
            r"""(?i)(password|passwd|pwd|secret|api[_-]?key|token|auth[_-]?token|private[_-]?key|access[_-]?token)\s*[:=]\s*["'][^"']{4,}["']""",
        ),
        (
            "C-SEC-INSECURE-HTTP",
            "high",
            "Insecure network connection",
            "Insecure HTTP URL detected; use HTTPS instead.",
            "Use https:// URLs for all network requests.",
            r"""(?i)https?://[^\s"'<>]+""",
        ),
        (
            "C-SEC-BUFFER_OVERFLOW",
            "high",
            "Potential buffer overflow",
            "gets() or strcpy() can cause buffer overflow vulnerabilities.",
            "Use fgets() or strncpy() with bounds checking instead.",
            r"\b(gets|strcpy|sprintf)\s*\(",
        ),
        (
            "C-SEC-WEAK_CRYPTO",
            "medium",
            "Weak cryptographic algorithm",
            "Weak or deprecated cryptographic hash detected (MD5/SHA1).",
            "Use SHA-256 or stronger via OpenSSL.",
            r"""(?i)\b(MD5|SHA1|SHA-1)\b""",
        ),
    ],
    "C++": [
        (
            "CPP-SEC-HARDCODED_SECRET",
            "high",
            "Hardcoded secrets",
            "Possible hardcoded secret or credential detected.",
            "Use environment variables or secret management instead of hardcoding secrets.",
            r"""(?i)(password|passwd|pwd|secret|api[_-]?key|token|auth[_-]?token|private[_-]?key|access[_-]?token)\s*[:=]\s*["'][^"']{4,}["']""",
        ),
        (
            "CPP-SEC-INSECURE-HTTP",
            "high",
            "Insecure network connection",
            "Insecure HTTP URL detected; use HTTPS instead.",
            "Use https:// URLs for all network requests.",
            r"""(?i)https?://[^\s"'<>]+""",
        ),
        (
            "CPP-SEC-BUFFER_OVERFLOW",
            "high",
            "Potential buffer overflow",
            "gets() or strcpy() can cause buffer overflow vulnerabilities.",
            "Use std::string or bounded copy functions instead.",
            r"\b(gets|strcpy|sprintf)\s*\(",
        ),
        (
            "CPP-SEC-WEAK_CRYPTO",
            "medium",
            "Weak cryptographic algorithm",
            "Weak or deprecated cryptographic hash detected (MD5/SHA1).",
            "Use SHA-256 or stronger via OpenSSL or Crypto++.",
            r"""(?i)\b(MD5|SHA1|SHA-1)\b""",
        ),
    ],
    "Ruby": [
        (
            "RUBY-SEC-HARDCODED_SECRET",
            "high",
            "Hardcoded secrets",
            "Possible hardcoded secret or credential detected.",
            "Use environment variables or secret management instead of hardcoding secrets.",
            r"""(?i)(password|passwd|pwd|secret|api[_-]?key|token|auth[_-]?token|private[_-]?key|access[_-]?token)\s*[:=]\s*["'][^"']{4,}["']""",
        ),
        (
            "RUBY-SEC-INSECURE-HTTP",
            "high",
            "Insecure network connection",
            "Insecure HTTP URL detected; use HTTPS instead.",
            "Use https:// URLs for all network requests.",
            r"""(?i)https?://[^\s"'<>]+""",
        ),
        (
            "RUBY-SEC-EVAL",
            "high",
            "Dangerous eval usage",
            "eval() or instance_eval() executes arbitrary code.",
            "Avoid eval() with untrusted input.",
            r"\b(eval|instance_eval|class_eval)\s*\(",
        ),
        (
            "RUBY-SEC-WEAK_CRYPTO",
            "medium",
            "Weak cryptographic algorithm",
            "Weak or deprecated cryptographic hash detected (MD5/SHA1).",
            "Use SHA-256 or stronger via Digest::SHA256.",
            r"""(?i)\b(MD5|SHA1|SHA-1)\b""",
        ),
    ],
    "PHP": [
        (
            "PHP-SEC-HARDCODED_SECRET",
            "high",
            "Hardcoded secrets",
            "Possible hardcoded secret or credential detected.",
            "Use environment variables or secret management instead of hardcoding secrets.",
            r"""(?i)(password|passwd|pwd|secret|api[_-]?key|token|auth[_-]?token|private[_-]?key|access[_-]?token)\s*[:=]\s*["'][^"']{4,}["']""",
        ),
        (
            "PHP-SEC-INSECURE-HTTP",
            "high",
            "Insecure network connection",
            "Insecure HTTP URL detected; use HTTPS instead.",
            "Use https:// URLs for all network requests.",
            r"""(?i)https?://[^\s"'<>]+""",
        ),
        (
            "PHP-SEC-EVAL",
            "high",
            "Dangerous eval usage",
            "eval() executes arbitrary PHP code.",
            "Avoid eval() with untrusted input.",
            r"\beval\s*\(",
        ),
        (
            "PHP-SEC-WEAK_CRYPTO",
            "medium",
            "Weak cryptographic algorithm",
            "Weak or deprecated cryptographic hash detected (MD5/SHA1).",
            "Use hash('sha256', ...) or stronger.",
            r"""(?i)\b(md5|sha1)\b""",
        ),
    ],
    "Kotlin": [
        (
            "KOTLIN-SEC-HARDCODED_SECRET",
            "high",
            "Hardcoded secrets",
            "Possible hardcoded secret or credential detected.",
            "Use environment variables or secret management instead of hardcoding secrets.",
            r"""(?i)(password|passwd|pwd|secret|api[_-]?key|token|auth[_-]?token|private[_-]?key|access[_-]?token)\s*[:=]\s*["'][^"']{4,}["']""",
        ),
        (
            "KOTLIN-SEC-INSECURE-HTTP",
            "high",
            "Insecure network connection",
            "Insecure HTTP URL detected; use HTTPS instead.",
            "Use https:// URLs for all network requests.",
            r"""(?i)https?://[^\s"'<>]+""",
        ),
        (
            "KOTLIN-SEC-WEAK_CRYPTO",
            "medium",
            "Weak cryptographic algorithm",
            "Weak or deprecated cryptographic hash detected (MD5/SHA1).",
            "Use SHA-256 or stronger via java.security.MessageDigest.",
            r"""(?i)\b(MD5|SHA1|SHA-1)\b""",
        ),
    ],
}


def _security_pattern_findings(source, filename, language, agent="security"):
    """Run regex-based security pattern checks for the given language."""
    patterns = SECURITY_PATTERNS.get(language, [])
    findings = []
    for rule_id, severity, category, message, suggestion, regex in patterns:
        for match in re.finditer(regex, source):
            findings.append(
                _issue(
                    rule_id,
                    severity,
                    category,
                    message,
                    suggestion,
                    filename,
                    (source, match.start()),
                    agent=agent,
                )
            )
    return findings


def security_findings(source, filename, language):
    """Check for common security anti-patterns in source code."""
    return _security_pattern_findings(source, filename, language)


def _score(findings, assessed, method):
    if not assessed:
        return {"score": None, "assessed": False, "findings": 0, "method": "Not assessed"}

    penalty = 0.0
    for finding in findings:
        severity = str(finding.get("severity", "low")).lower()
        try:
            confidence = min(1.0, max(0.0, float(finding.get("confidence", 1.0))))
        except (TypeError, ValueError):
            confidence = 1.0
        penalty += SEVERITY_PENALTIES.get(severity, 0) * confidence

    return {
        "score": max(0, round(100 - penalty)),
        "assessed": True,
        "findings": len(findings),
        "method": method,
    }


def category_scores(findings, agents_run, language, ai_used):
    """Score only categories covered by the checks that actually ran."""
    agents = set(agents_run)
    security_agents = {"security", "ai_security", "sca"}
    quality_agents = {"quality", "ai_quality", "ai_architecture", "policy", "ai_policy"}
    testing_agents = {"test", "ai_test"}

    def matching(agent_names, predicate=None):
        return [
            finding for finding in findings
            if finding.get("agent") in agent_names and (predicate is None or predicate(finding))
        ]

    security = matching(security_agents)
    quality = matching(quality_agents)
    testing = matching(testing_agents)
    efficiency = matching(
        {"ai_performance", "quality"},
        lambda finding: finding.get("agent") == "ai_performance"
        or str(finding.get("category", "")).lower() in {"complexity", "file length", "performance"},
    )
    accessibility = matching({"accessibility"})
    efficiency_agents_ran = "quality" in agents or (ai_used and "ai_performance" in agents)

    return {
        "security": _score(security, bool(agents & security_agents), "PRISM security agents"),
        "quality": _score(quality, bool(agents & quality_agents), "PRISM quality and architecture agents"),
        "efficiency": _score(
            efficiency,
            efficiency_agents_ran,
            "Complexity checks + AI performance" if ai_used else "PRISM complexity checks",
        ),
        "testing": _score(testing, bool(agents & testing_agents), "Static test-pattern agents; tests are not executed"),
        "accessibility": _score(
            accessibility,
            language == WEB_LANGUAGE,
            "Static HTML/JSX accessibility checks",
        ),
    }
