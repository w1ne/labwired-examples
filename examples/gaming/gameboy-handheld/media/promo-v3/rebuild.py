#!/usr/bin/env python3
"""Rebuild the 18-second promo from pinned CAD, native PCB and actual ROM frames."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parent
EXAMPLE = ROOT.parent.parent

def run(*args):
    subprocess.run([str(x) for x in args], check=True)

def check_hash(path, expected):
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f'SHA-256 mismatch for {path}: {actual}')
    return actual

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, default=ROOT/'build')
    parser.add_argument('--no-network', action='store_true', help='Require already downloaded, hash-matching assets')
    parser.add_argument('--prepare-only', action='store_true', help='Build inputs and renderer; omit the full 1080-frame render')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    for name in ('motion','pcb','game','audio'):
        (output/name).mkdir(parents=True, exist_ok=True)
    for command in ('cc','g++','ffmpeg','ffprobe'):
        if shutil.which(command) is None:
            raise RuntimeError(f'Missing required command: {command}')
    assets = json.loads((ROOT/'assets.json').read_text())
    fetch_args = [sys.executable,ROOT/'fetch_assets.py','--output-dir',output]
    if args.no_network:
        fetch_args.append('--no-network')
    run(*fetch_args)
    board = EXAMPLE/'pcb/handheld-carrier.kicad_pcb'
    check_hash(board, assets['native_board']['sha256'])
    run(sys.executable,ROOT/'pcb/extract_routing.py','--source',board,'--output-dir',output/'pcb')
    run(sys.executable,ROOT/'pcb/build_copper_mesh.py','--work-dir',output/'pcb')
    firmware = EXAMPLE/'firmware'
    host = output/'game/host-brick-breaker'
    run('cc','-std=c99','-O2',firmware/'host_brick_breaker.c','-o',host)
    run(host,output/'game/native.rgb',output/'game/native-state.jsonl','--promo')
    run(sys.executable,firmware/'capture_brick_breaker.py',output/'game/native.rgb',output/'game/native-state.jsonl',output/'motion')
    check_hash(output/'motion/lcd.rgb',assets['lcd']['sha256'])
    run(sys.executable,ROOT/'motion/prepare_mesh.py','--work-dir',output/'motion')
    run('g++','-O3','-fopenmp','-std=c++17',ROOT/'motion/render_cpu.cpp','-o',output/'motion/render_cpu')
    if args.prepare_only:
        print(json.dumps({'prepared':str(output),'rendered':False}))
        return
    run(sys.executable,ROOT/'motion/record.py','--work-dir',output/'motion')
    run(sys.executable,ROOT/'audio/make_soundtrack.py','--output-dir',output/'audio')
    movie = output/'LabWired-KernelCAD-BrickBreaker-18s.mp4'
    run(sys.executable,ROOT/'finish_promo.py','--video',output/'motion/geometry-master.mp4',
        '--audio',output/'audio/wire-runner-original-30s.wav','--captions',ROOT/'promo.ass','--output',movie)
    print(json.dumps({'output':str(movie),'sha256':hashlib.sha256(movie.read_bytes()).hexdigest()}))

if __name__ == '__main__':
    main()
