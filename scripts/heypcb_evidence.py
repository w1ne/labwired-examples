"""Strict, offline provenance and evidence-stage gate for public PCB acceptance."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.request import urlopen

MANIFEST = Path(__file__).resolve().parents[1] / "examples/pcb/heypcb-import-acceptance/manifest.json"
SHA = re.compile(r"^[0-9a-f]{40}$")
STAGES = ("fetched", "parsed", "imported", "mapped", "analog_simulated", "firmware_verified", "whole_board_verified")
GOOD = {"passed", "partial", "not_verified", "blocked"}
SOURCE_PREFIX = "https://raw.githubusercontent.com/"


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def validate_manifest(document):
    """Never turn parsed/imported/partially modeled into a full-board success."""
    errors = []
    if document.get("schema") != "labwired.heypcb.acceptance.v1":
        errors.append("invalid manifest schema")
    if document.get("evidence_source") != "https://github.com/w1ne/labwired/pull/2934":
        errors.append("acceptance evidence must link to original PR")
    boards = document.get("boards")
    if not isinstance(boards, list) or not boards:
        return errors + ["nonempty boards list required"]
    seen = set()
    for b in boards:
        key = b.get("id", "<missing>")
        label = f"{key}: "
        if key in seen:
            errors.append(label + "duplicate board id")
        seen.add(key)
        src = b.get("source", {})
        if not re.fullmatch(r"HeyPCB/[A-Za-z0-9_.-]+", src.get("repo", "")):
            errors.append(label + "source must be in pinned HeyPCB repository")
        for field in ("commit", "blob_sha", "license_blob_sha"):
            if not SHA.fullmatch(src.get(field, "")):
                errors.append(label + "missing pinned " + field)
        if src.get("license_path") != "LICENSE" or src.get("license_spdx") not in ("MIT", "CERN-OHL-S-2.0"):
            errors.append(label + "missing scoped source license")
        path = src.get("path", "")
        if not path.endswith(".kicad_pcb") or path.startswith("/") or ".." in Path(path).parts:
            errors.append(label + "unsafe or non-PCB source path")
        status = b.get("stages", {})
        if set(status) != set(STAGES) or any(s not in GOOD for s in status.values()):
            errors.append(label + "incomplete or invalid stage vocabulary")
            continue
        for preceding, following in zip(STAGES, STAGES[1:]):
            if status[following] == "passed" and status[preceding] != "passed":
                errors.append(label + f"{following} passed without {preceding} passed")
        counts = b.get("import_counts", {})
        if any(not isinstance(counts.get(k), int) or isinstance(counts.get(k), bool)
               or counts[k] < 0 for k in ("mapped", "dropped", "ignored")):
            errors.append(label + "invalid import part counts")
        coverage = b.get("model_coverage", {})
        if not isinstance(coverage.get("unmodeled_refs"), list):
            errors.append(label + "missing unmodeled references")
        if coverage.get("net_completeness") not in ("not_measured", "partial", "complete"):
            errors.append(label + "missing net completeness measurement status")
        if coverage.get("pin_completeness") not in ("not_measured", "partial", "complete"):
            errors.append(label + "missing pin completeness measurement status")
        if status["mapped"] == "passed" and (counts.get("dropped", 0) or coverage.get("unmodeled_refs")):
            errors.append(label + "cannot report complete model map with dropped/unmodeled parts")
        whole = b.get("whole_board", {})
        if status["whole_board_verified"] == "passed":
            if (status["analog_simulated"] != "passed" or
                status["mapped"] != "passed" or
                status["imported"] != "passed" or
                coverage.get("net_completeness") != "complete" or
                coverage.get("pin_completeness") != "complete" or
                coverage.get("active_models") != "complete" or
                coverage.get("unmodeled_refs") or
                counts.get("dropped", 1) != 0 or
                whole.get("verdict") != "PASS" or
                whole.get("run_status") != "pass" or
                not whole.get("positive_control") or
                not whole.get("negative_control")):
                errors.append(label + "whole-board PASS without required model and oracle evidence")
        if whole.get("verdict") == "UNSUPPORTED" and (whole.get("run_status") != "not_started" or status["whole_board_verified"] == "passed"):
            errors.append(label + "UNSUPPORTED board cannot claim simulation")
        if status["firmware_verified"] == "passed" and not whole.get("firmware_oracle"):
            errors.append(label + "firmware PASS without board-level firmware oracle")
    bench = document.get("subcircuit_bench", {})
    if bench.get("whole_board_verified") is not False or bench.get("board_id") not in seen:
        errors.append("subcircuit bench cannot be treated as whole-board proof")
    if bench.get("model_verified") and not (bench.get("positive", {}).get("run_status") == "pass" and bench.get("negative", {}).get("run_status") == "fail"):
        errors.append("subcircuit bench requires a passing positive and failing negative control")
    return errors


def raw_source_url(src, path):
    return SOURCE_PREFIX + src["repo"] + "/" + src["commit"] + "/" + path


def verify_pinned_sources(document, timeout=20):
    """Network opt-in. Check actual downloaded source bytes and LICENSE Git blob SHA."""
    errors = []
    checked = {}
    for b in document["boards"]:
        src = b["source"]
        for path, sha in ((src["path"], src["blob_sha"]), (src["license_path"], src["license_blob_sha"])):
            url = raw_source_url(src, path)
            if url in checked:
                actual = checked[url]
            else:
                with urlopen(url, timeout=timeout) as response:
                    payload = response.read(8 * 1024 * 1024 + 1)
                if len(payload) > 8 * 1024 * 1024:
                    errors.append(f"{b['id']}: exceeds 8 MiB per source")
                    continue
                actual = git_blob_sha(payload)
                checked[url] = actual
            if actual != sha:
                errors.append(f"{b['id']}: Git blob SHA mismatch for {url}: {actual} != {sha}")
    return errors, len(checked)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-source", action="store_true", help="fetch pinned public sources and compare Git blob SHA")
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text())
    errors = validate_manifest(data)
    checked = 0
    if args.verify_source and not errors:
        source_errors, checked = verify_pinned_sources(data)
        errors.extend(source_errors)
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 1
    print(f"PASS: {len(data['boards'])} pinned PCB records; whole-board verified: "
          f"{sum(b['stages']['whole_board_verified'] == 'passed' for b in data['boards'])}; "
          f"external source blobs checked: {checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
