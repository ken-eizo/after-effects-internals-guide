"""Disassembly-only discovery probe for AE 2025 BEE.dll.
Do not load/call private exports and do not modify installed AE binaries.
"""
from pathlib import Path
from hashlib import sha256
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

binary = Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll")
output = Path(__file__).resolve().parents[1] / "results" / "bee_private_surface_probe.json"
if not binary.is_file():
    raise SystemExit(f"Missing distributed runtime artifact: {binary}")
raw = binary.read_bytes()
pe = pefile.PE(data=raw, fast_load=False)
image_base = pe.OPTIONAL_HEADER.ImageBase
# Use dumpbin-derived export entries from AEIG because pefile may report
# long MSVC decorated export names as None even when dumpbin resolves them.
import csv
import re
catalog = Path(r"D:\Developer\After Effects Internals Guide\datasets\ae-2025-vector-shape-symbols.csv")
symbols = []
with catalog.open(encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        if row["module"] != "BEE.dll" or row["relation"] != "export":
            continue
        line = row["entry"]
        if not any(token in line for token in ("TDB_StreamFactory", "BEE_GenericShapeStream",
                                               "PopulateVectorArt", "Rasterize2DGraph",
                                               "C_AGMDLTranslatePort")):
            continue
        m = re.match(r"\s*(\d+)\s+[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s+(\S+)", line)
        if not m:
            continue
        symbols.append({"name": m.group(3), "rva": int(m.group(2), 16),
                        "ordinal": int(m.group(1)), "source": "AEIG dumpbin export inventory"})
targets = [
    s for s in symbols if (
        "??0BEE_GenericShapeStream@@" in s["name"]
        or "PopulateVectorArt" in s["name"]
        or "Rasterize2DGraph" in s["name"]
    )
]
decoder = Cs(CS_ARCH_X86, CS_MODE_64)
snippets = []
for s in targets[:12]:
    try:
        offset = pe.get_offset_from_rva(s["rva"])
    except Exception:
        continue
    code = raw[offset:offset+512]
    asm = []
    for index, inst in enumerate(decoder.disasm(code, image_base+s["rva"])):
        if index >= 80:
            break
        asm.append(f"{inst.address:016X} {inst.mnemonic} {inst.op_str}")
        if inst.mnemonic in ("ret", "retf"):
            break
    snippets.append({"symbol": s["name"], "rva": hex(s["rva"]),
                     "note": "first basic instructions only; no causal trace, ABI or safe-call claim",
                     "disassembly": asm})
result = {
    "title": "BEE shape stream factory and renderer static discovery",
    "research_kind": "E2-L; static PE export + raw x64 disassembly",
    "binary_path": str(binary),
    "binary_sha256": sha256(raw).hexdigest(),
    "binary_size": len(raw),
    "export_count": len(pe.DIRECTORY_ENTRY_EXPORT.symbols),
    "filtered_symbol_count": len(symbols),
    "matched_symbols": symbols,
    "sampled_disassembly": snippets,
    "interpretation": "An exported constructor accepts a TDB_StreamFactory* pointer; registration interface and external plug-in ownership not established.",
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Source:", binary, "SHA:", result["binary_sha256"])
print("Exports:", result["export_count"], "selected:", len(symbols))
for s in symbols:
    if "BEE_GenericShapeStream" in s["name"] and "??0" in s["name"]:
        print("Constructor:", hex(s["rva"]), s["name"])
print("Disassemblies:", len(snippets), "Output:", output)
