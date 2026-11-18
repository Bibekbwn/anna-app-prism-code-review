"""Loopback-only web adapter for the existing PRISM CLI review engine."""

import argparse
import importlib.util
import json
import logging
import os
import re
import tempfile
import threading
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

APP_DIR = Path(__file__).resolve().parent
os.chdir(APP_DIR)

try:
    import prism
    from prism import token_usage
    from prism.ai_providers import PROVIDERS, PROVIDER_ALIASES, _is_placeholder_key
    from prism.agents import Blocker, Finding, Severity
    from prism.cli_config import load_config
    from prism.cli_review import json_output, review_file
    from prism.commands_common import _finding_to_dict
    from prism.reports import (
        REPORTS_DIR,
        clear_reports,
        delete_report,
        get_recent_reports,
        load_report,
        save_report,
    )
except ImportError as error:
    raise SystemExit(
        "PRISM is not installed in this Python environment. "
        "Install local-companion/requirements.txt, then restart the companion."
    ) from error

from quality_metrics import accessibility_findings, category_scores
from web_security import allowed_origin, is_loopback_host, normalize_origin

LOGGER = logging.getLogger("prism.local_companion")
MAX_CODE_CHARS = 40_000
MAX_BODY_BYTES = 180_000
MAX_HISTORY = 50
REVIEW_LOCK = threading.Lock()
SETTINGS_FILE = APP_DIR / ".prism-web.json"
DEFAULT_SETTINGS = {
    "effort": "Balanced",
    "theme": "Dark",
    "showSuggestions": True,
    "templates": [],
}
# Default efforts/themes can be overridden via environment variables
# Format: comma-separated list, e.g., PRISM_VALID_EFFORTS="Lite,Balanced,Max"
_VALID_EFFORTS_ENV = os.environ.get("PRISM_VALID_EFFORTS", "")
VALID_EFFORTS = set(
    [s.strip() for s in _VALID_EFFORTS_ENV.split(",") if s.strip()]
    or {"Lite", "Balanced", "Max"}
)

_VALID_THEMES_ENV = os.environ.get("PRISM_VALID_THEMES", "")
VALID_THEMES = set(
    [s.strip() for s in _VALID_THEMES_ENV.split(",") if s.strip()]
    or {"Dark", "Light"}
)
LANGUAGE_EXTENSIONS = {
    "Python": ".py",
    "JavaScript / TypeScript": ".ts",
    "Go": ".go",
    "Rust": ".rs",
    "Java": ".java",
    "C#": ".cs",
    "C": ".c",
    "C++": ".cpp",
    "Ruby": ".rb",
    "PHP": ".php",
    "Kotlin": ".kt",
    "Swift": ".swift",
}
EXTENSION_LANGUAGES = {extension: language for language, extension in LANGUAGE_EXTENSIONS.items()}
DEFAULT_ORIGINS = {
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://website-ui-to-code.v0.build",
    "https://anna.partners",
}
ALLOWED_ORIGINS = {
    normalized
    for origin in DEFAULT_ORIGINS | {
        value.strip() for value in os.environ.get("PRISM_WEB_ORIGINS", "").split(",") if value.strip()
    }
    if (normalized := normalize_origin(origin)) is not None
}


def _settings():
    if not SETTINGS_FILE.exists():
        return dict(DEFAULT_SETTINGS)
    try:
        saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_SETTINGS)
    if not isinstance(saved, dict):
        return dict(DEFAULT_SETTINGS)
    settings = dict(DEFAULT_SETTINGS)
    settings.update(saved)
    effort = settings.get("effort")
    theme = settings.get("theme")
    settings["effort"] = effort if isinstance(effort, str) and effort in VALID_EFFORTS else "Balanced"
    settings["theme"] = theme if isinstance(theme, str) and theme in VALID_THEMES else "Dark"
    settings["showSuggestions"] = bool(settings["showSuggestions"])
    templates = settings.get("templates")
    settings["templates"] = [
        item for item in templates
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and isinstance(item.get("name"), str)
        and isinstance(item.get("description"), str)
        and isinstance(item.get("code"), str)
    ] if isinstance(templates, list) else []
    return settings


def _write_settings(settings):
    temporary = SETTINGS_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    temporary.replace(SETTINGS_FILE)


def _provider_status():
    provider = (os.environ.get("MODEL_PROVIDER") or "gemini").strip().lower()
    provider = PROVIDER_ALIASES.get(provider, provider)
    spec = PROVIDERS.get(provider)
    if spec is None:
        return {"configured": False, "provider": provider, "reason": "unknown_provider"}
    key = os.environ.get(spec["key"], "")
    configured = bool(key and not _is_placeholder_key(key))
    module_name = {
        "gemini": "google.generativeai",
        "claude": "anthropic",
        "openai": "openai",
    }.get(spec["kind"])
    try:
        sdk_installed = bool(module_name and importlib.util.find_spec(module_name))
    except (ImportError, ModuleNotFoundError, ValueError):
        sdk_installed = False
    reason = None
    if not configured:
        reason = "no_key"
    elif not sdk_installed:
        reason = "no_sdk"
    return {
        "configured": configured and sdk_installed,
        "keyConfigured": configured,
        "sdkInstalled": sdk_installed,
        "provider": provider,
        "reason": reason,
    }


def _safe_filename(language):
    return "snippet" + LANGUAGE_EXTENSIONS.get(language, ".py")


def _detect_language(code):
    text = code[:12000]
    if "<?php" in text or re.search(r"\$[A-Za-z_]\w*\s*=", text):
        return "PHP"
    if "#include" in text:
        return "C++" if any(token in text for token in ("std::", "iostream", "namespace ")) else "C"
    if re.search(r"\bpackage\s+\w+", text) and re.search(r"\bfunc\s+\w+", text):
        return "Go"
    if re.search(r"\bfn\s+\w+", text) or "use std::" in text:
        return "Rust"
    if "import Foundation" in text or re.search(r"\bguard\s+\w+", text):
        return "Swift"
    if re.search(r"\bfun\s+\w+", text) or re.search(r"\bval\s+\w+\s*=", text):
        return "Kotlin"
    if re.search(r"\busing\s+System\b", text) or "namespace " in text:
        return "C#"
    if re.search(r"\bpublic\s+static\s+void\s+main\b", text) or "System.out.println" in text:
        return "Java"
    if re.search(r"\binterface\s+\w+\s*\{", text) or re.search(r"\btype\s+\w+\s*=\s*\{", text):
        return "JavaScript / TypeScript"
    if re.search(r"\b(def|elif|lambda)\b", text) or "import os" in text:
        return "Python"
    if re.search(r"\b(const|let|function|export)\b", text) or "=>" in text:
        return "JavaScript / TypeScript"
    if re.search(r"\bclass\s+\w+", text):
        return "Java"
    return "Python"


def _normalize_finding(item, index, filename):
    severity = str(item.get("severity") or "low").lower()
    severity_title = severity.capitalize() if severity in {"critical", "high", "medium", "low", "info"} else "Low"
    return {
        "id": str(item.get("rule_id") or "PRISM-{:03d}".format(index + 1))[:80],
        "severity": severity_title,
        "title": str(item.get("category") or item.get("rule_id") or "Code finding")[:140],
        "message": str(item.get("problem") or "").strip()[:2000],
        "recommendation": str(item.get("suggestion") or "Review this code path and verify the behavior.").strip()[:2000],
        "suggestedFix": str(item.get("suggested_code") or "").strip()[:6000] or None,
        "file": filename,
        "line": item.get("line") if isinstance(item.get("line"), int) and item.get("line") > 0 else None,
        "agent": str(item.get("agent") or "unknown")[:80],
        "confidence": float(item.get("confidence") or 0),
        "ruleId": item.get("rule_id"),
        "corroboratedBy": list(item.get("corroborated_by") or []),
        "blocking": bool(item.get("blocking")),
    }


def _report_filename(report):
    files = report.get("files_reviewed") or ["snippet.py"]
    return Path(files[0]).name


def _web_findings(report, filename):
    findings = []
    for index, item in enumerate(report.get("findings") or []):
        if not isinstance(item, dict):
            continue
        source_name = Path(item.get("file") or filename).name
        findings.append(_normalize_finding(item, index, source_name))
    return findings


def _report_summary(context, total, blocking):
    summary = context.get("summary")
    if summary:
        return summary
    if total == 0:
        return "PRISM found no actionable issues."
    return "PRISM found {} issue(s), including {} blocking.".format(total, blocking)


def _to_web_report(report):
    context = report.get("web_context") or {}
    filename = _report_filename(report)
    findings = _web_findings(report, filename)
    blocking = int(report.get("blocking") or 0)
    language = context.get("language") or EXTENSION_LANGUAGES.get(Path(filename).suffix, "Unknown")
    report_id = str(report.get("id") or "")
    report_date = report.get("timestamp") or ""
    effort = context.get("effort") or "Balanced"
    summary = _report_summary(context, len(findings), blocking)
    web_report = {
        "id": report_id,
        "date": report_date,
        "effort": effort,
        "fileName": filename,
        "summary": summary,
        "language": language,
        "findings": findings,
        "riskScore": float(report.get("risk_score") or 0),
        "blocking": blocking,
        "commitAllowed": bool(report.get("commit_allowed", True)),
        "qualityGatesPassed": bool(context.get("qualityGatesPassed", report.get("commit_allowed", True))),
        "tokenUsage": report.get("token_usage") or {},
        "categoryScores": context.get("categoryScores") or {},
        "testsRun": False,
    }
    return {
        "id": report_id,
        "date": report_date,
        "language": language,
        "effort": effort,
        "fileName": filename,
        "report": web_report,
    }


def _all_recent_reports():
    entries = get_recent_reports(MAX_HISTORY)
    result = []
    for entry in reversed(entries):
        report = load_report(str(entry.get("id", "")))
        if report:
            result.append(_to_web_report(report))
    return result


def _validate_review_request(payload):
    code = payload.get("code")
    if not isinstance(code, str) or not code.strip():
        raise ValueError("Paste code before starting a review.")
    if len(code) > MAX_CODE_CHARS:
        raise ValueError("Code must be 40,000 characters or fewer.")
    if "\x00" in code:
        raise ValueError("Binary content cannot be reviewed as source code.")

    requested_language = str(payload.get("language") or "Auto-detect")
    language = _detect_language(code) if requested_language == "Auto-detect" else requested_language
    if language not in LANGUAGE_EXTENSIONS:
        raise ValueError("Choose one of PRISM’s supported languages.")
    effort = str(payload.get("effort") or _settings()["effort"]).capitalize()
    if effort not in VALID_EFFORTS:
        raise ValueError("Effort must be Lite, Balanced, or Max.")
    return code, language, effort, _safe_filename(language)


def _serialize_cli_findings(results, raw_findings, filename, code):
    raw_by_key = {}
    for result in results:
        for finding in result.findings:
            raw_by_key[(finding.agent, finding.rule_id, finding.line)] = finding

    serialized = []
    for item in raw_findings:
        key = (item.get("agent"), item.get("rule_id"), item.get("line"))
        finding = raw_by_key.get(key)
        if finding is None:
            normalized = dict(item)
        else:
            normalized = _finding_to_dict(finding, code)
            normalized["blocking"] = item.get("blocking", False)
        normalized["file"] = filename
        serialized.append(normalized)
    return serialized


def _run_engine_review(code, language, effort, filename):
    token_usage.reset()
    config = load_config()
    with tempfile.TemporaryDirectory(prefix=".prism-web-") as temporary_directory:
        source_file = Path(temporary_directory) / filename
        source_file.write_text(code, encoding="utf-8")
        results, risk_score = review_file(
            str(source_file), config, effort=effort.lower(), fast=effort == "Lite"
        )
        output = json_output(results, config, {str(source_file): risk_score}, str(source_file))

    findings = _serialize_cli_findings(results, output.get("findings", []), filename, code)
    findings.extend(accessibility_findings(code, filename, language))
    agents_run = [result.agent_name for result in results]
    return output, findings, risk_score, agents_run


def _store_web_context(report_id, language, effort, summary, quality_gates_passed, score_breakdown):
    report = load_report(report_id) or {}
    report["web_context"] = {
        "language": language,
        "effort": effort,
        "summary": summary,
        "qualityGatesPassed": quality_gates_passed,
        "categoryScores": score_breakdown,
    }
    report_file = Path(REPORTS_DIR) / (report_id + ".json")
    temporary_report = report_file.with_suffix(".tmp")
    temporary_report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    temporary_report.replace(report_file)
    return _to_web_report(report)


def _ai_failure(effort, usage):
    if effort == "Lite" or usage.get("calls"):
        return None
    try:
        from prism.ai_providers import last_model_failure
        reason, provider, _detail = last_model_failure()
    except Exception:
        return {"reason": "unavailable"}
    return {"reason": reason, "provider": provider} if reason else None


def _build_review(payload):
    code, language, effort, filename = _validate_review_request(payload)
    with REVIEW_LOCK:
        output, findings, risk_score, agents_run = _run_engine_review(
            code, language, effort, filename
        )
        usage = token_usage.summary()
        blocking = int(output.get("blocking", 0))
        score_breakdown = category_scores(findings, agents_run, language, bool(usage.get("calls")))
        total = len(findings)
        summary = (
            "PRISM found no actionable issues."
            if total == 0
            else "PRISM found {} issue(s), including {} blocking.".format(total, blocking)
        )
        report_id = save_report(
            files_reviewed=[filename],
            findings=findings,
            risk_score=float(risk_score),
            blocking=blocking,
            commit_allowed=bool(output.get("commit_allowed", True)),
            token_usage=usage,
        )
        web_report = _store_web_context(
            report_id,
            language,
            effort,
            summary,
            bool(output.get("quality_gates_passed", True)),
            score_breakdown,
        )
        ai_failure = _ai_failure(effort, usage)

    return {
        "report": web_report,
        "ai": {"configured": bool(_provider_status()["configured"]), "failure": ai_failure},
        "testsRun": False,
    }


def _content_type_is_json(handler):
    return handler.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() == "application/json"


class PrismHandler(BaseHTTPRequestHandler):
    server_version = "PRISM-Local/1.0"

    def log_message(self, format_string, *args):
        LOGGER.info("%s - %s", self.address_string(), format_string % args)

    def _origin(self):
        return allowed_origin(self.headers.get("Origin"), ALLOWED_ORIGINS)

    def _send_json(self, status, payload):
        origin = self._origin()
        if self.headers.get("Origin") and origin is None:
            status = HTTPStatus.FORBIDDEN
            payload = {"error": "This website origin is not allowed to use the local PRISM companion."}
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _request_json(self):
        if self.headers.get("X-PRISM-Client") != "web":
            raise PermissionError("Missing PRISM web client header.")
        if not _content_type_is_json(self):
            raise TypeError("Requests must use application/json.")
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            size = 0
        if size < 0 or size > MAX_BODY_BYTES:
            raise OverflowError("Request is too large.")
        raw = self.rfile.read(size)
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Request body must be valid JSON.") from error
        if not isinstance(value, dict):
            raise ValueError("Request body must be a JSON object.")
        return value

    def _is_loopback_host(self):
        return is_loopback_host(self.headers.get("Host", ""))

    def _authorized_request(self):
        if not self._is_loopback_host():
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "The companion only accepts loopback requests."})
            return False
        origin = self._origin()
        if self.headers.get("Origin") and origin is None:
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "Website origin is not allowed."})
            return False
        if self.headers.get("X-PRISM-Client") != "web":
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "Missing PRISM web client header."})
            return False
        return True

    def do_OPTIONS(self):
        if not self._is_loopback_host():
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        origin = self._origin()
        if self.headers.get("Origin") and origin is None:
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-PRISM-Client")
        if self.headers.get("Access-Control-Request-Private-Network", "").lower() == "true":
            self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Access-Control-Max-Age", "300")
        self.end_headers()

    def do_GET(self):
        if not self._authorized_request():
            return
        path = urlsplit(self.path).path.rstrip("/") or "/"
        if path in ("/api/health", "/api/status"):
            provider = _provider_status()
            self._send_json(HTTPStatus.OK, {
                "ok": True,
                "version": getattr(prism, "__version__", "unknown"),
                "engine": "PRISM",
                "regexAvailable": True,
                "languages": list(LANGUAGE_EXTENSIONS),
                "ai": provider,
            })
        elif path == "/api/settings":
            self._send_json(HTTPStatus.OK, _settings())
        elif path == "/api/templates":
            self._send_json(HTTPStatus.OK, _settings()["templates"])
        elif path == "/api/reports":
            self._send_json(HTTPStatus.OK, _all_recent_reports())
        elif path.startswith("/api/reports/"):
            report_id = path.rsplit("/", 1)[-1]
            if not re.fullmatch(r"[A-Za-z0-9-]{1,80}", report_id):
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid report ID."})
                return
            report = load_report(report_id)
            if not report:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Report not found."})
                return
            self._send_json(HTTPStatus.OK, _to_web_report(report))
        else:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Endpoint not found."})

    def _read_json_or_send_error(self):
        try:
            return self._request_json()
        except PermissionError as error:
            self._send_json(HTTPStatus.FORBIDDEN, {"error": str(error)})
        except TypeError as error:
            self._send_json(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"error": str(error)})
        except OverflowError as error:
            self._send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": str(error)})
        except ValueError as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
        return None

    def _post_review(self, payload):
        self._send_json(HTTPStatus.CREATED, _build_review(payload))

    def _post_settings(self, payload):
        current = _settings()
        effort = payload.get("effort", current["effort"])
        theme = payload.get("theme", current["theme"])
        suggestions = payload.get("showSuggestions", current["showSuggestions"])
        valid = effort in VALID_EFFORTS and theme in VALID_THEMES and isinstance(suggestions, bool)
        if not valid:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid settings."})
            return
        current.update({"effort": effort, "theme": theme, "showSuggestions": suggestions})
        _write_settings(current)
        self._send_json(HTTPStatus.OK, current)

    def _post_template(self, payload):
        name = payload.get("name")
        description = payload.get("description", "Custom template")
        code = payload.get("code")
        valid_text = isinstance(description, str) and all(
            isinstance(value, str) and value.strip() for value in (name, code)
        )
        if not valid_text:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Template name, description, and code must be text."})
            return
        if len(name) > 80 or len(description) > 160 or len(code) > 10000:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Template fields exceed allowed lengths."})
            return
        current = _settings()
        if len(current["templates"]) >= 50:
            self._send_json(HTTPStatus.CONFLICT, {"error": "Local template limit reached."})
            return
        template = {
            "id": uuid4().hex,
            "name": name.strip(),
            "description": description.strip() or "Custom template",
            "code": code,
            "custom": True,
        }
        current["templates"].append(template)
        _write_settings(current)
        self._send_json(HTTPStatus.CREATED, template)

    def do_POST(self):
        if not self._authorized_request():
            return
        payload = self._read_json_or_send_error()
        if payload is None:
            return
        path = urlsplit(self.path).path.rstrip("/") or "/"
        handler = {
            "/api/reviews": self._post_review,
            "/api/settings": self._post_settings,
            "/api/templates": self._post_template,
        }.get(path)
        if handler is None:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Endpoint not found."})
            return
        try:
            handler(payload)
        except ValueError as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
        except Exception:
            LOGGER.exception("Local PRISM request failed")
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "PRISM could not complete this request."})

    def do_PUT(self):
        self.do_POST()

    def _delete_all_reports(self):
        payload = self._read_json_or_send_error()
        if payload is None:
            return
        if payload.get("confirm") is not True:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Confirm report deletion."})
            return
        self._send_json(HTTPStatus.OK, {"deleted": clear_reports()})

    def _delete_report(self, report_id):
        if not re.fullmatch(r"[A-Za-z0-9-]{1,80}", report_id):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid report ID."})
            return
        self._send_json(HTTPStatus.OK, {"deleted": bool(delete_report(report_id))})

    def _delete_template(self, template_id):
        current = _settings()
        remaining = [item for item in current["templates"] if item.get("id") != template_id]
        if len(remaining) == len(current["templates"]):
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Template not found."})
            return
        current["templates"] = remaining
        _write_settings(current)
        self._send_json(HTTPStatus.OK, {"deleted": True})

    def do_DELETE(self):
        if not self._authorized_request():
            return
        path = urlsplit(self.path).path.rstrip("/") or "/"
        if path == "/api/reports":
            self._delete_all_reports()
            return
        match = re.fullmatch(r"/api/(reports|templates)/([A-Za-z0-9-]{1,80})", path)
        if match is None:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Endpoint not found."})
            return
        collection, identifier = match.groups()
        handlers = {"reports": self._delete_report, "templates": self._delete_template}
        handlers[collection](identifier)


class LocalPrismServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    parser = argparse.ArgumentParser(description="Run PRISM’s loopback-only web companion.")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PRISM_WEB_PORT", "8765")))
    args = parser.parse_args()
    server = LocalPrismServer(("127.0.0.1", args.port), PrismHandler)
    print("PRISM local companion: http://localhost:{}/api/health".format(args.port))
    print("Project data and reports stay in {}".format(APP_DIR))
    print("Allowed web origins: {}".format(", ".join(sorted(ALLOWED_ORIGINS))))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping PRISM local companion.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
