# 팀원 설치 및 첫 작업

## 환경
- Windows PC, Unreal Engine **5.8.3**. 엔진은 Epic Games Launcher에서 본인 계정으로 설치합니다.
- Git for Windows + Git LFS.
- Visual Studio 2022: C++를 사용한 게임 개발/데스크톱 개발, MSVC v143, Windows 11 SDK, .NET Framework 4.8 SDK.
- 현재 기준 도구: MSVC 14.44.35207, Windows SDK 10.0.26100.0.
- Python 3.12 이상: 저장소 검사와 일부 제작 도구용.
- Blender 5.2.2 LTS: 모델 담당자만 필요합니다.
- 외부 AI 서비스 계정이나 유료 생성은 게임 실행에 필요하지 않습니다.

## 내려받기
작업 폴더는 OneDrive 밖의 영문 경로를 권장합니다.

```powershell
git lfs install
git clone https://github.com/insik03/night-rules.git C:\Projects\night-rules
cd C:\Projects\night-rules
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\team\Setup-Team.ps1
```

`.lfsconfig`는 기본 에셋 다운로드를 `NightRulesPrototype/Content/**`로 제한합니다. 약 1.1 GiB이며 앞으로 변경될 수 있습니다. 다른 `Art` 파일이 작은 텍스트로 보이는 것은 아직 해당 원본을 받지 않았기 때문입니다.

## 모델 담당자가 원본 추가로 받기
```powershell
git lfs pull --include="Art/Characters/Residents-Tripo-v1/**" --exclude=""
git lfs pull --include="Art/EnvironmentConcepts/**,Art/GeneratedProps/**" --exclude=""
```

필요한 경로만 선택하세요. 전체 원본은 `git lfs pull --include="*" --exclude=""`로 받지만 다운로드 용량과 LFS 사용량이 커집니다.

## 첫 빌드
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\build.ps1 -EngineRoot "C:\Program Files\Epic Games\UE_5.8"
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\team\Open-Editor.ps1
```

이미 반입한 `.uasset`이 포함되어 있으므로 처음 받았다고 `-ImportAssets`를 붙이지 않습니다. 이 옵션은 초기 임시 에셋을 다시 반입합니다. 특정 에셋을 수정한 담당자만 해당 반입 도구를 사용합니다.

에디터에서 Play하면 코드로 고시원 맵이 생성됩니다. Enter/Esc/이동 등 실제 입력과 새 입주민의 문틈 대화를 확인하세요. 게임 로직은 `NRGame.cpp`, 구조는 `NRArchitecture.cpp`, 주민은 `NRResidents.cpp`에 있습니다.

## 팀원 권한
공개 저장소는 누구나 clone할 수 있습니다. 직접 작업 브랜치를 push하려면 초대를 수락해야 합니다.
초대 수락: https://github.com/insik03/night-rules/invitations

`hdj2004723`는 write 권한으로 초대 대상입니다. 수락 여부는 GitHub의 저장소 초대 화면에서 확인합니다. 원본 저장소 직접 작업은 브랜치 → Pull Request → 검토 → 병합 순서입니다.

## 파일 잠금
```powershell
git lfs lock "NightRulesPrototype/Content/PrototypeAssets/ResidentsV1/Minseo/SK_Minseo.uasset"
# 작업/PR 병합 후
git lfs unlock "NightRulesPrototype/Content/PrototypeAssets/ResidentsV1/Minseo/SK_Minseo.uasset"
```

잠그지 않은 바이너리 파일은 읽기 전용일 수 있습니다. 전체 파일의 읽기 전용 속성을 강제로 풀지 마세요.

## 문제 해결
- 메시/텍스처가 비어 있음: `git lfs pull --include="NightRulesPrototype/Content/**" --exclude=""`.
- 모듈/DLL 없음: 위의 첫 빌드를 실행합니다. DLL은 저장소에 올리지 않습니다.
- 다른 엔진으로 업그레이드하라는 창: 팀의 5.8.3 버전을 먼저 맞춥니다.
- 에디터 Entry 맵이 비어 있음: 현재는 런타임 생성 구조이므로 Play로 확인합니다.
- `Art`의 GLB/PNG가 안 열림: 해당 경로를 LFS로 추가 다운로드합니다.
- `main` push가 거부됨: 작업 브랜치로 올리고 PR을 사용합니다.
- LFS 한도 오류: 관리자에게 알립니다. 자동 과금/요금제 변경을 하지 않습니다.

## 기존 PC와 공유 폴더
기존 제작 폴더와 Git 이력은 보존되어 있습니다. 공개 저장소는 개인정보/임시 응답을 제외한 2026-11-12 작업 스냅샷에서 시작합니다.
관리자 PC의 공용 작업 복사본: `%USERPROFILE%\Projects\night-rules`.
앞으로 팀과 교환할 변경은 공용 작업 복사본에서 진행하세요. 이전 폴더의 변경을 가져올 때는 필요한 파일만 검토 후 복사하고, 서로 다른 Git 이력을 강제 푸시하지 않습니다.
