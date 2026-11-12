"""Bundle the current packaged Windows build for offline private playtests."""
import argparse
import hashlib
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--tag', required=True)
parser.add_argument('--engine', default='C:/Program Files/Epic Games/UE_5.8')
args = parser.parse_args()
if not args.tag.replace('-', '').isalnum():
    raise SystemExit('Tag must contain only letters, digits and hyphens.')
source = root / 'Builds/Windows'
name = f'NightRules-Demo-{args.tag}'
output = root / 'Builds/Portable' / f'{name}.zip'
runtime = Path(args.engine) / 'Engine/Extras/Redist/en-us/vc_redist.x64.exe'
for required in [source / 'NightRulesPrototype.exe', runtime,
                 source / 'NightRulesPrototype/Content/Paks/global.utoc']:
    if not required.is_file():
        raise SystemExit(f'Missing required file: {required}')
if output.exists():
    raise SystemExit(f'Refusing to overwrite: {output}')
output.parent.mkdir(parents=True, exist_ok=True)

def launcher(extra):
    return ('@echo off\r\nsetlocal\r\ncd /d "%~dp0"\r\n'
            'if not exist "NightRulesPrototype.exe" (\r\n'
            '  echo Extract the entire ZIP before running.\r\n'
            '  pause\r\n  exit /b 1\r\n)\r\n'
            f'start "" "NightRulesPrototype.exe" -windowed -ResX=1280 -ResY=720 {extra}\r\n')

readme = '''야간수칙 — 개인 시연용 DAY 1 프로토타입

실행 방법
1. ZIP 파일을 USB나 개인 클라우드로 노트북에 복사합니다.
2. 노트북의 로컬 폴더에 반드시 전체 압축을 풉니다.
3. MX450 노트북은 Play_Laptop.cmd를 실행합니다.
4. 비교용 기본 품질은 Play_Standard.cmd를 실행합니다.

언리얼 에디터, Blender, Steam 설치나 로그인은 필요하지 않습니다.
파일 일부만 옮기지 말고 Engine과 NightRulesPrototype 폴더를 함께 유지하세요.
VCRUNTIME/MSVCP 오류가 나면 Prerequisites/vc_redist.x64.exe를 설치하세요.
이 파일은 Visual C++ 실행 구성요소이며, 게임 실행 전에 자동 설치하지 않습니다.

노트북 모드
1280x720 창 모드 / 내부 렌더 해상도 80% / 최대 30fps
그림자·후처리·효과·텍스처 품질 감소. 30fps 성능을 보장하는 설정은 아닙니다.
전원을 연결하고 Windows 그래픽 설정에서 게임 실행파일에 MX450을 지정하세요.
실행파일: NightRulesPrototype/Binaries/Win64/NightRulesPrototype.exe
기본 품질 버튼은 기본 품질 값(3), 내부 해상도 100%, 최대 60fps로 실행합니다.
이 빌드는 Windows x64용이며, macOS용이 아닙니다.

조작
WASD 이동 / 마우스 시점 / E 상호작용
Shift 달리기 / Ctrl 앉기 / F 손전등 / Q 일반광·UV 전환
T 카트리지 장착 / J 기록 / Esc 일시정지·설정
처음에는 관리실 전화를 받으세요.

현재 내용
DAY 1 프로토타입입니다. 2시간 본편이나 3개 최종 엔딩 완성본은 아닙니다.
UV로 직접 비출 때만 손자국이 보이고, 맵 조명과 손전등 밝기 감소가 반영됐습니다.
테스트와 성능 확인을 위한 개인 시연용 빌드입니다.
'''

count = 0
total = 0
with ZipFile(output, 'w', ZIP_DEFLATED, compresslevel=5) as archive:
    for path in sorted(source.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(source)
        if 'Saved' in rel.parts or path.suffix.lower() in {'.pdb', '.log', '.dmp'}:
            continue
        if len(rel.parts) == 1 and rel.name not in {'NightRulesPrototype.exe', 'NOTICES.txt'}:
            continue
        archive.write(path, f'{name}/{rel.as_posix()}')
        count += 1
        total += path.stat().st_size
    archive.write(runtime, f'{name}/Prerequisites/vc_redist.x64.exe')
    archive.writestr(f'{name}/Play_Laptop.cmd', launcher('-ExecCmds="sg.ShadowQuality 1,sg.PostProcessQuality 0,sg.EffectsQuality 1,sg.TextureQuality 1,r.ScreenPercentage 80,t.MaxFPS 30"'))
    archive.writestr(f'{name}/Play_Standard.cmd', launcher('-ExecCmds="sg.ShadowQuality 3,sg.PostProcessQuality 3,sg.EffectsQuality 3,sg.TextureQuality 3,r.ScreenPercentage 100,t.MaxFPS 60"'))
    archive.writestr(f'{name}/README-KO.txt', readme.encode('utf-8-sig'))
    archive.write(root / 'docs/third-party-assets.md', f'{name}/ThirdPartyAssets.md')
with ZipFile(output) as archive:
    broken = archive.testzip()
    if broken:
        raise SystemExit(f'Corrupt ZIP entry: {broken}')
with output.open('rb') as stream:
    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
output.with_suffix('.sha256').write_text(f'{digest}  {output.name}\n', encoding='ascii')
print(f'ZIP: {output}\nFiles from build: {count}\nBuild size: {total/1024**2:.1f} MiB\nZIP size: {output.stat().st_size/1024**2:.1f} MiB\nSHA256: {digest}', flush=True)
