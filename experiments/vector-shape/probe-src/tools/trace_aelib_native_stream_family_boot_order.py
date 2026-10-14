"""Cross-DLL native Adobe OM / FLT / BEE Birth and Death caller ordering.
Reads only installed original aelib.dll 2025/2026; direct IAT CALL with x64
instruction-boundary + .pdata function containment. No private host execution.
"""
from pathlib import Path
import pefile,capstone,subprocess,re,bisect,struct,json,hashlib,collections
ROOTS={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files"),
       "2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files")}
WANTED=("?BEE_Birth@@","?BEE_Death@@","?FLT_Birth@@","?FLT_Death@@","?OM_Birth@@","?OM_Death@@")
allout={}
for year,root in ROOTS.items():
 path=root/"aelib.dll";pe=pefile.PE(str(path));base=pe.OPTIONAL_HEADER.ImageBase
 imp={i.address-base:(d.dll.decode(errors="replace"),i.name.decode(errors="replace") if i.name else "")
      for d in pe.DIRECTORY_ENTRY_IMPORT for i in d.imports}
 expected={rva:(dll,name) for rva,(dll,name) in imp.items() if any(name.startswith(w) for w in WANTED)}
 assert len(expected)==6,(year,expected)
 pdata=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in pe.DIRECTORY_ENTRY_EXCEPTION)
 starts=[x[0] for x in pdata]
 cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);cs.detail=True
 groups=collections.defaultdict(list)
 for section in pe.sections:
  if not section.Characteristics&0x20000000:continue
  blob=section.get_data();idx=blob.find(b"\xff\x15")
  while idx>=0 and idx+6<=len(blob):
   rva=section.VirtualAddress+idx
   to=rva+6+struct.unpack("<i",blob[idx+2:idx+6])[0]
   if to in expected:
    j=bisect.bisect_right(starts,rva)-1
    fun=pdata[j] if j>=0 and pdata[j][0]<=rva<pdata[j][1] else None
    if fun is not None:
     insns=list(cs.disasm(pe.get_data(fun[0],fun[1]-fun[0]),base+fun[0]))
     hit=[x for x in insns if x.address-base==rva]
     if len(hit)==1 and hit[0].mnemonic=="call" and hit[0].size==6:
      dll,name=expected[to]
      groups[hex(fun[0])].append({"call_rva":hex(rva),"import_symbol":name,"import_from":dll,"import_iat_rva":hex(to)})
   idx=blob.find(b"\xff\x15",idx+1)
 print("==",year,"aelib Birth/Death cross-DLL direct callsites",sum(map(len,groups.values())),"functions",len(groups))
 for fn,items in sorted(groups.items(),key=lambda x:int(x[0],16)):
  print("FUNC",fn,len(items))
  for x in sorted(items,key=lambda x:int(x["call_rva"],16)):
   print(" ",x["call_rva"],x["import_symbol"].split("@@",1)[0])
 assert any(x["import_symbol"].startswith("?BEE_Birth") for a in groups.values() for x in a)
 assert any(x["import_symbol"].startswith("?FLT_Birth") for a in groups.values() for x in a)
 assert any(x["import_symbol"].startswith("?OM_Birth") for a in groups.values() for x in a)
 allout[year]={"aelib_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"import_iat":{hex(r):{"dll":v[0],"name":v[1]} for r,v in expected.items()},"callers":dict(groups)}
out=Path(__file__).resolve().parents[4]/"datasets"/"ae-aelib-om-flt-bee-native-birth-death-2025-2026.json"
out.write_text(json.dumps(allout,indent=2)+"\n",encoding="utf-8")
print("PASS",out)
