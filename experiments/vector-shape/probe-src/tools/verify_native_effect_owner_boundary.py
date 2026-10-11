"""Verify FLT native Effect object interfaces in both pinned AE binaries."""
from pathlib import Path
import json,hashlib,pefile
root=Path(r"D:\Developer\ShapeLayerAE\results")
rtti=json.loads((root/"flt_parade_canonical_rtti_gate_2025_2026.json").read_text())["versions"]
bee=json.loads((root/"effectparade_native_owner_factory_trace_2025_2026.json").read_text())["versions"]
files={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\FLT.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\FLT.dll"}
keynames={
 "effect_interface":"??_7FLT_FCSeqSpec@@6BISequenceSpec@FLTHost@@@",
 "tdb_group_interface":"??_7FLT_FCSeqSpec@@6BTDB_NamedStreamGroup@@@",
 "creator":"?Create@FLT_FCSeqSpec@@","clone":"?CloneStream@FLT_FCSeqSpec@@",
 "read":"?Read@FLT_FCSeqSpec@@","write":"?Write@FLT_FCSeqSpec@@"
}
out={}
for year,filename in files.items():
 data=Path(filename).read_bytes();p=pefile.PE(data=data)
 symbols={e.name.decode(errors="replace"):e.address for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 found={}
 for k,name in keynames.items():
  hits=[hex(rva) for n,rva in symbols.items() if n.startswith(name)]
  assert len(hits)==1,(year,k,hits)
  found[k]=hits[0]
 assert hashlib.sha256(data).hexdigest()==rtti[year]["sha256"]
 constructors=[fn for fn in bee[year]["functions"] if fn["symbol"].startswith("??0BEE_EffectParade@@")]
 assert constructors and all(any("FLT.dll!??0FLT_Parade@@" in call["import"] for call in fn["calls"]) for fn in constructors)
 assert rtti[year]["types"]["destination"]==".?AVFLT_FCSeqSpec@@"
 out[year]={"sha256":rtti[year]["sha256"],"native_interface_evidence":found,
            "bee_effect_parade_forwarding_constructors":len(constructors),
            "canonical_cast_to_flt_seqspec_confirmed":True,
            "third_party_owner_proven":False}
 print("PASS",year,"FLT sequence spec runtime/TDB dual interface and BEE ownership")
dst=root/"native_effect_owner_boundary_crossmodule_2025_2026.json"
dst.write_text(json.dumps({"classification":"static PE crossmodule proof","versions":out},indent=2)+"\n")
print("SAVED",dst)
