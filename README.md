# 야간수칙 · 해담고시원

엔투엔의 Windows PC 심리공포 게임 개발 저장소입니다. Unreal Engine **5.8.3**을 사용합니다.

**팀원 시작 안내: [docs/team-setup.md](docs/team-setup.md)**  
**협업 규칙: [CONTRIBUTING.md](CONTRIBUTING.md)**

## 처음 받기

Git for Windows와 Git LFS를 설치한 뒤 PowerShell에서 실행합니다.

```powershell
git lfs install
git clone https://github.com/insik03/night-rules.git C:\Projects\night-rules
cd C:\Projects\night-rules
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\team\Setup-Team.ps1
```

기본 다운로드는 게임에 필요한 `NightRulesPrototype/Content`입니다. 모델링 원본은 Git LFS에 보관하며 작업에 필요한 폴더만 추가로 받습니다. GitHub의 **Download ZIP 대신 git clone**을 사용하세요.

## 빌드와 열기

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\build.ps1 -EngineRoot "C:\Program Files\Epic Games\UE_5.8"
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\team\Open-Editor.ps1
```

첫 빌드에는 Visual Studio 2022의 C++ 도구, Windows SDK, .NET Framework 4.8 SDK가 필요합니다. 엔진과 개인 로그인 정보는 이 저장소에 포함되지 않습니다.

## 현재 상태

- DAY 1 프로토타입과 독립 최종밤 TRUE / RED / BLACK 분기를 개발하고 있습니다.
- 첫 회차 2시간 · 5일 · 엔딩 3개는 제품 목표이며 본편 완성 상태가 아닙니다.
- 입주민 6명의 에셋과 배치 코드가 포함되어 있습니다. 최신 변경의 전체 엔진 빌드·패키지 검증은 아직 남아 있습니다.
- `main`은 검토를 거쳐 합치는 공유 기준입니다. 초기 공개 스냅샷 자체를 출시/QA 완료 버전으로 간주하지 않습니다.
- CI의 `repository-checks`는 저장소·데이터·스크립트 검사이며 Unreal 컴파일/실플레이 검사가 아닙니다.
- 맵은 **게임 시작 시 C++로 생성**됩니다. 에디터의 Entry 맵이 비어 보여도 Play 시 생성되며, 에디터에서 임의로 옮긴 가구는 현재 배치 코드에 저장되지 않습니다.

## 작업 위치

| 영역 | 위치 |
|---|---|
| 게임 코드 | `NightRulesPrototype/Source/NightRulesPrototype` |
| 사건·대사 데이터 | `NightRulesPrototype/Content/Data` |
| 반입된 게임 에셋 | `NightRulesPrototype/Content/PrototypeAssets` |
| Blender/FBX/GLB 원본 | `Art` |
| 설계 치수 | `Art/EnvironmentConcepts/unified-v15/furniture-layout.json` |
| 스토리 | [스토리 v0.3](docs/story-plan-v03.md) |
| 공간 구조 | [통합 설계](docs/floor-plan-unified-v15.md) |
| 에셋 출처 | [외부 에셋](docs/third-party-assets.md), [AI 에셋](docs/ai-assets.md) |

실행파일·빌드 캐시·개인 제출 서류·서비스 로그인/임시 다운로드 응답은 공유하지 않습니다. 실행파일이 필요한 시연자는 별도 패키지를 받습니다.

## 공개 범위와 권리

공개 저장소 설정은 일반적인 재사용 라이선스를 부여한다는 뜻이 아닙니다. 프로젝트 전체에 MIT/Apache 등 오픈소스 라이선스는 부여하지 않았습니다. 외부 자료에는 해당 원본 라이선스가 적용됩니다. [출처와 공개 범위](docs/team-assets.md)를 확인하세요.
