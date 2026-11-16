#!/usr/bin/env python3
"""prism-review — Anna Executa plugin for PRISM-style code review."""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prism_engine.agents import review_text
from prism_engine.reporter import score_findings

MANIFEST = {
    "name": "prism-review",
    "display_name": "PRISM Code Review",
    "version": "1.0.0",
    "description": "Multi-agent code review: security, quality, policy, test findings with scores and fix suggestions.",
    "author": "builder",
    "tools": [
        {
            "name": "review_code",
            "description": "Review a single file's source code for security, quality, policy, and test issues. Returns findings with line numbers and fix suggestions.",
            "parameters": [
                {"name": "filename", "type": "string", "description": "Name of the file being reviewed", "required": True},
                {"name": "content", "type": "string", "description": "Source code content to review", "required": True},
                {"name": "language", "type": "string", "description": "Programming language (python, javascript, typescript, go, rust, etc.)", "required": False}
            ],
        },
        {
            "name": "scan_files",
            "description": "Review multiple files at once. Returns per-file findings and an overall project score.",
            "parameters": [
                {"name": "files", "type": "array", "description": "List of {filename, content, language} objects", "required": True}
            ],
        },
    ],
}


def invoke(tool, args):
    if tool == "review_code":
        filename = args.get("filename", "unknown")
        content = args.get("content", "")
        language = args.get("language")
        findings = review_text(filename, content, language)
        project_score = score_findings(findings)
        return {
            "success": True,
            "data": {
                "filename": filename,
                "language": language,
                "findings": findings,
                "score": project_score,
                "total_findings": len(findings),
                "blocking": sum(1 for f in findings if f.get("blocking")),
            },
        }
    if tool == "scan_files":
        files = args.get("files", [])
        per_file = []
        all_findings = []
        for f in files:
            fname = f.get("filename", "unknown")
            content = f.get("content", "")
            language = f.get("language")
            findings = review_text(fname, content, language)
            file_score = score_findings(findings)
            per_file.append({
                "filename": fname,
                "language": language,
                "findings": findings,
                "score": file_score,
                "total_findings": len(findings),
                "blocking": sum(1 for x in findings if x.get("blocking")),
            })
            all_findings.extend(findings)
        overall = score_findings(all_findings)
        return {
            "success": True,
            "data": {
                "per_file": per_file,
                "overall_score": overall,
                "total_findings": len(all_findings),
                "total_files": len(files),
                "blocking": sum(1 for x in all_findings if x.get("blocking")),
            },
        }
    raise ValueError(f"unknown tool: {tool}")


def handle(req):
    method = req.get("method")
    if method == "describe":
        return {"result": MANIFEST}
    if method == "invoke":
        params = req.get("params") or {}
        try:
            return {"result": invoke(params.get("tool", ""), params.get("arguments") or {})}
        except ValueError as exc:
            return {"error": {"code": -32601, "message": str(exc)}}
        except Exception as exc:
            return {"error": {"code": -32603, "message": str(exc)}}
    if method == "health":
        return {"result": {"status": "ready"}}
    return {"error": {"code": -32601, "message": f"unknown method: {method}"}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as exc:
            payload = {"error": {"code": -32700, "message": str(exc)}}
            req_id = None
        else:
            payload = handle(req)
            req_id = req.get("id")
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": req_id, **payload}) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
