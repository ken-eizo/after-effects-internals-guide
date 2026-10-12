"""Recover a few native unnamed Shape schema MatchName literal strings from
actual static BEE constructor call sites. No host calls.
"""
from pathlib import Path
import pefile,struct,json
src=json.load(open(r"D:\Developer\ShapeLayerAE\results\bee_vector_native_layer_contents_allowed_children_2025_2026.json"))["versions"]
paths={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
r={}
for ver,pth in paths.items():
 p=pefile.PE(pth);blob=Path(pth).read_bytes()
 rvas=set()
 for f in src[ver]["three_schema_classes"][:2]:
  for e in f["canonical_children"]:
   rvas.add(int(e["last_matchname_arg"]["matchname_rva"],16))
 names={}
 for target in sorted(rvas):
  hits=[]
  for sect in p.sections:
   if not (sect.Characteristics&0x20000000):continue
   data=sect.get_data();o=0
   while True:
    at=data.find(b"\x48\x8d\x0d",o)
    if at<0:break
    pc=sect.VirtualAddress+at
    dest=pc+7+struct.unpack_from("<i",data,at+3)[0] if at+7<len(data) else -1
    if dest==target and pc<0x65000:
     choices=[]
     for back in range(max(0,at-35),max(0,at-6)):
      if data[back:back+3]!=b"\x48\x8d\x15":continue
      val=sect.VirtualAddress+back+7+struct.unpack_from("<i",data,back+3)[0]
      try:
       b=blob[p.get_offset_from_rva(val):p.get_offset_from_rva(val)+150]
       s=b.split(b"\x00",1)[0].decode("ascii")
      except Exception:s=""
      if s and len(s)<110 and all(32<=ord(c)<127 for c in s):
       choices.append({"rva":hex(val),"text":s,"pc":hex(sect.VirtualAddress+back)})
     hits.append({"site":hex(pc),"literals":choices})
    o=at+1
  names[hex(target)]=hits
  print(ver,hex(target),"refs",len(hits),hits[:4],flush=True)
 r[ver]=names
dest=Path(r"D:\Developer\ShapeLayerAE\results\bee_native_vector_group_schema_matchname_literal_init_2025_2026.json")
dest.write_text(json.dumps({"evidence":"E2-L BEE native static MatchName constructors' data refs; candidate initializer literal scanning only","versions":r},indent=2)+"\n")
print("SAVED",dest)
