"""PRISM scoring: convert findings into a 0-100 code quality/security score."""

SEVERITY_WEIGHT = {
    "critical": 25,
    "high": 15,
    "medium": 7,
    "low": 2,
    "info": 0,
}


def score_findings(findings: list) -> dict:
    """Return a score dict from a list of findings.

    Score starts at 100 and is reduced by severity weights.
    Blocking findings (critical/high) weigh more.
    """
    score = 100
    breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

    for f in findings:
        sev = f.get("severity", "low")
        weight = SEVERITY_WEIGHT.get(sev, 2)
        penalty = weight
        if f.get("blocking"):
            penalty = weight * 2  # blocking findings count double
        score -= penalty
        breakdown[sev] = breakdown.get(sev, 0) + 1

    score = max(0, min(100, score))

    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    elif score >= 60:
        grade = "D"
    else:
        grade = "F"

    return {
        "score": score,
        "grade": grade,
        "breakdown": breakdown,
        "total_findings": len(findings),
        "blocking_count": sum(1 for f in findings if f.get("blocking")),
    }
