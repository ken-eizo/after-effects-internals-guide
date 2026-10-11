"""Compile actual SDK callback bodies, reproduce UB, and verify the repaired path."""
from __future__ import annotations
import argparse
from fractions import Fraction as Q
import json
import math
from pathlib import Path
import random
import shutil
import struct
import subprocess
import repair

HERE = Path(__file__).resolve().parent
WORK = HERE / "workbench"
RESULTS = HERE / "results"
HELPERS = ["Pin32", "RoundDouble", "FindDeepHSL", "RGBtoHSL16", "PutHSLFloat",
           "HSLtoRGBFloat", "RGBtoYIQ", "YIQtoRGBFloat"]
HDR_HELPERS = ["AEIGHdrInputSupported", "AEIGHdrOutputSupported", "AEIGHdrInvertYIQ"]
YIQ_MODES = [11, 12, 13, 14]
HSL_MODES = [6, 7, 8, 9]
A = [[Q(n, 10000) for n in row] for row in
     [[2989,5866,1144],[5959,-2741,-3218],[2113,-5227,3113]]]


def inverse(matrix):
    """Independent exact Gaussian elimination, unlike C++ cofactor implementation."""
    rows = [list(row) + [Q(i == j) for j in range(3)] for i, row in enumerate(matrix)]
    for column in range(3):
        pivot = next(i for i in range(column, 3) if rows[i][column])
        rows[column], rows[pivot] = rows[pivot], rows[column]
        scale = rows[column][column]
        rows[column] = [value/scale for value in rows[column]]
        for i in range(3):
            if i != column:
                factor = rows[i][column]
                rows[i] = [x-factor*y for x,y in zip(rows[i],rows[column])]
    assert [row[:3] for row in rows] == [[Q(i == j) for j in range(3)] for i in range(3)]
    return [row[3:] for row in rows]


INVERSE = inverse(A)


def f32(value):
    return struct.unpack("f", struct.pack("f", float(value)))[0]


def reference(rgb, mode, blend=0):
    values = [Q.from_float(f32(v)) for v in rgb]
    yiq = [sum(x*y for x,y in zip(row,values)) for row in A]
    if mode in (11,12): yiq[0] = 1-yiq[0]
    if mode in (11,13): yiq[1] = -yiq[1]
    if mode in (11,14): yiq[2] = -yiq[2]
    converted = [f32(sum(x*y for x,y in zip(row,yiq))) for row in INVERSE]
    return [f32(Q.from_float(v)+(original-Q.from_float(v))*Q(blend,256))
            for v,original in zip(converted,values)]


def harness_text(source: str) -> str:
    """Accepts original, repaired, or composed source; uses real SDK header types."""
    source = source.replace("\r\n", "\n")
    names = HELPERS + (HDR_HELPERS if "AEIGHdrInputSupported" in source else []) + ["InvertPixelFloat"]
    blocks = [repair.function_text(source, name) for name in names]
    return r'''
#include <iostream>
#include <iomanip>
#include <string>
#include <cstdlib>
#include <cmath>
#include <limits>
#include "SmartyPants.h"
static_assert(sizeof(A_u_short)==2 && sizeof(A_long)==4 && sizeof(PF_FpShort)==4, "SDK ABI widths");
''' + "\n\n".join(blocks) + r'''
int main() {
    int channel, blend;
    std::string r,g,b,a;
    std::cout << std::setprecision(9) << std::scientific;
    while (std::cin >> channel >> blend >> r >> g >> b >> a) {
        SmartyPantsData data{};
        data.channel = channel;
        data.blend = static_cast<A_short>(blend);
        PF_LayerDef world{};
        world.width = 1;
        world.height = 1;
        SmartyPantsDataPlus refcon{};
        refcon.id = &data;
        refcon.outputP = &world;
        PF_PixelFloat input{std::strtof(a.c_str(),nullptr), std::strtof(r.c_str(),nullptr),
                            std::strtof(g.c_str(),nullptr), std::strtof(b.c_str(),nullptr)};
        PF_PixelFloat output{-9,-9,-9,-9};
        PF_Err error = InvertPixelFloat(&refcon, 0, 0, &input, &output);
        std::cout << error << " " << output.alpha << " " << output.red << " "
                  << output.green << " " << output.blue << "\n";
    }
}
'''


def compiler_flags(sdk):
    return ["-std=c++17", "-DMSWindows", "-DWIN32", "-D_WINDOWS"] + [
        "-I"+str(sdk/part) for part in ["Headers","Headers/SP","Headers/Win","Resources","Util","Effect/SmartyPants"]]


def compile_harness(source: str, destination: Path, sdk: Path, *, sanitize=False):
    compiler = shutil.which("clang++")
    if not compiler: raise RuntimeError("clang++ is unavailable")
    source_path = destination.with_suffix(".cpp")
    source_path.write_text(harness_text(source), encoding="utf-8", newline="\n")
    command = [compiler, *compiler_flags(sdk), "-O1", str(source_path), "-o", str(destination)]
    if sanitize: command += ["-fsanitize=float-cast-overflow", "-fno-sanitize-recover=all"]
    run = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    if run.returncode: raise RuntimeError(run.stdout + run.stderr[-600:])
    return {"command":command,"returncode":run.returncode,"warnings":run.stderr.count("warning:"),
            "harness_sha256":repair.sha(source_path.read_bytes())}


def batch(executable, cases, *, allow_failure=False):
    payload = "".join(f"{mode} {blend} {rgb[0]} {rgb[1]} {rgb[2]} {alpha}\n"
                      for mode,blend,rgb,alpha in cases)
    run = subprocess.run([str(executable)],input=payload,capture_output=True,text=True,timeout=60)
    if run.returncode and not allow_failure: raise AssertionError(run.stderr)
    rows = [[float(v) for v in row.split()] for row in run.stdout.splitlines()]
    if not allow_failure: assert len(rows)==len(cases), (len(rows),len(cases),run.stderr)
    return rows,run


def syntax_check(source_path, sdk):
    command = [shutil.which("clang++"), *compiler_flags(sdk), "-fsyntax-only", str(source_path)]
    run = subprocess.run(command,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=120)
    if run.returncode: raise RuntimeError(run.stdout + run.stderr[-600:])
    return {"returncode":0,"warnings":run.stderr.count("warning:"),"command":command,
            "scope":"whole translation unit and actual SDK headers; no link or host execution"}


def run(sdk=repair.DEFAULT_SDK):
    provenance = repair.prepare(sdk)
    RESULTS.mkdir(exist_ok=True)
    original = (WORK/"original.cpp").read_text("utf-8")
    fixed = (WORK/"fixed.cpp").read_text("utf-8")
    builds = {}
    for name,source,sanitizer in [("original",original,False),("original-ubsan",original,True),
                                  ("fixed",fixed,True)]:
        builds[name] = compile_harness(source,WORK/(name+".exe"),sdk,sanitize=sanitizer)
    ub = []
    for mode in (7,11):
        for value in (2.0,-0.25):
            cases=[(mode,0,(value,0.5,0.5),1.0)]
            _,observed = batch(WORK/"original-ubsan.exe",cases,allow_failure=True)
            assert observed.returncode != 0 and "outside the range" in observed.stderr, observed.stderr
            (RESULTS/f"original-ub-{mode}-{value}.log").write_text(observed.stderr,encoding="utf-8")
            ub.append({"mode":mode,"red":value,"returncode":observed.returncode,
                       "diagnostic":observed.stderr.strip()})
    grey_case=[(7,0,(1.5,1.5,1.5),1.0)]
    grey,_=batch(WORK/"original.exe",grey_case)
    rejected,_=batch(WORK/"fixed.exe",grey_case)
    assert grey[0][2] != grey[0][3] and rejected[0][0] != 0

    levels=[0.0,0.1,0.25,0.5,0.9,1.0]
    sdr=[(mode,blend,(r,g,b),0.75) for mode in YIQ_MODES for blend in (0,97,255)
         for r in levels for g in levels for b in levels]
    old,_=batch(WORK/"original.exe",sdr)
    new,_=batch(WORK/"fixed.exe",sdr)
    max_difference=0.0
    max_reference_error=0.0
    for case,legacy,repaired in zip(sdr,old,new):
        mode,blend,rgb,alpha=case
        assert repaired[0]==0 and repaired[1]==alpha
        expected=reference(rgb,mode,blend)
        max_difference=max(max_difference,max(abs(x-y) for x,y in zip(legacy[2:],repaired[2:])))
        error=max(abs(x-y) for x,y in zip(expected,repaired[2:]))
        max_reference_error=max(max_reference_error,error)
        assert error <= 4e-7*max(1,*map(abs,expected)), (case,expected,repaired)

    rng=random.Random(20260922)
    hdr=[(mode,blend,tuple(f32(rng.uniform(-16,32)) for _ in range(3)),0.625)
         for mode in YIQ_MODES for blend in (0,128,255) for _ in range(100)]
    maximum=f32(3.4028234663852886e38)
    limit=f32(maximum/32)
    hdr += [(mode,blend,(r,g,b),1.0) for mode in YIQ_MODES for blend in (0,128,255)
            for r,g,b in [(limit,-limit,limit),(-limit,limit,-limit),(2,-0.25,8)]]
    output,_=batch(WORK/"fixed.exe",hdr)
    max_hdr_relative_error=0.0
    for case,observed in zip(hdr,output):
        mode,blend,rgb,alpha=case
        assert observed[0]==0 and observed[1]==alpha and all(map(math.isfinite,observed[1:]))
        expected=reference(rgb,mode,blend)
        error=max(abs(x-y) for x,y in zip(expected,observed[2:]))/max(1,*map(abs,expected))
        max_hdr_relative_error=max(max_hdr_relative_error,error)
        assert error < 8e-7, (case,expected,observed)
    invalid=[(mode,0,(value,0.5,0.5),1.0)
             for mode in YIQ_MODES+HSL_MODES
             for value in ("nan","inf","-inf",maximum)]
    invalid += [(mode,0,(value,0.5,0.5),1.0) for mode in HSL_MODES for value in (-0.25,1.5,2)]
    invalid_output,_=batch(WORK/"fixed.exe",invalid)
    assert all(row[0]!=0 for row in invalid_output)
    hsl_sdr=[(mode,0,(r,g,b),0.5) for mode in HSL_MODES
             for r in levels for g in levels for b in levels]
    hsl_old,_=batch(WORK/"original.exe",hsl_sdr)
    hsl_new,_=batch(WORK/"fixed.exe",hsl_sdr)
    assert hsl_old==hsl_new

    # Existing sample interpolation overflows at finite HDR inputs before /256.
    blend_case=[(1,128,(limit,limit,limit),1.0)]
    blend_old,_=batch(WORK/"original.exe",blend_case)
    blend_new,_=batch(WORK/"fixed.exe",blend_case)
    assert any(not math.isfinite(x) for x in blend_old[0][2:])
    assert all(math.isfinite(x) for x in blend_new[0][1:])
    syntax={name:syntax_check(WORK/(name+".cpp"),sdk) for name in ("original","fixed")}
    assert repair.sha((sdk/repair.SOURCE).read_bytes())==provenance["source_sha256"]
    report={"provenance":provenance,"builds":builds,"original_ub":ub,
            "original_hdr_gray_hue":grey[0],"repaired_hdr_gray_hue":rejected[0],
            "sdr_yiq_cases":len(sdr),"sdr_max_abs_compatibility_difference":max_difference,
            "sdr_max_abs_rational_reference_error":max_reference_error,
            "hdr_yiq_cases":len(hdr),"hdr_max_scaled_rational_reference_error":max_hdr_relative_error,
            "domain_rejections":len(invalid),"legacy_hsl_sdr_exact_match_cases":len(hsl_sdr),
            "original_float_blend_overflow":str(blend_old[0]),
            "repaired_float_blend":blend_new[0],
            "inverse_rational":[[str(value) for value in row] for row in INVERSE],
            "syntax":syntax,"ae_host_execution":False}
    (RESULTS/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("builds","original_ub","syntax","inverse_rational")},indent=2))
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk",type=Path,default=repair.DEFAULT_SDK)
    run(parser.parse_args().sdk)
