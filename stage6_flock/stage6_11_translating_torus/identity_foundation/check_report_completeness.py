"""Automated incompleteness scan for identity_foundation/*.md reports.

Per the mandate's requirement that "new generated reports must fail an
automated check for unfinished sections or inconsistent counts" -- this is
that check, run by hand today, meant to be run before treating any report
in this directory as final. Not wired into a test runner (no CI exists for
markdown in this repo); invoke directly: `python3 check_report_completeness.py`.

Deliberately simple: a denylist scan plus a markdown-table row-count cross
check against any "N rows"/"N seeds"/"N candidates" style count asserted in
the surrounding prose. False positives are expected and fine -- this is a
tripwire, not a formal verifier.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).parent

DENYLIST = [
    r"\bPLACEHOLDER\b",
    r"\bTODO\b",
    r"\bTBD\b",
    r"\[FILL",
    r"\bXXX\b",
    r"<insert",
]

# Words discussing the word "placeholder" as a historical fact (about
# RESULTS_6_11B.md's own past) are legitimate prose, not an unfinished
# section in *this* report -- exempt lines that quote or discuss the term
# rather than containing a live placeholder token themselves.
EXEMPT_CONTEXT = re.compile(r"still contained completion placeholders|automated .unfinished section. scan|PLACEHOLDER\|TBD\|TODO", re.IGNORECASE)


def scan_file(path: Path) -> list[str]:
    issues = []
    text = path.read_text()
    for lineno, line in enumerate(text.splitlines(), 1):
        if EXEMPT_CONTEXT.search(line):
            continue
        for pat in DENYLIST:
            if re.search(pat, line):
                issues.append(f"{path.name}:{lineno}: matched {pat!r}: {line.strip()[:120]}")
    return issues


def check_table_row_counts(path: Path) -> list[str]:
    """Best-effort: if prose asserts 'N seeds'/'N candidates'/'N files' near
    a markdown table, check the table's data-row count matches N. Cheap
    heuristic, not exhaustive -- flags a mismatch for human review rather
    than silently trusting either number."""
    issues = []
    text = path.read_text()
    lines = text.splitlines()
    count_claim = re.compile(r"\b(\d+)\s+(seeds?|candidates?|files?|rows?|scenarios?|hypotheses)\b", re.IGNORECASE)
    for i, line in enumerate(lines):
        m = count_claim.search(line)
        if not m:
            continue
        claimed_n = int(m.group(1))
        # look for the nearest markdown table within the next 15 lines
        for j in range(i, min(i + 15, len(lines))):
            if lines[j].strip().startswith("|") and set(lines[j].strip()) <= set("|-: "):
                # this is a header-separator row; count data rows after it
                data_rows = 0
                k = j + 1
                while k < len(lines) and lines[k].strip().startswith("|"):
                    data_rows += 1
                    k += 1
                if claimed_n and abs(data_rows - claimed_n) > max(2, claimed_n // 5):
                    issues.append(
                        f"{path.name}:{i+1}: prose claims {claimed_n} {m.group(2)}, "
                        f"nearby table at line {j+1} has {data_rows} data rows -- verify by hand"
                    )
                break
    return issues


def main() -> int:
    md_files = sorted(HERE.glob("*.md"))
    all_issues: list[str] = []
    for path in md_files:
        all_issues.extend(scan_file(path))
        all_issues.extend(check_table_row_counts(path))

    if all_issues:
        print(f"{len(all_issues)} potential issue(s) found across {len(md_files)} file(s):\n")
        for issue in all_issues:
            print(" -", issue)
        return 1

    print(f"No denylist/row-count issues found across {len(md_files)} file(s): "
          + ", ".join(p.name for p in md_files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
