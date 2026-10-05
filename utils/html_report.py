"""Create a local HTML summary from real pytest JUnit results (stdlib only)."""
import argparse
import html
from pathlib import Path
import xml.etree.ElementTree as ET


def generate(source, destination, rerun=None):
    root = ET.parse(source).getroot()
    rows = []
    totals = dict(passed=0, failed=0, error=0, skipped=0)
    cases = {(c.get("classname", ""), c.get("name", "")): c for c in root.iter("testcase")}
    history = {}
    if rerun:
        for case in ET.parse(rerun).getroot().iter("testcase"):
            key = (case.get("classname", ""), case.get("name", ""))
            if key in cases:
                previous = cases[key].find("failure")
                if previous is None:
                    previous = cases[key].find("error")
                if previous is not None:
                    history[key] = previous.text or previous.get("message", "")
            cases[key] = case
    for case in cases.values():
        status = "passed"
        detail = ""
        for kind, tag in (("failed", "failure"), ("error", "error"), ("skipped", "skipped")):
            node = case.find(tag)
            if node is not None:
                status = kind
                detail = node.text or node.get("message", "")
                break
        totals[status] += 1
        key = (case.get("classname", ""), case.get("name", ""))
        shown_status = status
        if key in history:
            detail = "Initial failure (retained for transparency):\n" + history[key] + "\n\nLatest rerun: " + status + "\n" + detail
            shown_status += " on rerun"
        name = case.get("classname", "") + "::" + case.get("name", "")
        if "test_admin_live" in name or "test_discrepancy_e2e" in name:
            evidence = "Live read-only"
        elif "test_login" in name or "test_discrepancy_smoke" in name:
            evidence = "Live UI"
        elif "protected_route" in name:
            evidence = "Unauthenticated UI"
        else:
            evidence = "Controlled API / UI"
        rows.append(f'<tr class="{status}"><td>{html.escape(name)}</td><td>{evidence}</td><td>{shown_status}</td><td>{html.escape(case.get("time", ""))}</td><td><details><summary>Details</summary><pre>{html.escape(detail)}</pre></details></td></tr>')
    summary = " | ".join(f"{key}: {value}" for key, value in totals.items())
    provenance = "Source: " + Path(source).name
    if rerun:
        provenance += "; additional validation run: " + Path(rerun).name + ". Original failures are retained in Details; additional results extend coverage and replace matching tests."
    document = """<!doctype html><html><head><meta charset="utf-8"><title>Admin test report</title>
<style>body{font:15px Arial;margin:30px;background:#f5f7fa}table{border-collapse:collapse;background:white;width:100%}td,th{padding:10px;border:1px solid #ddd;text-align:left}pre{white-space:pre-wrap;max-width:700px}.failed,.error{background:#ffe9e9}.skipped{background:#fff8df}h1{color:#193e70}</style></head><body><h1>Admin test report</h1><p>""" + html.escape(summary) + "</p><p>" + html.escape(provenance) + """</p><p>Controlled API results validate UI behavior; they do not certify the live backend. Live tests are read-only.</p><table><thead><tr><th>Test</th><th>Evidence</th><th>Result</th><th>Seconds</th><th>Failure</th></tr></thead><tbody>""" + "".join(rows) + "</tbody></table></body></html>"
    Path(destination).write_text(document, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--rerun", help="Optional actual JUnit results for affected tests rerun after fixes")
    args = parser.parse_args()
    generate(args.input, args.output, args.rerun)
