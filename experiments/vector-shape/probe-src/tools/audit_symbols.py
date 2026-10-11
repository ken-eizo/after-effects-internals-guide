"""Reproducible E2-L static inventory. Presence != ABI contract or causal call chain."""
import csv
import hashlib
import json
from pathlib import Path

src = Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-2025-vector-shape-symbols.csv")
out = Path(__file__).resolve().parents[1] / "results" / "static_symbol_audit.json"
patterns = {
    "factory": ["TDB_StreamFactory", "TDB_MatchName", "BEE_GenericShapeStream"],
    "vector_stream": ["BEE_VectorStream", "PopulateVectorArt"],
    "vector_art": ["BEE_VectorArt", "OriginInfo", "GetBounds"],
    "raster_graph": ["Rasterize2DGraph", "RG_RenderNode", "C_AGMDLTranslatePort"],
    "agm_bridge": ["CAGMPath", "COR_NewAGMPort", "COR_PlayOutlines", "AdobeSVGAGM"],
}
rows = list(csv.DictReader(src.open(encoding="utf-8-sig", newline="")))
groups = {}
for category, names in patterns.items():
    group = {}
    for needle in names:
        hits = [r for r in rows if needle.lower() in r["entry"].lower()]
        group[needle] = {
            "count": len(hits),
            "modules": sorted({r["module"] for r in hits}),
            "examples": [dict(r) for r in hits[:6]],
        }
    groups[category] = group
record = {
    "experiment_id": "EXP-SHAPE-003",
    "evidence": "E2-L (static module inventory only)",
    "conclusion": "Symbols observed only. No code execution or new stream registration is proven.",
    "source": str(src),
    "source_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
    "row_count": len(rows),
    "patterns": groups,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"{out} : {len(rows)} source rows")
for k, val in groups.items():
    print(k, " ".join(f"{n}={v['count']}" for n, v in val.items()))
