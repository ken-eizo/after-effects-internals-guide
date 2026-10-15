"""Enumerate all AEIG pages with explicit public / observed / research ownership."""
from pathlib import Path
from collections import Counter
from sdk_taxonomy import checked_classify
import sys,re,csv,io,argparse
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
ROOT=Path(__file__).resolve().parents[2]
DOCS=ROOT/"docs"
CSV=ROOT/"datasets/aeig-sdk-taxonomy-inventory.csv"
REPORT=DOCS/"reference/sdk-taxonomy-coverage.md"
def gather():
 rows=[]
 for p in sorted(DOCS.rglob("*.md")):
  rel=p.relative_to(DOCS).as_posix()
  c=checked_classify(rel)
  t=p.read_text(encoding="utf-8-sig",errors="replace")
  h=re.search(r"(?m)^#\s+(.+?)\s*$",t)
  m=re.search(r"(?m)^status:\s*(.+)$",t)
  rows.append(dict(path=rel,heading=h.group(1) if h else "",
       section=c.section,topic=c.topic,authority=c.authority,owner=c.owner,
       status=m.group(1) if m else "unclassified evidence status"))
  assert not (rel.startswith("ui-system/effect-controls-custom-ui/") and c.owner!="Custom ECW UI")
  assert not (rel.startswith("ui-system/gizmo-") and c.owner!="Custom Comp UI")
  assert not (rel.startswith("state-model/native-property-system/") and c.section=="AEGPs")
  assert not (rel.startswith("host-integration/cpp-sdk/effect-details/postload-") and c.authority=="official")
 return rows
def report(rows):
 n=Counter(r["section"] for r in rows)
 a=Counter(r["authority"] for r in rows)
 out=["---","status: generated-editorial-audit; not proof of every page claim",
      "last_verified: 2026-10-16","---","",
      "# AEIG SDK Terminology and Host-context Classification Coverage","",
      f"**Documents classified:** {len(rows)}. **Owner sections:** {len(n)}.",
      f"Official API name-origin: **{a['official']}**; observed private implementation: **{a['observed']}**; AEIG research model: **{a['research']}**.",
      "",
      "The CSV inventory: ¤datasets/aeig-sdk-taxonomy-inventory.csv¤.",
      "Every document is assigned a function owner and name provenance. This is not a certification that the documentation or host behavior was tested.",
      "",
      "## Navigation ownership","",
      "| API family / observed host context | Documents |",
      "| --- | ---: |"]
 for section,count in n.most_common():out.append(f"| {section} | {count} |")
 out+=["","## Known collision classes and decisions","",
       "| Collision | Editorial resolution |","| --- | --- |",
       "| Custom ECW UI / Custom Comp UI | Two official Effect UI purposes, separated by PF_Window_EFFECT vs PF_Window_COMP/LAYER |",
       "| Drawbot shared API | Shared drawing suite, never feature owner of both UIs |",
       "| AEGP Stream suites / TDB-BEE | Public suite in AEGPs; private factory and Stream objects in Observed Native Implementation |",
       "| SmartFX GPU / Drawbot | Pixel renderer vs host-managed effect UI drawing |",
       "| FLT/PIN postload / Effect Details | Private native module lifecycle, not public PF extension API |",
       "| CEP / UXP | Host panel scripting bridge vs version-scoped UXP runtime observation |",
       "| Effect Preview Media (Effects Panel) / Effect Controls Window | Adobe's Effect Preview Media applies to Premiere Pro Beta 27.0+ only (Aug 2026), NOT After Effects; Custom ECW UI is AE Effect UI |",
       "","## Scope and limitations","",
       "- This generated inventory records each Markdown H1, path, functional owner and declared evidence status.",
       "- Unknown directories fail classification; source code: ¤probes/process-tools/sdk_taxonomy.py¤.",
       "- Existing evidence or programmatic test outcomes are not upgraded by moving pages or renaming site navigation.",
       "- Private functions may retain exact native symbol names from installed AE versions; they cannot be given invented Adobe public API names.",
       "- To regenerate: ¤python probes/process-tools/audit_sdk_taxonomy.py¤; use ¤--check¤ to verify the stored inventory.",
       "","See [Official names and contextual scope](../foundations/sdk-nomenclature-and-context.md).",""]
 return "\n".join(out).replace("¤",chr(96))
def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--check",action="store_true")
 args=parser.parse_args()
 rows=gather()
 output=io.StringIO(newline="")
 writer=csv.DictWriter(output,fieldnames=list(rows[0]),lineterminator="\n")
 writer.writeheader();writer.writerows(rows)
 cs=output.getvalue()
 rs=report(rows)
 if args.check:
  assert CSV.read_text(encoding="utf-8")==cs,"Stale taxonomy CSV"
  assert REPORT.read_text(encoding="utf-8")==rs,"Stale taxonomy report"
  print("PASS",len(rows),"pages classified")
 else:
  CSV.parent.mkdir(parents=True,exist_ok=True)
  CSV.write_text(cs,encoding="utf-8")
  REPORT.write_text(rs,encoding="utf-8")
  print("WROTE",len(rows),"pages",len(set(x["section"] for x in rows)),"sections")
if __name__=="__main__":main()
