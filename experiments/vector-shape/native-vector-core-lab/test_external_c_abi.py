"""Cross-module, non-MSVC C ABI smoke test for the actual built Windows x64 DLL.
No Adobe runtime, AEGP, Shape layer, Mask or PF_World used.
"""
import ctypes as c
import os
from pathlib import Path
p=Path(os.environ.get("CNL_NATIVE_VECTOR_CORE_DLL",
      str(Path(__file__).resolve().parent/"build"/"Release"/"CNLNativeVectorCore.dll")))
if not p.exists():
 p=Path(r"D:\Developer\ShapeLayerAE\build\native_vector_core\Release\CNLNativeVectorCore.dll")
dll=c.CDLL(str(p))
u64=c.c_uint64;u32=c.c_uint32;sz=c.c_size_t;ptr=c.c_void_p
class Cubic(c.Structure):
 _fields_=[(k,c.c_double) for k in ("x0","y0","x1","y1","x2","y2","x3","y3")]
dll.cnl_document_create.restype=ptr
dll.cnl_document_destroy.argtypes=[ptr]
dll.cnl_document_add_group.argtypes=[ptr,u64,c.c_char_p,c.POINTER(u64)]
dll.cnl_document_add_ellipse.argtypes=[ptr,u64,c.c_char_p,c.c_double,c.c_double,c.c_double,c.c_double,c.POINTER(u64)]
dll.cnl_document_copy_cubics.argtypes=[ptr,u64,c.POINTER(Cubic),c.POINTER(u32)]
dll.cnl_document_serialize.argtypes=[ptr,ptr,c.POINTER(sz)]
dll.cnl_document_deserialize.argtypes=[ptr,sz,c.POINTER(ptr)]
dll.cnl_document_get_child_count.argtypes=[ptr,u64,c.POINTER(u32)]
assert p.exists()
doc=dll.cnl_document_create()
assert doc
try:
 group=u64()
 assert dll.cnl_document_add_group(doc,1,b"Procedural Contents",c.byref(group))==0
 path=u64()
 assert dll.cnl_document_add_ellipse(doc,group.value,b"Code Ellipse",10,25,80,30,c.byref(path))==0
 count=u32()
 assert dll.cnl_document_copy_cubics(doc,path.value,None,c.byref(count))==5
 assert count.value==4
 shapes=(Cubic*count.value)()
 assert dll.cnl_document_copy_cubics(doc,path.value,shapes,c.byref(count))==0
 assert abs(shapes[0].x0-90)<1e-12
 assert abs(shapes[0].x3-10)<1e-12
 assert abs(shapes[0].y3-55)<1e-12
 size=sz()
 assert dll.cnl_document_serialize(doc,None,c.byref(size))==5
 buffer=c.create_string_buffer(size.value)
 assert dll.cnl_document_serialize(doc,buffer,c.byref(size))==0
 restored=ptr()
 assert dll.cnl_document_deserialize(buffer,size.value,c.byref(restored))==0
 try:
  nc=u32()
  assert dll.cnl_document_get_child_count(restored,group.value,c.byref(nc))==0
  assert nc.value==1
  print("PASS Python ctypes -> actual CNLNativeVectorCore.dll; 64-bit IDs; compiled ellipse 4 Beziers; C ABI archive roundtrip; bytes",size.value,"library",p)
 finally:dll.cnl_document_destroy(restored)
finally:dll.cnl_document_destroy(doc)
