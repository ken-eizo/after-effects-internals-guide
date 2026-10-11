"""Offline BEE vector owner startup chain witness, two pinned installed files.
Does not load BEE or mutate AE; validates exact direct entry control flow.
"""
from pathlib import Path
import pefile,hashlib,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
cfg={
"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x6e4100,0x76b6f0,0x77c630,0x6eef40,0x6fdcc0),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x708a30,0x78cf60,0x79d040,0x713550,0x7217c0)}
out={}
for year,(path,entry,wrapper,first,second,tail) in cfg.items():
 p=pefile.PE(path);data=Path(path).read_bytes();base=p.OPTIONAL_HEADER.ImageBase
 dis=Cs(CS_ARCH_X86,CS_MODE_64)
 def take(rva,n):
  off=p.get_offset_from_rva(rva)
  return list(dis.disasm(data[off:off+n],base+rva))
 thunk=take(entry,5)
 assert len(thunk)==1 and thunk[0].mnemonic=="jmp"
 assert int(thunk[0].op_str,16)-base==wrapper
 ops=take(wrapper,25)
 calls=[int(x.op_str,16)-base for x in ops if x.mnemonic=="call"]
 jumps=[int(x.op_str,16)-base for x in ops if x.mnemonic=="jmp"]
 assert calls==[first,second],(year,calls)
 assert jumps==[tail],(year,jumps)
 assert any(x.mnemonic=="mov" and x.op_str=="cl, 1" for x in ops)
 out[year]={"BEE_sha256":hashlib.sha256(data).hexdigest(),"entry":hex(entry),
 "wrapper":hex(wrapper),"first_call":hex(first),"evaluator_registry_init":hex(second),
 "final_tail_call":hex(tail),"instructions":[{"rva":hex(x.address-base),"op":x.mnemonic,"args":x.op_str} for x in ops]}
 print("PASS",year,"vector RegisterStreams wrapper and BEE evaluator init",flush=True)
dest=Path(r"D:\Developer\ShapeLayerAE\results\bee_vector_registerstreams_startup_chain_2025_2026.json")
dest.write_text(json.dumps({"evidence":"E2-L code-entry control flow only; not external registration permission","versions":out},indent=2)+"\n",encoding="utf8")
print("SAVED",dest)
