"""Pinned-source PreRender dependency/publication laboratory. No AE host execution."""
from __future__ import annotations
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
WORK = HERE / "workbench"
SDK_DEFAULT = Path("E:/ae25.6_61.64bit.AfterEffectsSDK/Examples")
LOCK = {
    "Effect/SmartyPants/SmartyPants.cpp": "4865f3d8db8de37f5109cb34fdf04b7ae8f5b5582f12f490baa67f7f179104c2",
    "Effect/SmartyPants/SmartyPants.h": "842b1fd4f3366ce456b3b7a0e6ec9edf032aef08f90cf9d06b21dc4e83c4f654",
    "Headers/AE_Effect.h": "215d07b840ef2c731d2394f00edad40d05cc23ec33d0a001b19a1468cf662faf",
    "Headers/AE_GeneralPlug.h": "df4e0cce90f910e06e04018e16bcf8a796099283fee5ba9d0261709e0888691a",
    "Util/Smart_Utils.cpp": "860aaaa6b9fd6448ea3bf9b5b6a1c687519cfe66150715fa0fd8da7ad0990c8c",
}
SOURCE = "Effect/SmartyPants/SmartyPants.cpp"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def function(source, name, return_type="PF_Err"):
    pattern = r"(?:static\s+)?" + return_type + r"\s+" + name + r"\s*\("
    matches = list(re.finditer(pattern, source))
    if len(matches) != 1:
        raise ValueError(f"ambiguous function {name}")
    start = matches[0].start()
    cursor = source.index("{", matches[0].end()) + 1
    depth = 1
    while depth:
        depth += (source[cursor] == "{") - (source[cursor] == "}")
        cursor += 1
    return source[start:cursor]


def repair(source):
    old = function(source, "PreRender")
    result = old
    replacements = [
        ("PF_CheckoutResult in_result;", "PF_CheckoutResult in_result = {};"),
        ("AEGP_LayerH\t\tlayerH;", "AEGP_LayerH\t\tlayerH = NULL;"),
        ("AEGP_CompH\t\tcompH;", "AEGP_CompH\t\tcompH = NULL;"),
        ("AEGP_ColorVal\tbg_color;", "AEGP_ColorVal\tbg_color = {};"),
        ("PFInterfaceSuite->AEGP_GetEffectLayer(in_data->effect_ref, &layerH);",
         "ERR(PFInterfaceSuite->AEGP_GetEffectLayer(in_data->effect_ref, &layerH));"),
        ("layerSuite->AEGP_GetLayerParentComp(layerH, &compH);",
         "ERR(layerSuite->AEGP_GetLayerParentComp(layerH, &compH));"),
        ("compSuite->AEGP_GetCompBGColor(compH, &bg_color);",
         "ERR(compSuite->AEGP_GetCompBGColor(compH, &bg_color));"),
        ("extra->cb->GuidMixInPtr(in_data->effect_ref, sizeof(bg_color), reinterpret_cast<void *>(&bg_color));",
         "ERR(extra->cb->GuidMixInPtr(in_data->effect_ref, sizeof(bg_color), reinterpret_cast<void *>(&bg_color)));"),
        ("if (channel_param.u.pd.value == Channel_ALPHA){",
         "if (!err && (channel_param.u.pd.value == Channel_ALPHA)){"),
        ("UnionLRect(&in_result.result_rect, \t\t&extra->output->result_rect);\n\tUnionLRect(&in_result.max_result_rect, \t&extra->output->max_result_rect);",
         "if (!err) {\n\t\tUnionLRect(&in_result.result_rect, \t\t&extra->output->result_rect);\n\t\tUnionLRect(&in_result.max_result_rect, \t&extra->output->max_result_rect);\n\t}")
    ]
    for before, after in replacements:
        if result.count(before) != 1:
            raise ValueError(f"missing exact patch preimage: {before}")
        result = result.replace(before, after, 1)
    return source.replace(old, result, 1)


def write_safe(path, data):
    if not path.resolve().is_relative_to(HERE.resolve()):
        raise ValueError("destination outside owned package")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f"refusing to overwrite changed artifact: {path}")
    path.write_bytes(data)


def harness_for_source(source: str, sdk: Path = SDK_DEFAULT) -> str:
    """Generate the same failure-injection harness for a composed source overlay.
    Supporting SDK headers/helper remain hash checked; the supplied source may
    include other separately verified patches. This function performs no writes.
    """
    for name in ["Effect/SmartyPants/SmartyPants.h", "Util/Smart_Utils.cpp"]:
        if sha((sdk / name).read_bytes()) != LOCK[name]:
            raise ValueError(f"supporting source changed: {name}")
    header = (sdk / "Effect/SmartyPants/SmartyPants.h").read_text()
    helper = (sdk / "Util/Smart_Utils.cpp").read_text()
    enum = re.search(r"enum\s*\{\s*Channel_RGB\s*=\s*1,.*?Channel_ALPHA\s*\};",
                     header, re.S).group()
    util = function(helper, "IsEmptyRect", "PF_Boolean") + "\n" + function(helper, "UnionLRect", "void")
    util = util.replace("UnionLRect(", "SDK_UnionLRect(")
    return ((HERE / "harness.cpp.in").read_text()
            .replace("// EXTRACTED_ENUM", enum)
            .replace("// EXTRACTED_UTIL", util)
            .replace("// EXTRACTED_PRERENDER", function(source, "PreRender")))


def run(sdk, compiler):
    sources = {}
    for name, digest in LOCK.items():
        data = (sdk / name).read_bytes()
        if sha(data) != digest:
            raise ValueError(f"source identity changed: {name}")
        sources[name] = data
    # Normalise newline only inside this managed copy; record both raw and normalized hashes.
    original = sources[SOURCE].decode().replace("\r\n", "\n")
    fixed = repair(original)
    header = sources["Effect/SmartyPants/SmartyPants.h"]
    for variant, text in [("original", original), ("fixed", fixed)]:
        write_safe(WORK / variant / "SmartyPants.cpp", text.encode())
        write_safe(WORK / variant / "SmartyPants.h", header)
    patch = "".join(difflib.unified_diff(original.splitlines(True), fixed.splitlines(True),
                                        fromfile="a/SmartyPants.cpp", tofile="b/SmartyPants.cpp"))
    write_safe(HERE / "SmartyPants-prerender.patch", patch.encode())
    includes = ["-I" + str(sdk / sub) for sub in
                ["Headers", "Headers/SP", "Headers/Win", "Resources", "Util", "Effect/SmartyPants"]]
    reports = {}
    for variant, source in [("original", original), ("fixed", fixed)]:
        generated = harness_for_source(source, sdk)
        cpp = WORK / (variant + "-" + sha(generated.encode())[:12] + "-harness.cpp")
        write_safe(cpp, generated.encode())
        exe = cpp.with_suffix(".exe")
        command = [compiler, "-std=c++17", "-O1", "-g", "-DMSWindows", "-DWIN32", "-D_WINDOWS",
                   "-Wno-pragma-pack", "-Wno-microsoft-include", str(cpp), *includes, "-o", str(exe)]
        build = subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace", timeout=120)
        if build.returncode:
            raise ValueError(build.stderr)
        process = subprocess.run([str(exe)], capture_output=True, encoding="utf-8", errors="replace", timeout=60)
        if process.returncode:
            raise ValueError(process.stderr)
        report = json.loads(process.stdout)
        whole_command = [compiler, "-std=c++17", "-fsyntax-only", "-DMSWindows", "-DWIN32", "-D_WINDOWS",
                         str(WORK / variant / "SmartyPants.cpp"), *includes]
        whole = subprocess.run(whole_command, capture_output=True, encoding="utf-8", errors="replace", timeout=120)
        if whole.returncode:
            raise ValueError(whole.stderr)
        report.update({
            "source_sha256": sha(source.encode()), "harness_sha256": sha(generated.encode()),
            "build_command": command, "whole_file_syntax_command": whole_command,
            "whole_file_syntax_returncode": whole.returncode,
            "whole_file_warning_count": whole.stderr.count("warning:"),
        })
        reports[variant] = report
    if reports["original"]["false_successes"] == 0 or reports["original"]["invalid_result_reads"] == 0:
        raise ValueError("original counterexample was not reproduced")
    required_zero = ["return_errors", "trace_errors", "publication_errors", "request_errors",
                     "invalid_result_reads", "false_successes"]
    if any(reports["fixed"][key] != 0 for key in required_zero):
        raise ValueError("fixed contract regression failed")
    version = subprocess.run([compiler, "--version"], capture_output=True, encoding="utf-8", errors="replace", timeout=20)
    result = {
        "issue": "SmartFX dependency failure propagation and success-gated metadata publication",
        "compiler_version": version.stdout.splitlines()[0], "source_lock": LOCK,
        "scope": "actual SDK callback types and macros; extracted complete PreRender; suite acquisition mocked; no AE host",
        "results": reports,
        "source_unchanged_after": all(sha((sdk/name).read_bytes()) == digest for name,digest in LOCK.items()),
    }
    if not result["source_unchanged_after"]:
        raise ValueError("source changed during test")
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "regression.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-root", type=Path, default=SDK_DEFAULT)
    parser.add_argument("--compiler", default=shutil.which("clang++"))
    args = parser.parse_args()
    try:
        if not args.compiler:
            raise ValueError("clang++ unavailable")
        print(json.dumps(run(args.sdk_root, args.compiler), indent=2))
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(str(exc).encode("ascii", "backslashreplace").decode())
        raise SystemExit(1)
