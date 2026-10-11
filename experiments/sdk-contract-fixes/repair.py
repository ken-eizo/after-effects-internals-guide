"""Source-locked SDK sample repairs; writes only inside this package.
Original SDK files are never modified. C++ fragment tests are not an AE host.
"""
from __future__ import annotations
import argparse
import difflib
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]
WORK = HERE / "workbench"
PATCHES = {
    "SmartyPants.cpp": [
        ("SDK-ALPHA16", "(PF_MAX_CHAN8 - id->blend) * (PF_MAX_CHAN16 - in->alpha)",
         "(256 - id->blend) * (PF_MAX_CHAN16 - in->alpha)"),
        ("SDK-ALPHA32", "out->alpha = 1.0 - in->alpha;",
         "out->alpha = (id->blend * in->alpha + (256 - id->blend) * (1.0 - in->alpha)) / 256.0;"),
        ("BQ-0029", "out_data->out_flags2 &= PF_OutFlag2_DOESNT_NEED_EMPTY_PIXELS;",
         "out_data->out_flags2 &= ~PF_OutFlag2_DOESNT_NEED_EMPTY_PIXELS;"),
    ],
    "compute-cache-key.cpp": [
        ("BQ-0020", 'const char* hash_buffer = "Level2Histo";',
         'const char hash_buffer[] = "Level2Histo";'),
        ("BQ-0020", "AEGP_CreateHashFromPtr(sizeof(hash_buffer), hash_buffer, out_keyP)",
         "AEGP_CreateHashFromPtr(sizeof(hash_buffer) - 1, hash_buffer, out_keyP)"),
    ],
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class CodeBlocks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.current = None
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == "code":
            self.current = []

    def handle_endtag(self, tag):
        if tag == "code" and self.current is not None:
            self.blocks.append("".join(self.current))
            self.current = None

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)


def guide_code(data: bytes) -> bytes:
    parser = CodeBlocks()
    parser.feed(data.decode("utf-8"))
    matches = [block for block in parser.blocks
               if 'const char* hash_buffer = "Level2Histo";' in block]
    if len(matches) != 1:
        raise ValueError("Guide code block is missing or ambiguous")
    return matches[0].encode("utf-8")


def change(data: bytes, name: str, reverse: bool = False) -> bytes:
    edits = reversed(PATCHES[name]) if reverse else PATCHES[name]
    for issue, before, after in edits:
        if reverse:
            before, after = after, before
        old, new = before.encode(), after.encode()
        if data.count(old) != 1:
            raise ValueError(f"{issue}: expected exactly one patch preimage in {name}")
        data = data.replace(old, new, 1)
    return data


def local_path(path: Path) -> Path:
    if not path.resolve().is_relative_to(HERE.resolve()):
        raise ValueError(f"write destination escapes package: {path}")
    return path


def _write_identical_or_new(path: Path, data: bytes):
    local_path(path)
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f"refusing to overwrite changed file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def prepare(sdk_root: Path):
    lock = json.loads((HERE / "source-lock.json").read_text("utf-8"))
    sources = {}
    records = {}
    for name, item in lock["sources"].items():
        root = sdk_root if item["kind"] == "sdk" else REPOSITORY
        source = root / item["path"]
        data = source.read_bytes()
        if sha(data) != item["sha256"]:
            raise ValueError(f"source changed: {source}; review before creating a new lock")
        sources[name] = data
        records[name] = {"source": str(source.resolve()), "sha256": sha(data), "bytes": len(data)}
    sources["compute-cache-key.cpp"] = guide_code(sources.pop("print_page.html"))
    records["compute-cache-key.cpp"] = {"source": "extracted HTML code block",
                                       "sha256": sha(sources["compute-cache-key.cpp"])}
    fixed = {name: change(sources[name], name) for name in PATCHES}
    # Validate the existing copies before touching any of them.
    for name, data in sources.items():
        for folder in ["original", "copy"]:
            destination = WORK / folder / name
            accepted = (data, fixed.get(name, data)) if folder == "copy" else (data,)
            if destination.exists() and destination.read_bytes() not in accepted:
                raise ValueError(f"copy has unrecognized edits: {destination}")
    for name, data in sources.items():
        _write_identical_or_new(WORK / "original" / name, data)
        destination = WORK / "copy" / name
        if not destination.exists():
            _write_identical_or_new(destination, data)
    for name, data in fixed.items():
        diff = "".join(difflib.unified_diff(
            sources[name].decode().splitlines(keepends=True), data.decode().splitlines(keepends=True),
            fromfile="a/" + name, tofile="b/" + name))
        _write_identical_or_new(HERE / "patches" / (name + ".patch"), diff.encode())
        records[name]["repaired_sha256"] = sha(data)
    _write_identical_or_new(WORK / "provenance.json",
                           (json.dumps(records, indent=2) + "\n").encode())
    return records


def apply(reverse: bool = False):
    provenance = json.loads((WORK / "provenance.json").read_text("utf-8"))
    pending = []
    for name in PATCHES:
        original = (WORK / "original" / name).read_bytes()
        if sha(original) != provenance[name]["sha256"]:
            raise ValueError(f"original copy changed: {name}")
        fixed = change(original, name)
        if sha(fixed) != provenance[name]["repaired_sha256"]:
            raise ValueError(f"repaired copy hash mismatch: {name}")
        before, after = (fixed, original) if reverse else (original, fixed)
        destination = local_path(WORK / "copy" / name)
        current = destination.read_bytes()
        if current == after:
            continue
        if current != before:
            raise ValueError(f"refusing to overwrite unrecognized edits: {destination}")
        pending.append((destination, after))
    for destination, data in pending:
        destination.write_bytes(data)
    return {"action": "revert" if reverse else "apply", "changed_files": len(pending)}


def function(source: str, name: str) -> str:
    matches = list(re.finditer(r"static\s+PF_Err\s+" + name + r"\s*\(", source))
    if len(matches) != 1:
        raise ValueError(f"function {name} missing or ambiguous")
    start = matches[0].start()
    opening = source.index("{", matches[0].end())
    level, cursor = 1, opening + 1
    while level:
        if source[cursor] == "{":
            level += 1
        elif source[cursor] == "}":
            level -= 1
        cursor += 1
    return source[start:cursor]


def extracted_cpp(source: str, guide: str, header: str, smarty_header: str) -> str:
    wrappers = []
    for suffix, pixel in [("8", "Pixel8"), ("16", "Pixel16"), ("Float", "PixelFloat")]:
        body = function(source, "InvertPixel" + suffix)
        alpha = re.search(r"case Channel_ALPHA:\s*(.*?)\s*break;", body, re.S)
        if alpha is None:
            raise ValueError("missing Alpha branch")
        wrappers.append(f"static {pixel} alpha{suffix}(short blend, {pixel} input) {{\n"
                        f"Data info{{blend}}; Data* id=&info; {pixel} result{{}};\n"
                        f"{pixel}* in=&input; {pixel}* out=&result;\n"
                        + alpha.group(1) + "\nreturn result; }\n")
    enum = re.search(r"enum\s*\{\s*Channel_RGB\s*=\s*1,.*?Channel_ALPHA\s*\};",
                     smarty_header, re.S)
    if enum is None:
        raise ValueError("missing channel enum")
    flag = re.search(r"PF_OutFlag2_DOESNT_NEED_EMPTY_PIXELS\s*=\s*([^,]+),", header)
    maxima = []
    for name in ["PF_MAX_CHAN8", "PF_MAX_CHAN16"]:
        match = re.search(r"^#define\s+" + name + r"\s+([^\r\n/]+)", header, re.M)
        if match is None:
            raise ValueError(f"missing {name}")
        maxima.append(f"constexpr int {name} = {match.group(1).strip()};")
    seed = re.search(r'const char(?:\* hash_buffer| hash_buffer\[\]) = "Level2Histo";', guide)
    call = re.search(r"err = hash_suite->AEGP_CreateHashFromPtr\([^;]+;", guide)
    if seed is None or call is None or flag is None:
        raise ValueError("missing seed/flag declaration")
    query = function(source, "QueryDynamicFlags")
    return ("\n".join(maxima) + "\n" + enum.group() + "\n"
            + f"constexpr unsigned PF_OutFlag2_DOESNT_NEED_EMPTY_PIXELS = {flag.group(1)};\n"
            + "\n".join(wrappers) + "\n" + query + "\n"
            + "static void seed_bytes() { int err=0; HashSuite storage; HashSuite* hash_suite=&storage; int key=0; int* out_keyP=&key;\n"
            + seed.group() + "\n" + call.group() + "\n(void)err; }\n")


def regression(compiler: str | None = None):
    compiler = compiler or shutil.which("clang++") or shutil.which("g++")
    if not compiler:
        raise ValueError("C++ compiler unavailable; specify --compiler")
    provenance = json.loads((WORK / "provenance.json").read_text("utf-8"))
    template = (HERE / "regression.cpp.in").read_text("utf-8")
    reports = {}
    for variant in ["original", "copy"]:
        base = WORK / variant
        for name in ["SmartyPants.cpp", "SmartyPants.h", "AE_Effect.h", "compute-cache-key.cpp"]:
            data = (base / name).read_bytes()
            expected = provenance[name]["sha256"] if variant == "original" else provenance[name].get("repaired_sha256", provenance[name]["sha256"])
            if sha(data) != expected:
                raise ValueError(f"{variant}/{name} not expected source; run apply first")
        snippet = extracted_cpp((base / "SmartyPants.cpp").read_text(),
                                (base / "compute-cache-key.cpp").read_text(),
                                (base / "AE_Effect.h").read_text(),
                                (base / "SmartyPants.h").read_text())
        cpp = local_path(WORK / f"regression-{variant}.cpp")
        cpp.write_text(template.replace("// EXTRACTED_SOURCE", snippet), encoding="utf-8")
        exe = local_path(WORK / f"regression-{variant}.exe")
        command = [compiler, "-std=c++17", "-O2", str(cpp), "-o", str(exe)]
        built = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if built.returncode:
            raise ValueError(f"compiler failed:\n{built.stdout}\n{built.stderr}")
        run = subprocess.run([str(exe)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        if run.returncode:
            raise ValueError(f"regression process failed: {run.stderr}")
        reports[variant] = json.loads(run.stdout)
        reports[variant]["extracted_harness_sha256"] = sha(cpp.read_bytes())
    for issue in ["alpha16_failures", "alpha32_failures", "flag_failures"]:
        if reports["original"][issue] <= 0 or reports["copy"][issue] != 0:
            raise ValueError(f"regression did not reproduce and repair {issue}")
    if reports["original"]["seed_bytes"] != reports["original"]["pointer_bytes"] or reports["copy"]["seed_bytes"] != 11 or reports["copy"]["seed_text"] != "Level2Histo":
        raise ValueError("seed-byte contract failed")
    if any(reports[v]["alpha8_failures"] != 0 or reports[v]["preserved_rgb_failures"] != 0 for v in reports):
        raise ValueError("unmodified 8-bit/RGB property failed")
    version = subprocess.run([compiler, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
    report = {"scope": "extracted source fragments compiled as C++17; mocked SDK callback; no AE host execution",
              "compiler": compiler, "compiler_version": version.stdout.splitlines()[0],
              "results": reports, "provenance": provenance}
    local_path(HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "regression.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    lock = json.loads((HERE / "source-lock.json").read_text("utf-8"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "apply", "revert", "regress"])
    parser.add_argument("--sdk-root", type=Path, default=Path(lock["sdk_default"]))
    parser.add_argument("--compiler")
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            result = prepare(args.sdk_root)
        elif args.action == "regress":
            result = regression(args.compiler)
        else:
            result = apply(reverse=args.action == "revert")
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}".encode("ascii", "backslashreplace").decode("ascii"))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
