"""Fast, dependency-free repository checks. Does not compile or play Unreal."""
import argparse,ast,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args])
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--runtime-assets',action='store_true');args=parser.parse_args()
    names=git('ls-files','-z').decode('utf-8').strip('\0').split('\0');errors=[];checked=0
    forbidden=['docs/showcase/','tools/output/','Builds/','blog-writer/','sites/','NightRulesPrototype/Saved/','NightRulesPrototype/Intermediate/','NightRulesPrototype/Binaries/']
    secret=re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{25,}|sk-[A-Za-z0-9_-]{30,}|msy_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY)')
    signed=re.compile(r'https?://[^\s"<>]+(?:X-Amz-Signature|[?&]Signature)=[A-Za-z0-9%+/]{20,}')
    binary={'.uasset','.umap','.blend','.fbx','.glb','.wav','.png','.jpg','.jpeg','.exr','.ttf','.ogg','.mp3','.tga','.hdr','.dds','.mp4','.zip'}
    for name in names:
        p=ROOT/name
        if any(name.startswith(v) for v in forbidden) or 'meshy_output' in p.parts or p.name=='.env':errors.append('Forbidden shared file: '+name)
        if not p.is_file():errors.append('Missing tracked file: '+name);continue
        if p.suffix.lower() in ('.py','.ps1','.cpp','.h','.json','.ini','.md','.yaml','.yml','.txt','.html','.cmd','.toml') and p.stat().st_size<8*1024**2:
            text=p.read_text(encoding='utf-8-sig',errors='replace')
            if secret.search(text) or signed.search(text):errors.append('Credential / signed URL candidate: '+name)
            if p.suffix=='.py':
                try:ast.parse(text,filename=name)
                except SyntaxError as exc:errors.append(f'Python syntax: {name}:{exc.lineno}')
        if name.startswith('NightRulesPrototype/Content/Data/') and p.suffix=='.json':
            try:json.loads(p.read_text(encoding='utf-8-sig'));checked+=1
            except (ValueError,UnicodeError):errors.append('Invalid game JSON: '+name)
    config=json.loads((ROOT/'NightRulesPrototype/NightRulesPrototype.uproject').read_text(encoding='utf-8-sig'))
    if config.get('EngineAssociation')!='5.8':errors.append('Unexpected engine association; update team contract explicitly')
    data=json.loads((ROOT/'NightRulesPrototype/Content/Data/day1.json').read_text(encoding='utf-8-sig'))
    if not isinstance(data.get('documents'),dict):errors.append('Missing day1 documents object')
    bins=[name for name in names if Path(name).suffix.lower() in binary]
    proc=subprocess.run(['git','-C',str(ROOT),'check-attr','--stdin','-z','filter'],input=('\0'.join(bins)+'\0').encode(),stdout=subprocess.PIPE,check=True)
    attrs=proc.stdout.decode('utf-8').strip('\0').split('\0')
    for i in range(0,len(attrs),3):
        if attrs[i+2]!='lfs':errors.append('Binary missing LFS rule: '+attrs[i])
    # Check committed/index blobs, not hydrated working files. LFS blobs should be tiny pointers.
    indexed=git('ls-files','-s','-z').decode('utf-8').strip('\0').split('\0')
    entries=[(line.split('\t',1)[0].split()[1],line.split('\t',1)[1]) for line in indexed]
    proc=subprocess.run(['git','-C',str(ROOT),'cat-file','--batch-check=%(objectsize)'],input=('\n'.join(oid for oid,_ in entries)+'\n').encode(),stdout=subprocess.PIPE,check=True)
    for (_,name),size in zip(entries,proc.stdout.decode().splitlines()):
        if int(size)>50*1024**2:errors.append('Oversized non-LFS blob: '+name)
    if args.runtime_assets:
        for name in bins:
            if name.startswith('NightRulesPrototype/Content/'):
                with (ROOT/name).open('rb') as stream:
                    if stream.read(50).startswith(b'version https://git-lfs.github.com/spec/v1'):errors.append('Runtime LFS file not downloaded: '+name)
    if errors:
        print('\n'.join(errors));return 1
    print(f'PASS: {len(names)} tracked files, {len(bins)} LFS assets, {checked} game JSON files. Unreal build/play NOT run.')
    return 0
if __name__=='__main__':sys.exit(main())
