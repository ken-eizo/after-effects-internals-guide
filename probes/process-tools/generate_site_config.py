from pathlib import Path
from collections import defaultdict
import argparse
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
OUT = ROOT / "mkdocs.yml"
ORDER = [
 "Introduction", "Effect Basics", "Effect Details", "SmartFX",
 "Effect UI & Events", "Audio", "AEGPs", "Artisans", "AEIOs",
 "Premiere Pro & Other Hosts", "Native Internals", "Rendering & Performance",
 "Project, Persistence & Media", "Other Host Interfaces",
 "Research & Evidence", "Reference",
]
OFFICIAL = {
 "introduction":"Introduction","effect-basics":"Effect Basics",
 "effect-details":"Effect Details","smartfx":"SmartFX",
 "effect-ui-events":"Effect UI & Events","audio":"Audio","aegps":"AEGPs",
 "artisans":"Artisans","aeios":"AEIOs",
 "premiere-other-hosts":"Premiere Pro & Other Hosts",
}
INTERNAL = {
 "architecture":"Whole-System Architecture","state-model":"Project State / Identity",
 "vector-shape-system":"Vector and Shape","text-system":"Text / Animators",
 "animation-system":"Animation / Keyframes","evaluation":"BEE Evaluation",
 "expression-engine":"Expressions","three-d-system":"3D",
 "ai-analysis":"AI and Analysis","tracking-analysis":"Tracking and Analysis",
 "ui-system":"UI and Timeline Internals",
}
RENDER = {
 "render-graph":"Render Graph","cache-system":"Cache",
 "temporal-system":"Temporal / Motion Blur","gpu-system":"GPU",
 "image-pipeline":"Image and Pixel Pipeline","color-pipeline":"Color",
 "memory-system":"Memory","mfr":"Multi-Frame Rendering",
 "threading-system":"Threading",
}
PROJECT = {
 "persistence":"Project Formats / Serialization","media-system":"Media",
 "interop":"Interoperability","product-shell":"Panels and Workspaces",
 "headless-system":"Headless / Command Line",
}
HOST = {
 "pica-sweetpea":"PICA and SweetPea","uxp-cep":"CEP and UXP",
 "cep":"CEP and UXP","command-line":"Command Line",
 "expressions":"Expressions API",
}
REFERENCE = {
 "API, SDK and Version Atlas":(
  "api","guide","sdk","surface","version","binding","registry","export",
  "corpus-coverage","master-surface"),
 "Release Status and Qualification":(
  "release","static-rc","static-release","readiness","aeig-1","final-operator",
  "l5-outcome","pre-operator","roadmap"),
 "Research Receipts and Self-Tests":(
  "selftest","prediction","finalizer","promot","integrity","audit","l5-",
  "radical-resolution","unknown","status","trace"),
}

def title(p):
 txt=p.read_text(encoding="utf-8-sig",errors="replace")
 m=re.search(r"(?m)^#\s+(.+?)\s*$",txt)
 return re.sub(r"[\x60*_]","",m.group(1)).strip() if m else p.stem.replace("-"," ").title()

def group_for(p):
 parts=p.parts
 area=parts[0]
 name=parts[-1]
 if area=="host-integration":
  if len(parts)>2 and parts[1]=="cpp-sdk":
   if len(parts)>3 and parts[2] in OFFICIAL:
    return OFFICIAL[parts[2]],"Guide and API"
   if name in ("performance-and-escape-hatches.md","verified-render-contracts.md"):
    return "Effect Details","Performance and SDK Execution"
   if name in ("aegp-internal-coordinate-bridges.md","state-api-evolution.md"):
    return "AEGPs","SDK State and Suite Semantics"
   return "Introduction","SDK Architecture, ABI and Samples"
  sub=parts[1] if len(parts)>1 else ""
  if sub=="scripting":return "AEGPs","Scripting, Properties and Reflection"
  if sub=="aegp":return "AEGPs","AEGP Runtime"
  if sub=="smartfx":return "SmartFX","SmartFX Runtime"
  if sub=="artisans":return "Artisans","Artisan Runtime"
  if sub=="aeio":return "AEIOs","AEIO Runtime"
  if sub=="premiere-pro":return "Premiere Pro & Other Hosts","Host Comparison"
  return "Other Host Interfaces",HOST.get(sub,"Host Integration")
 if area=="state-model" and len(parts)>1 and parts[1]=="native-property-system":
  return "AEGPs","Native Property System"
 if area=="ui-system" and (name.startswith("gizmo-") or name in {
  "drawbot-ui-drawing.md","interactive-ui-latency.md",
  "effect-custom-ui-input-routing.md","effect-custom-ui-invalidation.md",
  "async-custom-ui-rendering.md"}):
  return "Effect UI & Events","Drawbot, Events and Gizmos"
 if area=="audio-system":return "Audio","Audio Runtime"
 if area in INTERNAL:return "Native Internals",INTERNAL[area]
 if area in RENDER:return "Rendering & Performance",RENDER[area]
 if area in PROJECT:return "Project, Persistence & Media",PROJECT[area]
 if area=="foundations":return "Introduction","AEIG Foundations and Evidence"
 if area=="capability-recipes":return "Introduction","Capabilities and Examples"
 if area=="research-notes":return "Research & Evidence","Research Notes"
 if area=="archaeology":return "Research & Evidence","History and Architecture Archaeology"
 if area=="observability":return "Research & Evidence","Observation and Instrumentation"
 if area=="troubleshooting":return "Research & Evidence","Troubleshooting / Failure Cases"
 if area=="reference":
  for g,prefixes in REFERENCE.items():
   if any(s in p.stem for s in prefixes):return "Reference",g
  return "Reference","Technical Registries and Tables"
 raise ValueError("Unclassified Markdown document: "+p.as_posix())

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
