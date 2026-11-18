#!/usr/bin/env python3
"""Record the exact binaries, configuration, and reviewed source used for a build."""
from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parent
out=root/'artifacts';out.mkdir(exist_ok=True)
for source,name in [('build/doom-s3.elf','doom-s3.elf'),('build/doom-s3.bin','doom-s3.bin'),('build/bootloader/bootloader.bin','bootloader.bin'),('build/partition_table/partition-table.bin','partition-table.bin'),('build/flasher_args.json','flasher_args.json'),('sdkconfig','sdkconfig')]:
    shutil.copyfile(root/'source'/source,out/name)
def identity(p):
    b=p.read_bytes();return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
files={p.name:identity(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='build-manifest.json'}
reviewed=json.loads((root/'source-provenance.json').read_text())
source_files={name:identity(root/'source'/name)['sha256'] for name in sorted(reviewed['packaged_files_sha256'])}
record={'schema':1,'inputs':json.loads((root/'build-inputs.json').read_text()),'files':files,'source_files_sha256':source_files,'reviewed_source_manifest_sha256':identity(root/'source-provenance.json')['sha256'],'flash_base':0,'hardware_tested':False,'runtime_validation':'See validation/ for separately recorded model results.'}
(out/'build-manifest.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'files':len(files),'merged_flash':files['doom-s3-flash.bin'],'elf':files['doom-s3.elf']},indent=2))
