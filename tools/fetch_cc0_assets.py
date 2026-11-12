"""Download an explicit selection from Poly Haven's official public API."""
from pathlib import Path
import hashlib, json, urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Art' / 'ThirdParty' / 'PolyHaven'
ASSETS = ['metal_office_desk', 'plastic_monobloc_chair_01',
          'steel_frame_shelves_03', 'vintage_microwave',
          'vintage_electric_kettle', 'pot_enamel_01', 'television_02',
          'security_camera_01', 'korean_fire_extinguisher_01', 'wall_clock',
          'old_bed_frame']
# Surface textures (1k PNG) for meshes authored in tools/create_door.py.
TEXTURES = ['oak_veneer_01']

def request(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={
        'User-Agent': 'HaedamPrototypeAssetImport/1.0'}), timeout=90)

def download(info, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or hashlib.md5(path.read_bytes()).hexdigest() != info['md5']:
        with request(info['url']) as response:
            path.write_bytes(response.read())
    if hashlib.md5(path.read_bytes()).hexdigest() != info['md5']:
        raise RuntimeError('Checksum mismatch: ' + str(path))

records = []
for slug in ASSETS:
    folder = OUT / slug
    folder.mkdir(parents=True, exist_ok=True)
    with request('https://api.polyhaven.com/files/' + slug) as response:
        files = json.load(response)
    with request('https://api.polyhaven.com/info/' + slug) as response:
        info = json.load(response)
    variant = files['blend']['2k']['blend']
    download(variant, folder / (slug + '_2k.blend'))
    for relative, resource in variant.get('include', {}).items():
        download(resource, folder / relative)
    (folder / 'source.json').write_text(json.dumps({
        'asset': slug, 'info': info, 'files': variant,
        'license': 'CC0-1.0', 'license_url': 'https://polyhaven.com/license',
        'source_url': 'https://polyhaven.com/a/' + slug
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    records.append({'asset': slug, 'source': 'https://polyhaven.com/a/' + slug,
                    'license': 'CC0-1.0', 'author': info.get('authors', {})})
    print('Downloaded and checksum verified:', slug, flush=True)
for slug in TEXTURES:
    with request('https://api.polyhaven.com/files/' + slug) as response:
        files = json.load(response)
    with request('https://api.polyhaven.com/info/' + slug) as response:
        info = json.load(response)
    for kind in ('Diffuse', 'Rough', 'nor_gl'):
        resource = files[kind]['1k']['png']
        download(resource, OUT / slug / Path(resource['url']).name)
    (OUT / slug / 'source.json').write_text(json.dumps({
        'asset': slug, 'info': info, 'license': 'CC0-1.0',
        'source_url': 'https://polyhaven.com/a/' + slug}, ensure_ascii=False, indent=2), encoding='utf-8')
    records.append({'asset': slug, 'source': 'https://polyhaven.com/a/' + slug,
                    'license': 'CC0-1.0', 'author': info.get('authors', {})})
    print('Downloaded and checksum verified:', slug, flush=True)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
(OUT / 'LICENSE.txt').write_text('Poly Haven assets: CC0 1.0 Universal.\n'
    'Official license: https://polyhaven.com/license\n'
    'License text: https://creativecommons.org/publicdomain/zero/1.0/\n'
    'Authors and original download checksums are recorded in each source.json.\n', encoding='utf-8')
