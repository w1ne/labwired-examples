#!/usr/bin/env python3
"""Replay the exact packaged firmware and require visible canonical-UART input."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def replay(args):
    cli = Path(args.labwired).resolve()
    rom, drom = Path(args.rom).resolve(), Path(args.drom).resolve()
    provenance = json.loads((ROOT / 'runtime/provenance.json').read_text())
    expected = json.loads((ROOT / 'validation/runtime/paired-acceptance.json').read_text())
    for path, name in [(rom, 'esp32s3_rom.bin'), (drom, 'esp32s3_drom.bin')]:
        assert digest(path) == provenance['roms'][name]['sha256'], f'Wrong mask ROM: {path}'
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env.pop('LABWIRED_ESP32S3_FASTBOOT', None)
    env.update(LABWIRED_ESP32S3_FLASH=str(ROOT / 'firmware/artifacts/doom-s3-flash.bin'),
               LABWIRED_ESP32S3_ROM=str(rom), LABWIRED_ESP32S3_DROM=str(drom))
    frames = {}
    receipts = {}
    with tempfile.TemporaryDirectory(prefix='doom-native-runtime-') as temporary:
        work = Path(temporary)
        system = (ROOT / 'runtime/system.yaml').read_text().replace('"chip.yaml"', json.dumps(str(ROOT / 'runtime/chip.yaml')))
        (work / 'system.yaml').write_text(system)
        for name in ['no-input', 'menu-input']:
            script = (ROOT / 'runtime' / (name + '.yaml')).read_text()
            script = script.replace('"../firmware/artifacts/doom-s3.elf"', json.dumps(str(ROOT / 'firmware/artifacts/doom-s3.elf')))
            script = script.replace('"system.yaml"', json.dumps(str(work / 'system.yaml')))
            script_path = work / (name + '.yaml')
            script_path.write_text(script)
            destination = output / name
            command = [str(cli), 'test', '--script', str(script_path), '--rom-boot',
                       '--no-uart-stdout', '--output-dir', str(destination),
                       '--inspect-bytes-max', '1048576', '--run-manifest']
            with (output / (name + '.log')).open('w') as log:
                execution = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=330)
            assert execution.returncode == 0, f'{name} failed: see {output / (name + ".log")}'
            result = json.loads((destination / 'result.json').read_text())
            assert result['status'] == 'pass' and result['steps_executed'] == 900000000
            assert len(result['assertions']) == 3 and all(x['passed'] for x in result['assertions'])
            assert result['firmware_hash'] == digest(ROOT / 'firmware/artifacts/doom-s3.elf')
            device = next(x for x in result['inspect']['devices'] if x['id'] == 'tft')
            frame = next(x for x in device['artifacts'] if x['kind'] == 'framebuffer')
            assert frame['meta']['format'] == 'rgb565_be'
            assert (frame['meta']['w'], frame['meta']['h']) == (320, 240)
            frames[name] = bytes(frame['bytes'])
            frame_hash = hashlib.sha256(frames[name]).hexdigest()
            assert frame_hash == expected['runs'][name]['framebuffer_sha256'], f'{name} image changed; inspect the real framebuffer before accepting new evidence'
            receipts[name] = {'framebuffer_sha256': frame_hash, 'steps': result['steps_executed'], 'assertions_passed': 3}
        log = (output / 'menu-input.log').read_text()
        assert "1 byte(s) delivered to 'uart0'" in log, 'Canonical UART input was not delivered'
        assert 'ERROR' not in log, 'Runtime reported an error despite a passing process result'
    changed = sum(a != b for a, b in zip(frames['no-input'], frames['menu-input']))
    assert changed == expected['input']['framebuffer_changed_bytes'] and changed > 0
    receipt = {'status': 'pass', 'cli_sha256': digest(cli), 'runs': receipts, 'framebuffer_changed_bytes': changed}
    (output / 'paired-acceptance.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--labwired', required=True, help='CLI built from the core commit in runtime/provenance.json')
    parser.add_argument('--rom', required=True, help='Verified ESP32-S3 IROM image')
    parser.add_argument('--drom', required=True, help='Verified ESP32-S3 DROM image')
    parser.add_argument('--output', required=True, help='New output directory; existing evidence is never overwritten')
    print(json.dumps(replay(parser.parse_args()), indent=2))
