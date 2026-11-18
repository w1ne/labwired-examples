#!/usr/bin/env python3
"""Verify packaged native source, flash composition and recorded protocol oracles."""
import hashlib
import json
from pathlib import Path
import struct
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def require(condition, message):
    if not condition:
        raise SystemExit('FAIL: ' + message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((HERE / 'package-manifest.json').read_text())
    seen = set()
    for item in manifest['files']:
        relative = Path(item['path'])
        require(not relative.is_absolute() and '..' not in relative.parts, 'unsafe manifest path')
        require(item['path'] not in seen, 'duplicate manifest path')
        seen.add(item['path'])
        path = ROOT / relative
        require(path.is_file(), 'missing ' + item['path'])
        require(path.stat().st_size == item['bytes'], 'size ' + item['path'])
        require(sha(path) == item['sha256'], 'hash ' + item['path'])
    require(sha(ROOT / manifest['hardware_identity']['board']) == manifest['hardware_identity']['board_sha256'], 'native board identity')
    for archive in json.loads((HERE / 'sources/source-archives.json').read_text()):
        path = HERE / 'sources' / archive['path']
        require(sha(path) == archive['sha256'], 'source archive identity')
    build = json.loads((HERE / 'evidence/clean-archive-build.json').read_text())
    require(len(build['runs']) == 2, 'application and bootloader replay')
    for run in build['runs']:
        require(run['exit'] == 0 and run['reproduced'], 'source replay failed')
        for artifact in run['artifacts'].values():
            expected = artifact.get('expectedSha256')
            if expected is not None:
                path = HERE / 'artifacts' / Path(artifact['path']).name
                require(sha(path) == expected == artifact['sha256'], 'reproduced flash identity')
    bundle = json.loads((HERE / 'sources/source-bundle.json').read_text())
    archive = HERE / 'sources' / bundle['archive']
    require(archive.stat().st_size == bundle['bytes'] and sha(archive) == bundle['sha256'], 'complete source bundle identity')
    expected_files = {item['path']: item for item in bundle['files']}
    found = {}
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar.getmembers():
            name = Path(member.name)
            require(not name.is_absolute() and '..' not in name.parts, 'unsafe source archive path')
            if member.isdir():
                continue
            require(member.isfile(), 'unexpected link/device source member')
            require(member.name not in found and member.name in expected_files, 'unexpected/duplicate archive member')
            data = tar.extractfile(member).read()
            item = expected_files[member.name]
            require(len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'], 'expanded source identity ' + member.name)
            found[member.name] = data
    require(set(found) == set(expected_files), 'incomplete expanded source archive')
    entry = bundle['entry']
    require(hashlib.sha256(found[entry['path']]).hexdigest() == entry['sha256'], 'editable entry source binding')
    replay = json.loads((HERE / 'evidence/complete-source-replay.json').read_text())
    require(manifest['sourceBundle'] == bundle, 'package source bundle manifest differs')
    require(replay['archive']['sha256'] == bundle['sha256'] and replay['archive']['bytes'] == bundle['bytes'], 'replayed source archive identity')
    require(replay['exit'] == 0 and all(x['exit'] == 0 and x['reproduced'] for x in replay['build']['runs']), 'expanded source replay failed')
    require(replay['build']['complete']['exit'] == 0 and replay['build']['complete']['reproduced'], 'complete flash replay failed')
    for artifact in replay['build']['complete']['artifacts'].values():
        require(sha(HERE / 'artifacts' / Path(artifact['path']).name) == artifact['sha256'] == artifact['expectedSha256'], 'replayed complete image identity')
    record = json.loads((HERE / 'evidence/flash-container-receipt.json').read_text())
    expected = bytearray([record['fillByte']] * record['flashBytes'])
    occupied = set()
    for item in record['sources']:
        data = (HERE / item['path']).read_bytes()
        start = item['address'] - record['flashStart']
        require(len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'], 'flash input identity')
        require(start >= 0 and start + len(data) <= len(expected), 'flash range')
        region = set(range(start, start + len(data)))
        require(not occupied.intersection(region), 'overlapping flash regions')
        occupied.update(region)
        expected[start:start + len(data)] = data
    complete = HERE / 'artifacts/OPENESC_30_F421_complete.elf'
    data = complete.read_bytes()
    require(data[:7] == b'\x7fELF\x01\x01\x01', 'little-endian ELF32 image')
    hdr = struct.unpack_from('<HHIIIIIHHHHHH', data, 16)
    require(hdr[1] == 40 and hdr[9] == 1, 'one ARM load segment')
    ph = struct.unpack_from('<IIIIIIII', data, hdr[4])
    require(ph[0] == 1 and ph[2] == ph[3] == record['flashStart'], 'flash segment address')
    require(ph[4] == ph[5] == len(expected), 'flash segment extent')
    require(data[ph[1]:ph[1] + ph[4]] == expected, 'ELF load bytes differ from original flash inputs')
    require((HERE / 'artifacts/OPENESC_30_F421_complete.bin').read_bytes() == expected, 'BIN composition')
    stack, entry = struct.unpack_from('<II', expected)
    require(stack == record['initialStack'] and entry == hdr[3] == record['bootEntry'], 'original boot vectors')
    runtime = ROOT / 'runtime/native-esc/evidence'
    invocation = json.loads((runtime / 'conventional-invocation.json').read_text())
    result = json.loads((runtime / 'conventional-result.json').read_text())
    require(invocation['exit'] == 0 and invocation['before'] == invocation['after'], 'frozen native protocol invocation')
    require(result['completeElfSha256'] == sha(complete), 'runtime complete image')
    require(result['applicationElfSha256'] == sha(HERE / 'artifacts/AM32_OPENESC_30_F421_2.21.elf'), 'runtime application image')
    before, bad, good = (result[k] for k in ['beforeCorruptFrame', 'afterCorruptFrame', 'afterValidFrame'])
    require(before['system_core_clock'] == 120_000_000 and before['inputSet'] == before['dshot'] == 1, 'native clock and DShot acquisition')
    require(before['dshot_goodcounts'] == 39 and before['dshot_badcounts'] == 0, 'valid acquisition frames')
    require(bad['dshot_badcounts'] == before['dshot_badcounts'] + 1 and bad['newinput'] == 0, 'corrupt-frame rejection')
    require(good['dshot_goodcounts'] == bad['dshot_goodcounts'] + 1 and good['newinput'] == 100, 'valid value100 acceptance')
    require(good['sensor_configuration_error'] == good['armed'] == 0, 'unforced pre-arm scope')
    invocation = json.loads((runtime / 'bidirectional-invocation.json').read_text())
    bidir = json.loads((runtime / 'bidirectional-result.json').read_text())
    require(invocation['exit'] == 0 and invocation['before'] == invocation['after'], 'frozen bidirectional invocation')
    require(invocation['coreCommit'] == manifest['runtime']['coreCommit'] == 'c29e0e367d0075975e4d555f8135b6f668e57f7b', 'actual runtime source commit')
    require(bidir['completeElfSha256'] == sha(complete) and bidir['applicationElfSha256'] == sha(HERE / 'artifacts/AM32_OPENESC_30_F421_2.21.elf'), 'bidirectional image identity')
    before, bad, good = (bidir[k] for k in ['beforeCorruptFrame', 'afterCorruptFrame', 'afterValidFrame'])
    require(before['dshot_telemetry'] == 1 and before['dshot_goodcounts'] == 14 and before['dshot_badcounts'] == 100, 'bidirectional acquisition')
    require(bad['dshot_badcounts'] == before['dshot_badcounts'] + 1 and bad['newinput'] == 0, 'bidirectional checksum rejection')
    require(good['dshot_goodcounts'] == bad['dshot_goodcounts'] + 1 and good['newinput'] == good['adjusted_input'] == 100, 'bidirectional value acceptance')
    require(good['armed'] == good['sensor_configuration_error'] == 0, 'single-controller unforced scope')
    wire = bidir['output']
    require(wire['drivenEdges'] == 17 and wire['released'] and not wire['contention'], 'actual PB4 drive/release')
    require(wire['decodedReply'].get('Ok') == [4095, 154], 'independent GCR/checksum/bit-clock oracle')
    require(bidir['validFrameTrace']['dropped'] == 0 and bidir['badFrameTrace']['dropped'] == 0, 'complete pad trace')
    require(manifest['fiveNodeRuntimeQualified'] is False, 'single-node package must not claim five-node proof')
    print(f'PASS: {len(seen)} source/artifact records; {len(found)} expanded source members; unchanged complete flash; conventional and bidirectional DShot600/GCR oracles')
    print('Connected five-node and physical motor/load qualification remain separate.')


if __name__ == '__main__':
    main()
