#!/usr/bin/python3
"""Copy exact accepted STEP bytes and replace only their absolute model paths."""
import argparse, hashlib, json, re, shutil
from pathlib import Path

MODEL_FILES = [
    {'filename': 'QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm.step',
     'original_path': '/home/andrii/ventures/state/pr-merge-backlog/a1-3d-exact-20261119T0054Z/models/Package_DFN_QFN.3dshapes/QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm.step',
     'references': ['U1'], 'sha256': 'ba30b82fac313a906167a8e5739f396cae47472c2ef885c0975be7ea93235b26'},
    {'filename': 'Molex_Micro-Fit_3.0_43650-0410_1x04-1MP_P3.00mm_Horizontal.stp',
     'original_path': '/home/andrii/ventures/state/pr-merge-backlog/a1-3d-molex-source-20261119T0205Z/Molex_Micro-Fit_3.0_43650-0410_1x04-1MP_P3.00mm_Horizontal.stp',
     'references': ['J10', 'J11', 'J12', 'J13'], 'sha256': '2d52fa75c9bc7928f3f3e8afb974956297365d501a06f1ca39d65186777a4b9a'},
    {'filename': 'XT30PW-M-media.step',
     'original_path': '/home/andrii/ventures/state/pr-merge-backlog/a1-3d-xt30-source-20261119T0156Z/XT30PW-M-media.step',
     'references': ['J1'], 'sha256': '8d503f92f9a79ceb5c7c2edea1f45ed92a7a1d3fd24ebe6179f6de88b64e38ed'},
]

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input')
    ap.add_argument('output')
    ap.add_argument('--models-dir', required=True)
    ap.add_argument('--evidence', required=True)
    args = ap.parse_args()
    source, dest = Path(args.input), Path(args.output)
    assert source.resolve() != dest.resolve(), 'Use a separate output for metadata provenance'
    before = source.read_bytes()
    after = before
    replacements = []
    model_dest = dest.parent / 'models'
    model_dest.mkdir(parents=True, exist_ok=True)
    for entry in MODEL_FILES:
        data = (Path(args.models_dir) / entry['filename']).read_bytes()
        assert digest(data) == entry['sha256'], 'Accepted model bytes changed: ' + entry['filename']
        target = model_dest / entry['filename']
        if not target.exists() or target.read_bytes() != data:
            target.write_bytes(data)
        old = ('(model "' + entry['original_path'] + '"').encode()
        portable = '${KIPRJMOD}/models/' + entry['filename']
        new = ('(model "' + portable + '"').encode()
        count = after.count(old)
        assert count == len(entry['references']), (entry['filename'], count)
        assert new not in after, 'Input is already portable or has an ambiguous duplicate'
        after = after.replace(old, new)
        replacements.append({**entry, 'portable_path': portable, 'occurrences': count, 'bytes': len(data)})
    for name in re.findall(rb'\(model\s+"([^"]+)"', after):
        assert name.startswith((b'${KICAD10_3DMODEL_DIR}/', b'${KIPRJMOD}/models/')), name
    restored = after
    for entry in replacements:
        restored = restored.replace(('(model "' + entry['portable_path'] + '"').encode(),
                                    ('(model "' + entry['original_path'] + '"').encode())
    assert restored == before, 'Changes exceeded the exact approved model path strings'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(after)
    source_pro = source.with_suffix('.kicad_pro')
    if source_pro.is_file():
        target_pro = dest.with_suffix('.kicad_pro')
        if source_pro.resolve() != target_pro.resolve():
            shutil.copy2(source_pro, target_pro)
    report = {'input_sha256': digest(before), 'output_sha256': digest(after),
              'model_path_replacements': replacements, 'reverse_restores_input_bytes': True,
              'changed_fields': ['footprint model filename'],
              'model_bytes_unchanged': True, 'geometry_unchanged': True, 'pass': True}
    evidence = Path(args.evidence)
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / 'portable-model-paths.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
