"""Reviewable SmartyPants float-domain repair; never edits the installed SDK."""
from __future__ import annotations
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
DEFAULT_SDK = Path(r"E:\ae25.6_61.64bit.AfterEffectsSDK\Examples")
SOURCE = Path("Effect/SmartyPants/SmartyPants.cpp")


def function_span(text: str, name: str) -> tuple[int, int]:
    matches = list(re.finditer(r"^" + re.escape(name) + r"\s*\(", text, re.M))
    if len(matches) != 1:
        raise ValueError(f"expected one definition of {name}")
    hit = matches[0].start()
    start = text.rfind("static", 0, hit)
    opening = text.index("{", hit)
    depth = 1
    cursor = opening + 1
    while depth:
        depth += (text[cursor] == "{") - (text[cursor] == "}")
        cursor += 1
    return start, cursor


def function_text(text: str, name: str) -> str:
    start, end = function_span(text, name)
    return text[start:end]


def once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError("patch preimage missing or ambiguous: " + old[:80])
    return text.replace(old, new, 1)


def patch_text(source: str) -> str:
    """Side-effect-free source transformation; accepts other labs' disjoint edits."""
    source = source.replace("\r\n", "\n")
    if "AEIGHdrInputSupported" in source:
        raise ValueError("HDR repair is already present")
    source = once(source, '#include "SmartyPants.h"',
                  '#include "SmartyPants.h"\n#include <cmath>\n#include <limits>')
    start, end = function_span(source, "InvertPixelFloat")
    callback = source[start:end]
    callback = once(callback, "\tSmartyPantsData\t\t*id\t\t= idp->id;",
                    "\tSmartyPantsData\t\t*id\t\t= idp->id;\n"
                    "\tif (id->blend < 0 || id->blend > 256) return PF_Err_BAD_CALLBACK_PARAM;")
    callback = once(callback, "\t\tA_FpLong\t\t\t\t\tyF, iF, qF;",
                    "\t\tif (!AEIGHdrInputSupported(*in)) return PF_Err_BAD_CALLBACK_PARAM;")
    hsl_call = "RGBtoHSL16((A_u_short)(32768.0 * in->red), (A_u_short)(32768.0 * in->green), (A_u_short)(32768.0 * in->blue), &hueL, &satL, &lightL);"
    callback = once(callback, hsl_call,
                    "// Legacy HSL has a bounded [0,1] RGB domain; reject unsupported HDR.\n"
                    "\t\t\t\tif (in->red < 0 || in->red > 1 || in->green < 0 || in->green > 1 ||\n"
                    "\t\t\t\t    in->blue < 0 || in->blue > 1) return PF_Err_BAD_CALLBACK_PARAM;\n"
                    "\t\t\t\t" + hsl_call)
    begin = callback.index("\t\t\tcase Channel_YIQ:")
    finish = callback.index("\n\t\t\tdefault:", begin)
    callback = callback[:begin] + """\t\t\tcase Channel_YIQ:
\t\t\tcase Channel_LUMINANCE:
\t\t\tcase Channel_IN_PHASE_CHROMINANCE:
\t\t\tcase Channel_QUADRATURE_CHROMINANCE:
\t\t\t\tif (AEIGHdrInvertYIQ(*in, *out, id->channel) != PF_Err_NONE)
\t\t\t\t\treturn PF_Err_BAD_CALLBACK_PARAM;
\t\t\t\tbreak;
""" + callback[finish:]
    begin = callback.index("\t\tif (id->blend && (id->channel != Channel_ALPHA))")
    finish = callback.index("\n\t\t++in;", begin)
    callback = callback[:begin] + """\t\tif (id->blend && (id->channel != Channel_ALPHA)) {
\t\t\t// Widen before subtraction/multiplication to avoid float intermediate overflow.
\t\t\tconst double t = id->blend / 256.0;
\t\t\tconst double r = double(out->red) + (double(in->red) - double(out->red)) * t;
\t\t\tconst double g = double(out->green) + (double(in->green) - double(out->green)) * t;
\t\t\tconst double b = double(out->blue) + (double(in->blue) - double(out->blue)) * t;
\t\t\tif (!AEIGHdrOutputSupported(r, g, b)) return PF_Err_BAD_CALLBACK_PARAM;
\t\t\tout->red = static_cast<PF_FpShort>(r);
\t\t\tout->green = static_cast<PF_FpShort>(g);
\t\t\tout->blue = static_cast<PF_FpShort>(b);
\t\t}
""" + callback[finish:]
    helpers = (HERE / "hdr_helpers.inc").read_text("utf-8")
    return source[:start] + helpers + "\n\n" + callback + source[end:]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prepare(sdk: Path = DEFAULT_SDK) -> dict:
    original = (sdk / SOURCE).read_bytes()
    text = original.decode("utf-8").replace("\r\n", "\n")
    fixed = patch_text(text)
    work = HERE / "workbench"
    work.mkdir(exist_ok=True)
    for name, payload in [("original.cpp", text), ("fixed.cpp", fixed)]:
        (work / name).write_text(payload, encoding="utf-8", newline="\n")
    patch = "".join(difflib.unified_diff(text.splitlines(True), fixed.splitlines(True),
                                      fromfile="a/Effect/SmartyPants/SmartyPants.cpp",
                                      tofile="b/Effect/SmartyPants/SmartyPants.cpp"))
    (HERE / "SmartyPants-hdr.patch").write_text(patch, encoding="utf-8", newline="\n")
    record = {"source": str((sdk / SOURCE).resolve()), "source_sha256": sha(original),
              "normalized_original_sha256": sha(text.encode()), "fixed_sha256": sha(fixed.encode()),
              "scope": "copied SDK source; installed SDK unchanged"}
    (work / "provenance.json").write_text(json.dumps(record, indent=2) + "\n")
    if sha((sdk / SOURCE).read_bytes()) != record["source_sha256"]:
        raise ValueError("source changed during preparation")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path, default=DEFAULT_SDK)
    print(json.dumps(prepare(parser.parse_args().sdk), indent=2))
