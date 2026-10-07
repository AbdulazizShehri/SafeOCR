import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
main = (ROOT / "main.tex").read_text(encoding="utf-8")
bib = (ROOT / "references.bib").read_text(encoding="utf-8")

errors: list[str] = []

document_markers = (r"\documentclass", r"\begin{document}", r"\end{document}")
if any(marker not in main for marker in document_markers):
    errors.append("main.tex is missing a required document boundary")

cite_keys: set[str] = set()
for group in re.findall(r"\\cite\{([^}]+)\}", main):
    cite_keys.update(key.strip() for key in group.split(",") if key.strip())

bib_keys = set(re.findall(r"@[A-Za-z]+\{([^,]+),", bib))
missing = sorted(cite_keys - bib_keys)
if missing:
    errors.append("missing bibliography keys: " + ", ".join(missing))
uncited = sorted(bib_keys - cite_keys)
if uncited:
    errors.append("uncited bibliography entries: " + ", ".join(uncited))

for forbidden in ("api_key", "token:", "password", ".env", "BEGIN PRIVATE KEY"):
    if forbidden.lower() in main.lower() or forbidden.lower() in bib.lower():
        errors.append(f"possible secret/private marker found: {forbidden}")

required_text = {
    "Ma2023 frozen 375/1,850 result": ("375/1,850", "375/1850"),
    "Ma2023 0/375 numeric component-pass result": ("0/375",),
    "LabGold 72.57% verified coverage": ("72.57",),
    "ClinOCR PaddleOCR 57/328 runtime-failure disclosure": ("57/328",),
    "exploratory 38/375 analyte-or-unit mismatch disclosure": ("38/375",),
    "LabGold ungated zero-event bound": ("1.316",),
    "Ma2023 ungated zero-event bound": ("0.207",),
}
for label, alternatives in required_text.items():
    if not any(value in main for value in alternatives):
        errors.append(f"{label} not found")

if "0.89" in main and "applies to the separate PKU1 dataset" not in main:
    errors.append("kappa=0.89 appears without the required PKU1 attribution")
if "preregistered" in main.lower():
    errors.append("stale preregistered wording found; use prespecified/commit-timestamped")
if "# SafeOCR" in main:
    errors.append("literal Markdown title leaked into LaTeX source")
if "Draft status" in main:
    errors.append("draft-status artifact leaked into LaTeX source")
table_count = len(re.findall(r"\\begin\{table\*?\}", main))
figure_count = len(re.findall(r"\\begin\{figure\*?\}", main))
if table_count != 4:
    errors.append(f"expected exactly four main tables, found {table_count}")
if figure_count > 6:
    errors.append(f"arXiv/JAMIA package exceeds six figures: {figure_count}")
if re.search(r"^\s*\|", main, flags=re.MULTILINE):
    errors.append("raw Markdown table row leaked into LaTeX source")
if "independent critical-crop" in main.lower() or "independent verification" in main.lower():
    errors.append("stale independence wording found; use second-engine/shared-crop wording")
if r"\n\bibliography" in main:
    errors.append("literal \\n command leaked before bibliography")

if errors:
    print("ARXIV_PACKAGE_CHECK=FAIL")
    for error in errors:
        print("-", error)
    sys.exit(1)

print("ARXIV_PACKAGE_CHECK=PASS")
print(f"CITATIONS={len(cite_keys)}")
print(f"BIB_ENTRIES={len(bib_keys)}")
print(f"TABLES={table_count}")
print(f"FIGURES={figure_count}")
