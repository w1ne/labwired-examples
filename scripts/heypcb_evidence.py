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
        # Acquisition stages are sequential; behavioral proof axes are independent.
        # A digital-only board can pass a firmware oracle with no analog simulation,
        # and an imported subcircuit can pass an analog test despite unmapped ICs.
        for preceding, following in (("fetched", "parsed"), ("parsed", "imported")):
            if status[following] == "passed" and status[preceding] != "passed":
                errors.append(label + f"{following} passed without {preceding} passed")
        if status["mapped"] in ("passed", "partial") and status["imported"] != "passed":
            errors.append(label + "mapped evidence without successful import")
        if status["whole_board_verified"] == "partial":
            errors.append(label + "whole-board verdict must be passed, blocked or not_verified")
        counts = b.get("import_counts", {})
        if any(not isinstance(counts.get(k), int) or isinstance(counts.get(k), bool)
               or counts[k] < 0 for k in ("mapped", "dropped", "ignored")):
            errors.append(label + "invalid import part counts")
        coverage = b.get("model_coverage", {})
        refs = coverage.get("unmodeled_refs")
        if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref for ref in refs):
            errors.append(label + "missing unmodeled references")
        gaps = coverage.get("model_gaps")
        if not isinstance(gaps, list):
            errors.append(label + "missing per-reference model-gap inventory")
        else:
            gap_refs = []
            dropped = 0
            for gap in gaps:
                if not isinstance(gap, dict):
                    errors.append(label + "malformed model-gap entry")
                    continue
                ref, part, resolution = (gap.get(k) for k in ("ref", "part", "import_resolution"))
                if not isinstance(ref, str) or not re.fullmatch(r"[A-Za-z]+[0-9]+", ref):
                    errors.append(label + "invalid model-gap reference")
                if not isinstance(part, str) or len(part.strip()) < 3:
                    errors.append(label + "model-gap part identity required")
                if resolution not in ("dropped", "mapped_without_behavior"):
                    errors.append(label + "invalid model-gap import resolution")
                dropped += (resolution == "dropped")
                gap_refs.append(ref)
            if isinstance(refs, list) and (len(gap_refs) != len(set(gap_refs)) or set(gap_refs) != set(refs)):
                errors.append(label + "model-gap references differ from unmodeled refs")
            if isinstance(counts.get("dropped"), int) and dropped != counts["dropped"]:
                errors.append(label + "model-gap dropped references differ from import count")
        if coverage.get("net_completeness") not in ("not_measured", "partial", "complete"):
            errors.append(label + "missing net completeness measurement status")
        if coverage.get("pin_completeness") not in ("not_measured", "partial", "complete"):
            errors.append(label + "missing pin completeness measurement status")
        if status["mapped"] == "passed" and (counts.get("dropped", 0) or coverage.get("unmodeled_refs")):
            errors.append(label + "cannot report complete model map with dropped/unmodeled parts")
        whole = b.get("whole_board", {})
        analog = b.get("analog_proof", {})
        if status["analog_simulated"] == "passed":
            if (status["imported"] != "passed" or
                analog.get("scope") not in ("subcircuit", "whole_board") or
                not all(analog.get(field) for field in ("input", "output", "negative_control"))):
                errors.append(label + "analog PASS without scoped input/output and negative control")
        if status["firmware_verified"] == "passed":
            if (status["imported"] != "passed" or
                not whole.get("firmware_oracle") or
                not whole.get("firmware_negative_control")):
                errors.append(label + "firmware PASS without input/oracle and negative control")
        if status["whole_board_verified"] == "passed":
            # Applicability is explicit: firmware is not mandatory on a power-only
            # circuit; analog proof is not mandatory on a digital-only circuit.
            analog_required = whole.get("requires_analog")
            firmware_required = whole.get("requires_firmware")
            if (not isinstance(analog_required, bool) or
                not isinstance(firmware_required, bool) or
                (analog_required and status["analog_simulated"] != "passed") or
                (firmware_required and status["firmware_verified"] != "passed") or
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
    bench = document.get("subcircuit_bench", {})
    if bench.get("whole_board_verified") is not False or bench.get("board_id") not in seen:
        errors.append("subcircuit bench cannot be treated as whole-board proof")
    if bench.get("model_verified") and not (bench.get("positive", {}).get("run_status") == "pass" and bench.get("negative", {}).get("run_status") == "fail"):
        errors.append("subcircuit bench requires a passing positive and failing negative control")
    return errors


def model_gap_report(document):
    """Group actual import gaps without treating a mapped device as simulated."""
    by_part = {}
    for board in document["boards"]:
        for gap in board["model_coverage"]["model_gaps"]:
            entry = by_part.setdefault(gap["part"], {"part": gap["part"], "locations": []})
            entry["locations"].append({
                "board": board["id"], "ref": gap["ref"],
                "import_resolution": gap["import_resolution"],
            })
    parts = sorted(by_part.values(), key=lambda item: (-len(item["locations"]), item["part"]))
    return {
        "recorded_date": document["recorded_date"],
        "evidence_source": document["evidence_source"],
        "sample_boards": len(document["boards"]),
        "full_boards_verified": sum(b["stages"]["whole_board_verified"] == "passed" for b in document["boards"]),
        "model_gap_references": sum(len(p["locations"]) for p in parts),
        "dropped_references": sum(x["import_resolution"] == "dropped" for p in parts for x in p["locations"]),
        "mapped_without_behavior_references": sum(x["import_resolution"] == "mapped_without_behavior" for p in parts for x in p["locations"]),
        "models": parts,
    }


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
    parser.add_argument("--model-gaps", action="store_true", help="print evidence-scoped, machine-readable unmodeled-part backlog")
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
    if args.model_gaps:
        print(json.dumps(model_gap_report(data), indent=2))
        return 0
    print(f"PASS: {len(data['boards'])} pinned PCB records; whole-board verified: "
          f"{sum(b['stages']['whole_board_verified'] == 'passed' for b in data['boards'])}; "
          f"external source blobs checked: {checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
