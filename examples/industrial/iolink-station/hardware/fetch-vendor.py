#!/usr/bin/env python3
"""Fetch public manufacturer references and reject changed bytes."""
import hashlib
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "vendor"
OUT.mkdir(exist_ok=True)
for entry in json.loads((ROOT / "vendor-sources.json").read_text())["artifacts"]:
    destination = OUT / entry["file"]
    if destination.exists():
        data = destination.read_bytes()
    else:
        with urllib.request.urlopen(entry["url"], timeout=90) as response:
            data = response.read()
    if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
        raise SystemExit(f'{entry["file"]}: manufacturer bytes differ from reviewed receipt')
    if not destination.exists():
        destination.write_bytes(data)
    print(f'{entry["file"]}: verified')
