#!/usr/bin/env python3
from pathlib import Path, PurePosixPath
import argparse, base64, hashlib, io, json, lzma, tarfile

ROOT=Path(__file__).resolve().parents[1]

def fail(msg):
    raise SystemExit(msg)

def sha256(raw):
    return hashlib.sha256(raw).hexdigest()

def safe_dest(out, relative):
    rel=PurePosixPath(relative)
    if rel.is_absolute() or '..' in rel.parts:
        fail(f'unsafe output path: {relative}')
    dest=(out/relative).resolve()
    if out not in dest.parents and dest!=out:
        fail(f'unsafe output path: {relative}')
    return dest

def apply_overlays(out):
    overlay_path=ROOT/'src/site-overlays.json'
    if not overlay_path.exists():
        return
    data=json.loads(overlay_path.read_text(encoding='utf-8'))
    styles=[]; scripts=[]
    for item in data.get('overlays', []):
        source=(ROOT/item['source']).resolve()
        if ROOT not in source.parents:
            fail(f'unsafe overlay source: {item["source"]}')
        raw=source.read_bytes()
        if len(raw)!=item['bytes'] or sha256(raw)!=item['sha256']:
            fail(f'overlay integrity failure for {item["source"]}')
        dest=safe_dest(out,item['target'])
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(raw)
        if item.get('kind')=='style': styles.append(item['target'])
        elif item.get('kind')=='script': scripts.append(item['target'])
        else: fail(f'unknown overlay kind: {item.get("kind")}')
        print(f'overlay {item["target"]} ({len(raw)} bytes, sha256 {sha256(raw)[:12]}…)')

    index_path=safe_dest(out,'index.html')
    html=index_path.read_text(encoding='utf-8')
    for href in styles:
        tag=f'<link rel="stylesheet" href="{href}">'
        if tag not in html:
            if '</head>' not in html: fail('cannot inject stylesheet overlay: </head> missing')
            html=html.replace('</head>',f'{tag}\n</head>',1)
    for src in scripts:
        tag=f'<script src="{src}"></script>'
        if tag not in html:
            if '</body>' not in html: fail('cannot inject script overlay: </body> missing')
            html=html.replace('</body>',f'{tag}\n</body>',1)
    encoded=html.encode('utf-8')
    final=data.get('final_index')
    if final and (len(encoded)!=final['bytes'] or sha256(encoded)!=final['sha256']):
        fail('final index integrity check failed after overlays')
    index_path.write_bytes(encoded)
    print(f'final index.html ({len(encoded)} bytes, sha256 {sha256(encoded)[:12]}…)')

def main():
    ap=argparse.ArgumentParser(description='Reconstruct the verified ResumeForge static site.')
    ap.add_argument('--output', default='.', help='Output directory (default: repository root)')
    args=ap.parse_args()
    out=(ROOT/args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output).resolve()
    manifest=json.loads((ROOT/'src/site-manifest.json').read_text(encoding='utf-8'))
    encoded=''.join((ROOT/p).read_text(encoding='ascii').strip() for p in manifest['parts'])
    try: archive=base64.b64decode(encoded,validate=True)
    except Exception as e: fail(f'invalid source-pack base64: {e}')
    if len(archive)!=manifest['archive_bytes'] or sha256(archive)!=manifest['archive_sha256']:
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
        digest=sha256(raw)
        if len(raw)!=meta['bytes'] or digest!=meta['sha256']:
            fail(f'integrity failure for {m.name}')
        dest=safe_dest(out,m.name)
        dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(raw); seen.add(m.name)
        print(f'built {m.name} ({len(raw)} bytes, sha256 {digest[:12]}…)')
    missing=set(expected)-seen
    if missing: fail('missing source-pack members: '+', '.join(sorted(missing)))
    apply_overlays(out)

if __name__=='__main__': main()
