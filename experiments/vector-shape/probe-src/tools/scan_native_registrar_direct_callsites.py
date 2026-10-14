"""Independent PE/x64 direct-import callsite scan of Adobe's native stream registrars.
Uses actual IAT-displacement instructions + unwind function boundaries; read-only.
Distinguishes true CALLs from JMP thunks. No live private API calls.
"""
from pathlib import Path
import pefile,capstone,struct,re,json,hashlib,bisect,subprocess
ROOTS={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files"),
       "2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files")}
TARGETS={
 "?RegisterFactoryFunc@TDB_StreamFactory@@":"TDB_StreamFactory::RegisterFactoryFunc",
 "?UnregisterFactoryFunc@TDB_StreamFactory@@":"TDB_StreamFactory::UnregisterFactoryFunc",
 "?Register@TDB_ScRegisterStreams@@":"TDB_ScRegisterStreams::Register",
 "?UnregisterAll@TDB_ScRegisterStreams@@":"TDB_ScRegisterStreams::UnregisterAll"
}
MODULES=("BEE.dll","FLT.dll","OM.dll","aelib.dll")
out={}
for version,root in ROOTS.items():
 verout={}
 for filename in MODULES:
  path=root/filename;raw=path.read_bytes();pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
  mem=pefile.PE(str(path),fast_load=True)
  # Force import parsing
  mem.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
  its={i.address-base:(d.dll.decode(errors="replace"),i.name.decode(errors="replace") if i.name else "")
       for d in getattr(mem,"DIRECTORY_ENTRY_IMPORT",[]) for i in d.imports}
  regiat={i:{"module":d[0],"symbol":d[1],"category":label}
          for i,d in its.items() for sym,label in TARGETS.items()
          if d[0].lower()=="tdb.dll" and d[1].startswith(sym)}
  exp=subprocess.run(["dumpbin","/exports",str(path)],text=True,errors="replace",capture_output=True,check=True).stdout
  names={}
  for line in exp.splitlines():
   m=re.match(r"\s*\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\S+)",line)
   if m:names[int(m.group(1),16)]=m.group(2)
  pdata=sorted((r.struct.BeginAddress,r.struct.EndAddress) for r in pe.DIRECTORY_ENTRY_EXCEPTION)
  starts=[a for a,b in pdata];cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);cs.detail=True
  calls=[]
  for section in pe.sections:
   if not section.Characteristics & 0x20000000:continue
   blob=section.get_data()
   positions=[]
   for candidate in (b"\xff\x15",b"\xff\x25"):
    at=blob.find(candidate)
    while at>=0:
     positions.append(at)
     at=blob.find(candidate,at+1)
   for offset in sorted(set(positions)):
    if offset+6>len(blob):continue
    op=blob[offset:offset+2]
    rva=section.VirtualAddress+offset
    disp=struct.unpack("<i",blob[offset+2:offset+6])[0]
    iat_rva=rva+6+disp
    if iat_rva not in regiat:continue
    j=bisect.bisect_right(starts,rva)-1
    fun=pdata[j] if j>=0 and pdata[j][0]<=rva<pdata[j][1] else None
    instruction_boundary=False
    if fun and 0<fun[1]-fun[0]<250000:
     for i in cs.disasm(pe.get_data(fun[0],fun[1]-fun[0]),base+fun[0]):
      if i.address-base==rva and i.size==6 and i.mnemonic==("call" if op==b"\xff\x15" else "jmp"):
       instruction_boundary=True
       break
      if i.address-base>rva:break
    calls.append({"rva":hex(rva),"kind":"CALL" if op==b"\xff\x15" else "JMP_IMPORT_THUNK",
                  "import":regiat[iat_rva]["symbol"],"category":regiat[iat_rva]["category"],
                  "function_start":hex(fun[0]) if fun else None,
                  "function_export":names.get(fun[0],"") if fun else "",
                  "instruction_verified":instruction_boundary})
  verout[filename]={"sha256":hashlib.sha256(raw).hexdigest(),
                    "registrar_iat":{hex(k):v for k,v in regiat.items()},
                    "verified_calls":calls}
  print(version,filename,"regiat",len(regiat),"active calls",sum(x["kind"]=="CALL" and x["instruction_verified"] for x in calls),
        "import thunks",sum(x["kind"]!="CALL" for x in calls),flush=True)
  for c in calls[:90]:
   if c["instruction_verified"]:
    print(" ",c["rva"],c["kind"],c["category"],"parent",c["function_start"],c["function_export"][:100],flush=True)
 out[version]=verout
outp=Path(__file__).resolve().parents[4]/"datasets"/"ae-native-tdb-registrar-direct-callsites-2025-2026.json"
outp.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print("PASS",outp,flush=True)
