#!/usr/bin/env python3
"""Fetch exact public source assets and verify their recorded hashes.

No mutable asset is silently accepted. Downloads use the normal system proxy
and CA configuration. No credentials, private endpoints or browser state are used.
"""
from pathlib import Path
import argparse, base64, hashlib, json, urllib.request
from PIL import Image

ROOT = Path(__file__).resolve().parent

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def fetch(spec, output, allow_network):
    path = output / spec['destination']
    if path.exists():
        data = path.read_bytes()
        if sha256(data) == spec['sha256'] and len(data) == spec['bytes']:
            return path
        raise ValueError(f'Existing asset has a different hash: {path}')
    if not allow_network:
        raise FileNotFoundError(f'Missing verified asset: {path}')
    req = urllib.request.Request(spec['url'], headers={'User-Agent':'LabWired-promo-rebuild/1'})
    with urllib.request.urlopen(req, timeout=60) as response:
        data = response.read()
    if spec.get('response') == 'github_base64_blob':
        obj = json.loads(data)
        if obj.get('sha') != spec['git_blob_sha'] or obj.get('encoding') != 'base64':
            raise ValueError('Unexpected vendor blob response')
        data = base64.b64decode(obj['content'])
        git_sha = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if git_sha != spec['git_blob_sha']:
            raise ValueError('Vendor Git blob hash mismatch')
    if len(data) != spec['bytes'] or sha256(data) != spec['sha256']:
        raise ValueError(f'Download hash mismatch: {spec["url"]}')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.download')
    temporary.write_bytes(data)
    temporary.replace(path)
    return path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--no-network', action='store_true')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    assets = json.loads((ROOT/'assets.json').read_text())
    mesh = fetch(assets['mesh'], output, not args.no_network)
    photo = fetch(assets['controller_image'], output, not args.no_network)
    spec = assets['controller_image']
    texture = output/spec['texture_destination']
    texture.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(photo) as image:
        image.convert('RGB').crop(tuple(spec['crop_xyxy'])).save(texture, format='PPM')
    if sha256(texture.read_bytes()) != spec['texture_sha256']:
        raise ValueError('Decoded controller texture differs; use the pinned Pillow version')
    print(json.dumps({'mesh':str(mesh),'controller_texture':str(texture),'hashes_verified':True}))

if __name__ == '__main__':
    main()
