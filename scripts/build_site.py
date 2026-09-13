#!/usr/bin/env python3
from pathlib import Path, PurePosixPath
import argparse, base64, hashlib, io, json, lzma, tarfile

ROOT=Path(__file__).resolve().parents[1]

def fail(msg):
    raise SystemExit(msg)

def main():
    ap=argparse.ArgumentParser(description='Reconstruct the verified ResumeForge static site.')
    ap.add_argument('--output', default='.', help='Output directory (default: repository root)')
    args=ap.parse_args()
    out=(ROOT/args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output).resolve()
    manifest=json.loads((ROOT/'src/site-manifest.json').read_text(encoding='utf-8'))
    encoded=''.join((ROOT/p).read_text(encoding='ascii').strip() for p in manifest['parts'])
    try: archive=base64.b64decode(encoded,validate=True)
    except Exception as e: fail(f'invalid source-pack base64: {e}')
    if len(archive)!=manifest['archive_bytes'] or hashlib.sha256(archive).hexdigest()!=manifest['archive_sha256']:
        fail('source-pack archive integrity check failed')
    expected={f['target']:f for f in manifest['files']}
    seen=set()
    try:
        tar_bytes=lzma.decompress(archive)
        tf=tarfile.open(fileobj=io.BytesIO(tar_bytes),mode='r:')
    except Exception as e: fail(f'cannot open source pack: {e}')
    members=tf.getmembers()
    for m in members:
        name=PurePosixPath(m.name)
        if m.isdir(): continue
        if not m.isfile() or name.is_absolute() or '..' in name.parts or m.name not in expected:
            fail(f'unsafe or unexpected source-pack member: {m.name}')
        raw=tf.extractfile(m).read()
        meta=expected[m.name]
        digest=hashlib.sha256(raw).hexdigest()
        if len(raw)!=meta['bytes'] or digest!=meta['sha256']:
            fail(f'integrity failure for {m.name}')
        dest=(out/m.name).resolve()
        if out not in dest.parents and dest!=out: fail(f'unsafe output path: {m.name}')
        dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(raw); seen.add(m.name)
        print(f'built {m.name} ({len(raw)} bytes, sha256 {digest[:12]}…)')
    missing=set(expected)-seen
    if missing: fail('missing source-pack members: '+', '.join(sorted(missing)))

if __name__=='__main__': main()
