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


def _issue(rule_id, severity, category, message, suggestion, filename, position):
    return {
        "agent": "accessibility",
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
