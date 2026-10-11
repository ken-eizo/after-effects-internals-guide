from pathlib import Path
from datetime import date
from collections import Counter
import csv, re, sys

ROOT=Path(r"D:\Developer\After Effects Internals Guide")
SRC=ROOT/"research"/"bug-quirks.csv"
OUT=ROOT/"datasets"/"aeig-bug-quirk-registry.csv"
PAGE=ROOT/"docs"/"reference"/"bug-quirk-registry.md"
FINDINGS=ROOT/"research"/"findings"

REQUIRED=[
    "bug_id","title","source_type","subsystem","affected_versions","fixed_version",
    "status","symptom","architecture_boundary","workaround_or_rule","evidence_ref",
    "source_url","docs_page","finding_id","confidence",
]

def read_rows(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

if not SRC.exists():
    raise SystemExit(f"missing curated bug/quirk source: {SRC}")
rows=read_rows(SRC)
errors=[]
if not rows:
    errors.append("registry source has no rows")
seen=set(); enriched=[]
for i,row in enumerate(rows,start=2):
    missing=[k for k in REQUIRED if k not in row]
    if missing:
        errors.append(f"row {i}: missing columns {missing}"); continue
    bid=row["bug_id"].strip()
    if not re.fullmatch(r"BQ-\d{4}",bid):
        errors.append(f"row {i}: invalid bug_id {bid!r}")
    if bid in seen: errors.append(f"row {i}: duplicate bug_id {bid}")
    seen.add(bid)
    for field in ("title","source_type","subsystem","status","symptom","architecture_boundary","evidence_ref","confidence"):
        if not row[field].strip(): errors.append(f"row {i}: empty {field}")
    url=row["source_url"].strip()
    if url and not re.match(r"^https://",url): errors.append(f"row {i}: non-HTTPS source_url {url}")
    doc_rel=row["docs_page"].strip()
    doc_exists=bool(doc_rel and (ROOT/doc_rel).exists())
    if doc_rel and not doc_exists: errors.append(f"row {i}: missing docs_page {doc_rel}")
    fid=row["finding_id"].strip()
    finding_matches=list(FINDINGS.glob(fid+"-*.md")) if fid else []
    finding_exists=(not fid) or len(finding_matches)==1
    if fid and not finding_exists: errors.append(f"row {i}: finding_id {fid} resolved {len(finding_matches)} files")
    out={k:row[k].strip() for k in REQUIRED}
    out["docs_exists"]=doc_exists
    out["finding_exists"]=finding_exists
    enriched.append(out)
if errors:
    print("BUG/QUIRK REGISTRY: FAIL")
    for e in errors: print(" -",e)
    raise SystemExit(2)

fields=REQUIRED+["docs_exists","finding_exists"]
with OUT.open("w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(enriched)

source_counts=Counter(r["source_type"] for r in enriched)
status_counts=Counter(r["status"] for r in enriched)
subsystem_counts=Counter(r["subsystem"].split("/",1)[0] for r in enriched)
fixed=sum(r["status"]=="fixed" for r in enriched)
active=sum(r["status"]!="fixed" for r in enriched)

lines=["---","status: generated",f"last_verified: {date.today().isoformat()}","---",
       "# AEIG Bug / Quirk / Regression Registry","",
       f"Curated entries: **{len(enriched)}**. Upstream-reported fixed: **{fixed}**. Other / source-repaired / contract / historical entries: **{active}**.","",
       "This registry is an evidence index, not a claim that AEIG knows every After Effects bug. A symptom identifies a boundary to investigate; it does not by itself prove a private root cause.","",
       "## Source classes","","| Source type | Entries |","|---|---:|"]
for k,v in source_counts.most_common(): lines.append(f"| `{k}` | {v} |")
lines += ["","## Subsystem coverage","","| Subsystem family | Entries |","|---|---:|"]
for k,v in subsystem_counts.most_common(): lines.append(f"| `{k}` | {v} |")
lines += ["","## Registry","",
          "| ID | Status | Subsystem | Symptom | Boundary / rule | Evidence |","|---|---|---|---|---|---|"]
for r in enriched:
    evidence=r["finding_id"] or r["evidence_ref"]
    rule=(r["architecture_boundary"]+"; "+r["workaround_or_rule"]).replace("|","/")
    lines.append(f"| `{r['bug_id']}` | `{r['status']}` | `{r['subsystem']}` | {r['symptom'].replace('|','/')} | {rule} | {evidence.replace('|','/')} |")
lines += ["","## Editorial rules","",
          "1. Fixed/known issue wording is behavioral evidence, not automatic proof of root cause.",
          "2. Unsupported SDK/sample behavior is labeled as a contract warning or pitfall rather than public functionality.",
          "3. Version scope is mandatory. Historical quirks are not silently described as current behavior.",
          "4. Add a Finding when a bug materially supports an architectural conclusion; keep the registry row as the symptom/version index.",
          "5. Preserve unknowns. If no workaround or cause is established, say so rather than inventing one.",
          "6. Source-repair statuses describe pinned laboratory evidence. They neither assign an Adobe fixed version nor establish real-host validation; partial policies retain their unsupported domains.","",
          "Machine-readable registry: `datasets/aeig-bug-quirk-registry.csv`. Curated source: `research/bug-quirks.csv`."]
PAGE.write_text("\n".join(lines)+"\n",encoding="utf-8")
print("BUG/QUIRK REGISTRY: PASS")
print("entries",len(enriched),"fixed",fixed,"nonfixed",active)
print("sources",dict(source_counts)); print("statuses",dict(status_counts))
print("wrote",OUT); print("wrote",PAGE)
