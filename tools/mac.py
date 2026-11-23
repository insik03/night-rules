"""Local Apple Silicon build/run helper. Uses only the Python standard library."""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'NightRulesPrototype/NightRulesPrototype.uproject'


def static_check():
    if not PROJECT.is_file():
        raise RuntimeError('Run this helper from the complete night-rules source folder.')
    descriptor = json.loads(PROJECT.read_text(encoding='utf-8-sig'))
    if descriptor.get('EngineAssociation') != '5.8':
        raise RuntimeError('This helper targets UE 5.8. Review the engine version first.')
    content = PROJECT.parent / 'Content'
    required = [
        'Data/day1.json', 'Data/voices.json',
        'Fonts/NanumMyeongjo-Regular.ttf', 'Fonts/NanumBrushScript-Regular.ttf',
        'PrototypeAssets/T_ClueHandprint.uasset',
    ]
    # The Mac helper also supports the shared baseline, before the UV-v2 update.
    investigation = PROJECT.parent / 'Source/NightRulesPrototype/NRInvestigation.cpp'
    if investigation.is_file() and 'M_UVHandResidue_v2' in investigation.read_text(encoding='utf-8-sig'):
        required.append('PrototypeAssets/M_UVHandResidue_v2.uasset')
    for name in required:
        if not (content / name).is_file():
            raise RuntimeError('Missing required runtime file: ' + name)
    count = 0
    for path in content.rglob('*'):
        if not path.is_file():
            continue
        with path.open('rb') as stream:
            if stream.read(80).startswith(b'version https://git-lfs.github.com/spec/v1'):
                raise RuntimeError('Unhydrated Git LFS file: ' + str(path.relative_to(ROOT))
                                   + '\nRun git lfs pull --include="NightRulesPrototype/Content/**"')
        count += 1
    print(f'PASS: {count} content files present; no LFS placeholders. Not a Mac build test.', flush=True)


def run(args, **kwargs):
    print('+ ' + ' '.join(str(v) for v in args), flush=True)
    subprocess.run([str(v) for v in args], check=True, cwd=ROOT, **kwargs)


def host_check(engine):
    if platform.system() != 'Darwin':
        raise RuntimeError('Build and play on an Apple Silicon Mac; Windows cannot run this Mac build.')
    if platform.machine() != 'arm64':
        raise RuntimeError('Use a native Apple Silicon terminal/Python (not Rosetta or an Intel Mac).')
    version = tuple(int(v) for v in platform.mac_ver()[0].split('.')[:2])
    if version < (14, 5):
        raise RuntimeError('Use macOS 14.5 or newer for this UE 5.8 development setup.')
    for rel in ['Engine/Build/BatchFiles/Mac/Build.sh', 'Engine/Build/BatchFiles/RunUAT.sh']:
        if not (engine / rel).is_file():
            raise RuntimeError('Missing Mac engine file: ' + str(engine / rel))
    v = json.loads((engine / 'Engine/Build/Build.version').read_text())
    if (v['MajorVersion'], v['MinorVersion']) != (5, 8):
        raise RuntimeError('Install Unreal Engine 5.8, preferably 5.8.3 to match the source assets.')
    xcode = subprocess.check_output(['xcodebuild', '-version'], text=True)
    match = re.search(r'Xcode (\d+)\.(\d+)', xcode)
    if not match or tuple(map(int, match.groups())) < (26, 0):
        raise RuntimeError('UE 5.8 published requirement: full Xcode 26.0+; 26.1.1 recommended.')
    if tuple(map(int, match.groups())) == (26, 4):
        raise RuntimeError('Epic lists Xcode 26.4 as incompatible. Select Xcode 26.1.1 for this setup.')
    subprocess.run(['xcrun', '--sdk', 'macosx', '--find', 'metal'], check=True,
                   stdout=subprocess.DEVNULL)
    print(xcode.strip(), flush=True)
    print('PASS: Mac toolchain preflight. Compilation/rendering still need to run.', flush=True)


def packaged_app():
    apps = list((ROOT / 'Builds/Mac').rglob('NightRulesPrototype.app'))
    if len(apps) != 1:
        raise RuntimeError('Expected one NightRulesPrototype.app under Builds/Mac. Run package first; '
                           'if multiple archives exist, keep the intended build in Builds/Mac.')
    return apps[0]


def app_executable(app):
    import plistlib
    with (app / 'Contents/Info.plist').open('rb') as stream:
        name = plistlib.load(stream)['CFBundleExecutable']
    return app / 'Contents/MacOS' / name


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['check', 'editor', 'package', 'play', 'verify'])
    p.add_argument('--engine', type=Path, default=Path(os.environ.get('UE_ROOT', '/Users/Shared/Epic Games/UE_5.8')))
    p.add_argument('--static', action='store_true', help='check source/assets only; use with check')
    args = p.parse_args()
    if args.static and args.action != 'check':
        p.error('--static is only valid for check')
    if args.action in ('play', 'verify'):
        if platform.system() != 'Darwin' or platform.machine() != 'arm64':
            raise RuntimeError('Play/verify requires an Apple Silicon Mac.')
        app = packaged_app()
        if args.action == 'play':
            run(['open', '-n', app, '--args', '-windowed', '-ResX=1280', '-ResY=720', '-log'])
        else:
            logdir = ROOT / 'Builds/MacVerification'
            logdir.mkdir(parents=True, exist_ok=True)
            for flag, marker in [('NRInvestigationTest', 'NR_INVESTIGATION_COMPLETE'),
                                 ('NRScoreTest', 'NR_SCORE_COMPLETE')]:
                logfile = logdir / (flag + '.log')
                # Remove stale log content before the process starts, not the user's game saves.
                logfile.write_text('')
                run([app_executable(app), '-' + flag, '-windowed', '-ResX=1280', '-ResY=720',
                     '-unattended', '-nosplash', '-abslog=' + str(logfile)], timeout=180)
                text = logfile.read_text(encoding='utf-8', errors='replace')
                if marker + ' failures=0' not in text:
                    raise RuntimeError('Runtime test did not report success: ' + str(logfile))
            print('PASS: Mac investigation and score runtime checks. Manual gameplay QA still required.')
        return
    static_check()
    if args.static:
        return
    engine = args.engine.expanduser().resolve()
    host_check(engine)
    if args.action == 'check':
        return
    run(['bash', engine / 'Engine/Build/BatchFiles/Mac/Build.sh',
         'NightRulesPrototypeEditor', 'Mac', 'Development', '-Project=' + str(PROJECT),
         '-architecture=arm64', '-WaitMutex', '-NoUBA', '-NoUBALocal'])
    if args.action == 'editor':
        run(['open', engine / 'Engine/Binaries/Mac/UnrealEditor.app', '--args', PROJECT])
    else:
        run(['bash', engine / 'Engine/Build/BatchFiles/RunUAT.sh', 'BuildCookRun',
             '-project=' + str(PROJECT), '-noP4', '-platform=Mac', '-clientconfig=Development',
             '-specifiedarchitecture=arm64', '-build', '-cook', '-stage', '-pak', '-package',
             '-archive', '-archivedirectory=' + str(ROOT / 'Builds/Mac'),
             '-map=/Engine/Maps/Entry', '-NoUBA'])
        app = packaged_app()
        run(['lipo', '-verify_arch', 'arm64', app_executable(app)])
        print('Mac package created: ' + str(app))
        print('Next: python3 tools/mac.py verify, then python3 tools/mac.py play')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        sys.exit(1)
