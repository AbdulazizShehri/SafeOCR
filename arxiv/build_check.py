from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
main = (ROOT / "main.tex").read_text(encoding="utf-8")
bib = (ROOT / "references.bib").read_text(encoding="utf-8")

errors = []

if "\\documentclass" not in main or "\\begin{document}" not in main or "\\end{document}" not in main:
    errors.append("main.tex is missing a required document boundary")

cite_keys = set()
for group in re.findall(r"\\cite\{([^}]+)\}", main):
    cite_keys.update(k.strip() for k in group.split(",") if k.strip())

bib_keys = set(re.findall(r"@[A-Za-z]+\{([^,]+),", bib))
missing = sorted(cite_keys - bib_keys)
if missing:
    errors.append("missing bibliography keys: " + ", ".join(missing))

for forbidden in ("api_key", "token:", "password", ".env", "BEGIN PRIVATE KEY"):
    if forbidden.lower() in main.lower() or forbidden.lower() in bib.lower():
        errors.append(f"possible secret/private marker found: {forbidden}")

if "375/1,850" not in main and "375/1850" not in main:
    errors.append("Ma2023 frozen 375/1,850 result not found")
if "0/375" not in main:
    errors.append("Ma2023 0/375 unsafe numeric component-pass result not found")
if "72.57" not in main:
    errors.append("LabGold 72.57% verified coverage not found")

if errors:
    print("ARXIV_PACKAGE_CHECK=FAIL")
    for e in errors:
        print("-", e)
    sys.exit(1)

print("ARXIV_PACKAGE_CHECK=PASS")
print(f"CITATIONS={len(cite_keys)}")
print(f"BIB_ENTRIES={len(bib_keys)}")
