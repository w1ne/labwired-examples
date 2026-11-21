#!/usr/bin/python3
"""Check native KiCad model/library dependency paths without changing source."""
import argparse, hashlib, json, re
from pathlib import Path
import pcbnew


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pcb')
    ap.add_argument('--standard-models', default='/usr/share/kicad/3dmodels')
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    pcb = Path(args.pcb).resolve()
    project = pcb.parent
    board = pcbnew.LoadBoard(str(pcb))
    models, errors, without = [], [], []
    for foot in board.GetFootprints():
        if not list(foot.Models()):
            without.append(foot.GetReference())
        for model in foot.Models():
            name = model.m_Filename
            if name.startswith('${KIPRJMOD}/'):
                kind = 'included-project-file'
                resolved = project / name[len('${KIPRJMOD}/'):]
                if project not in resolved.resolve().parents:
                    errors.append('Project model escapes the package: ' + name)
            elif name.startswith('${KICAD10_3DMODEL_DIR}/'):
                kind = 'standard-kicad10-library'
                resolved = Path(args.standard_models) / name[len('${KICAD10_3DMODEL_DIR}/'):]
            else:
                errors.append('Unsupported or absolute model path: ' + name)
                continue
            exists = resolved.is_file()
            if not exists:
                errors.append('Missing model: ' + name)
            models.append({'reference': foot.GetReference(), 'path': name, 'kind': kind,
                           'exists': exists, 'sha256': sha(resolved) if exists else None})
    table = project / 'fp-lib-table'
    libraries = []
    library_names = {}
    symbol_libraries = []
    if not table.is_file():
        errors.append('Missing project footprint table')
    else:
        for library_name, name in re.findall(r'\(lib\s+\(name\s+"([^"]+)"\)\s*\(type\s+"KiCad"\)\s*\(uri\s+"([^"]+)"\)', table.read_text()):
            if not name.startswith('${KIPRJMOD}/'):
                errors.append('Nonportable project footprint library: ' + name)
                continue
            resolved = project / name[len('${KIPRJMOD}/'):]
            exists = resolved.is_dir()
            if not exists:
                errors.append('Missing project footprint library: ' + name)
            library_names[library_name] = resolved
            libraries.append({'name': library_name, 'path': name, 'exists': exists,
                              'files': [{'path': str(f.relative_to(project)), 'sha256': sha(f)}
                                        for f in sorted(resolved.glob('*.kicad_mod'))] if exists else []})
    for foot in board.GetFootprints():
        name = foot.GetFPIDAsString()
        if ':' not in name:
            errors.append('Unqualified native footprint: ' + foot.GetReference())
            continue
        namespace, item = name.split(':', 1)
        if namespace not in library_names or not (library_names[namespace] / (item + '.kicad_mod')).is_file():
            errors.append('Missing local footprint: ' + foot.GetReference() + ' ' + name)
    symbol_table = project / 'sym-lib-table'
    if not symbol_table.is_file():
        errors.append('Missing project symbol library table')
    else:
        for name in re.findall(r'\(uri\s+"([^"]+)"', symbol_table.read_text()):
            if not name.startswith('${KIPRJMOD}/'):
                errors.append('Nonportable symbol library: ' + name)
                continue
            file = project / name[len('${KIPRJMOD}/'):]
            if not file.is_file():
                errors.append('Missing symbol library: ' + name)
            symbol_libraries.append({'path': name, 'exists': file.is_file(), 'sha256': sha(file) if file.is_file() else None})
    native_files = [pcb, pcb.with_suffix('.kicad_pro'), pcb.with_suffix('.kicad_sch'), table, symbol_table]
    native_files.extend(project.rglob('*.kicad_sym'))
    native_files.extend(project.glob('*.pretty/*.kicad_mod'))
    for file in native_files:
        if not file.is_file():
            errors.append('Missing native source file: ' + file.name)
            continue
        if re.search(r'"/(?:data|home|tmp|workspace)/', file.read_text()):
            errors.append('Transient absolute dependency in ' + str(file.relative_to(project)))
    report = {'pcb_sha256': sha(pcb), 'schematic_sha256': sha(pcb.with_suffix('.kicad_sch')),
              'rules_sha256': sha(pcb.with_suffix('.kicad_pro')),
              'model_references': len(models), 'included_model_references': sum(m['kind'] == 'included-project-file' for m in models),
              'standard_model_references': sum(m['kind'] == 'standard-kicad10-library' for m in models),
              'footprints_without_3d_models': sorted(without),
              'models': sorted(models, key=lambda m: (m['reference'], m['path'])),
              'footprint_libraries': libraries, 'symbol_libraries': symbol_libraries,
              'standard_library_requirement': 'KiCad 10 standard 3D model library; KICAD10_3DMODEL_DIR',
              'errors': errors, 'pass': not errors}
    Path(args.output).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ['pcb_sha256', 'model_references', 'included_model_references', 'standard_model_references', 'errors', 'pass']}, indent=2))
    assert not errors, errors


if __name__ == '__main__':
    main()
