from pathlib import Path
from collections import defaultdict
from sdk_taxonomy import checked_classify
import argparse
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
OUT = ROOT / "mkdocs.yml"
ORDER = [
 "Introduction", "Effect Basics", "Effect Details", "SmartFX",
 "Effect UI & Events", "Audio", "AEGPs", "Artisans", "AEIOs",
 "Premiere Pro & Other Hosts",
 "Scripting (ExtendScript DOM)", "Expressions (AE Host API)",
 "Extension Host Interfaces (Distinct APIs)", "Command Line (aerender)",
 "Observed Native Implementation (AEIG Research)",
 "Observed Render, Cache & Execution (AEIG Research)",
 "Observed Project, Media & Persistence (AEIG Research)",
 "Research & Evidence", "Reference",
]

def title(p):
 txt=p.read_text(encoding="utf-8-sig",errors="replace")
 m=re.search(r"(?m)^#\s+(.+?)\s*$",txt)
 return re.sub(r"[\x60*_]","",m.group(1)).strip() if m else p.stem.replace("-"," ").title()

def group_for(p):
    """Classify by the owning API/host context, never a shared API nickname.

    "Custom ECW UI" and "Custom Comp UI" both use Drawbot; they remain
    independently navigable. Private TDB/BEE/FLT/PIN evidence is never
    presented as a public AEGP or Effect Details SDK API.
    """
    classification = checked_classify(p.as_posix())
    return classification.section, classification.topic


def quote(s):return '"' + s.replace("\\","\\\\").replace('"','\\"') + '"'

def navigation():
 groups=defaultdict(lambda:defaultdict(list))
 # Only committed or explicitly staged pages may appear in the deployed
 # navigation. Other active local research can contain untracked Markdown;
 # including it would produce broken GitHub Pages links on the next push.
 proc = subprocess.run(
     ["git","-C",str(ROOT),"ls-files","--cached","-z","--","docs"],
     capture_output=True,check=True)
 files = sorted(
     Path(item[len("docs/"):])
     for item in proc.stdout.decode("utf-8").split("\0")
     if item.startswith("docs/") and item.endswith(".md")
     and (ROOT/item).is_file())
 assert files, "No tracked Markdown pages available for navigation"
 for p in files:
  if p.as_posix()=="index.md":continue
  top,feature=group_for(p)
  groups[top][feature].append(p)
 nav=["nav:","    - Home: index.md"]
 paths=[]
 for top in ORDER:
  if top not in groups:continue
  nav.append("    - "+quote(top)+":")
  for feature,items in groups[top].items():
   nav.append("        - "+quote(feature)+":")
   for p in sorted(items,key=lambda p:(0 if p.name=="index.md" else 1 if p.name=="overview.md" else 2,title(DOCS/p).casefold(),p.as_posix())):
    nav.append("            - "+quote(title(DOCS/p))+": "+p.as_posix())
    paths.append(p.as_posix())
 assert len(paths)==len(set(paths))==len(files)-1
 assert set(paths)=={p.as_posix() for p in files if p.as_posix()!="index.md"}
 return "\n".join(nav)+"\n",groups,len(files)

site_nav,grouped,file_count=navigation()
print("NAV COVERAGE",file_count,"pages",len(grouped),"top-level sections",
 sum(map(len,grouped.values())),"feature sections")
for top in ORDER:
 if top in grouped:
  print(" ",top,sum(len(v) for v in grouped[top].values()),"pages",len(grouped[top]),"subsections")

# Preserve the repository's documented Material theme, plugins and CSS while
# replacing only the navigation and the one noncollapsible sections feature.
# This keeps existing active contributors' Markdown pages and settings in view.
HEADER = """site_name: After Effects Internals Guide
site_description: After Effects C++ SDK companion and evidence-graded internal architecture reference
site_url: https://ken-eizo.github.io/after-effects-internals-guide/
repo_url: https://github.com/ken-eizo/after-effects-internals-guide
repo_name: ken-eizo/after-effects-internals-guide
edit_uri: edit/main/docs/
docs_dir: docs
copyright: Unofficial research. Adobe and After Effects are trademarks of Adobe.

"""
existing=OUT.read_text(encoding="utf-8-sig") if OUT.exists() else ""
tail=existing.split("\ntheme:\n",1)[1] if "\ntheme:\n" in existing else ""
assert tail, "Existing Material config missing: do not clobber"
tail="theme:\n"+tail
tail=tail.replace("        - navigation.sections\n","")
tail=tail.replace("        - navigation.expand\n","")
if "        - navigation.indexes\n" not in tail:
 tail=tail.replace("        - navigation.footer\n","        - navigation.footer\n        - navigation.indexes\n")
if "        - navigation.tracking\n" not in tail:
 tail=tail.replace("        - navigation.indexes\n","        - navigation.indexes\n        - navigation.tracking\n")
config=HEADER+site_nav+"\n"+tail
assert "navigation.sections" not in config
ap=argparse.ArgumentParser()
ap.add_argument("--check",action="store_true")
ap.add_argument("--dry-run",action="store_true")
ap.add_argument("--output",type=Path,default=OUT)
args=ap.parse_args()
if args.check:
 assert args.output.exists(),"No mkdocs.yml"
 current=args.output.read_text(encoding="utf-8-sig")
 assert current==config, "Site config differs from generated canonical navigation"
 print("PASS canonical grouped collapsible navigation up to date")
elif args.dry_run:
 print("PREVIEW")
 print(config[:5500])
else:
 args.output.write_text(config,encoding="utf-8")
 print("WROTE",args.output,"pages",file_count)
