#!/usr/bin/python3
"""Build and verify the complete portable KiCad source archive from staged files."""
import argparse, hashlib, json, zipfile
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release-root', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    release = Path(args.release_root)
    output = Path(args.output)
    entries = {}

    def add(file, path):
        assert not path.startswith('/') and '..' not in Path(path).parts, path
        data = file.read_bytes()
        if path in entries:
            assert entries[path] == data, ('Conflicting payload', path)
            return
        entries[path] = data

    for file in sorted((release / 'source').rglob('*')):
        if file.is_file() and (file.suffix.lower() in ['.kicad_pcb', '.kicad_pro', '.kicad_sch', '.kicad_mod', '.kicad_sym', '.step', '.stp'] or file.name in ['fp-lib-table', 'sym-lib-table', 'KICAD_SYMBOLS_ATTRIBUTION.md', 'KICAD_SYMBOLS_LICENSE.md']):
            add(file, 'hardware/' + str(file.relative_to(release / 'source')))
    for file in sorted((release / 'exports').iterdir()):
        if file.is_file() and file.suffix.lower() in ['.step', '.pdf']:
            add(file, 'hardware/exports/' + file.name)
    for sub, target in [('evidence', 'verification/native-pcb'), ('tools', 'verification/native-pcb/tools'),
                        ('inputs', 'hardware/source-inputs/native-pcb'), ('accepted-baseline', 'verification/native-pcb/accepted-baseline'),
                        ('physical-source', 'verification/native-pcb/physical-source')]:
        directory = release / sub
        if not directory.is_dir():
            continue
        for file in sorted(directory.rglob('*')):
            if file.is_file() and '__pycache__' not in file.parts and file.suffix != '.pyc':
                add(file, target + '/' + str(file.relative_to(directory)))
    add(release / 'native-package-README.md', 'README.md')
    source = release / 'source/a1-printcore.kicad_pcb'
    audit = json.loads((release / 'evidence/native-source-audit.json').read_text())
    assert audit['pass'] and audit['candidate_sha256'] == digest(source.read_bytes())
    assert audit['schematic_parity_checked'] and audit['portability_required']
    assert audit['drc_counts'] == {'violations': 0, 'unconnected_items': 0, 'schematic_parity': 0}
    erc = json.loads((release / 'evidence/native-erc-summary.json').read_text())
    assert erc['errors'] == 0 and erc['pcb_sha256'] == audit['candidate_sha256']
    assert erc['counts_by_type'] == {'isolated_pin_label': 9}
    portability = json.loads((release / 'evidence/native-project-portability.json').read_text())
    assert portability['pass'] and portability['pcb_sha256'] == audit['candidate_sha256']
    manifest = {
        'schema': 'labwired.native-kicad-package.v1',
        'pcb_sha256': audit['candidate_sha256'],
        'schematic_sha256': digest(source.with_suffix('.kicad_sch').read_bytes()),
        'rules_sha256': digest(source.with_suffix('.kicad_pro').read_bytes()),
        'physical_geometry_source_sha256': '55b7162b73d0d9675725c5ea9211b6c633feeb2bd298e9a1e6209b5e5c25a6ad',
        'accepted_populated_step_sha256': '4fa338f753a8c8a17331facabd8ee8d3698bc0a0cd3fa152b71749e88baa2e2a',
        'footprints': audit['footprint_count'], 'physical_pads': audit['pad_count'],
        'native_drc': audit['drc_counts'], 'schematic_parity_checked': True,
        'source_portability_checked': True, 'native_erc_errors': 0, 'native_erc_warnings': {'isolated_pin_label': 9},
        'standard_dependencies': ['KiCad 10 standard 3D model library via KICAD10_3DMODEL_DIR'],
        'files': [{'path': path, 'bytes': len(data), 'sha256': digest(data)} for path, data in sorted(entries.items())],
    }
    entries['manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, data in sorted(entries.items()):
            info = zipfile.ZipInfo('a1-printcore/' + path, (2026, 11, 21, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(entries)
        for path, data in entries.items():
            assert archive.read('a1-printcore/' + path) == data
    report = {'archive_filename': output.name, 'archive_bytes': output.stat().st_size,
              'archive_sha256': digest(output.read_bytes()), 'archive_member_count': len(entries),
              'manifest': manifest, 'zip_crc_and_all_payload_bytes_verified': True}
    output.with_suffix('.manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ['archive_filename', 'archive_bytes', 'archive_sha256', 'archive_member_count', 'zip_crc_and_all_payload_bytes_verified']}, indent=2))


if __name__ == '__main__':
    main()
