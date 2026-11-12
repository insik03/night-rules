# UE Project Context — 야간수칙
확인일: 2026-11-01. 파일로 확인한 사실과 사용자 목표를 구분한다.

## 엔진 / 제품
- `NightRulesPrototype/NightRulesPrototype.uproject`: EngineAssociation 5.8.
- 설치 엔진 `C:/Program Files/Epic Games/UE_5.8`, Build.version: 5.8.3, CL 58210709.
- Windows PC 싱글플레이, Steam 출시 목표. 서버/네트워킹은 제품 요구사항이 아니다.
- 시제품은 DAY 1 + 독립 최종밤 엔딩 테스트이며 2시간 전체 본편 완성 상태가 아니다. 최신 스토리 검토안: `docs/story-plan-v03.md`, 구현 한계: `docs/endings-v1.md`.

## 실제 코드 구조
- Runtime 모듈: NightRulesPrototype, LoadingPhase Default.
- Game / Editor targets: NightRulesPrototypeTarget / NightRulesPrototypeEditorTarget. BuildSettings와 IncludeOrder는 Latest.
- Build.cs 의존성: Core, CoreUObject, Engine, InputCore, Slate, SlateCore, Json, AudioMixer.
- 현재 C++ 중심이다. 오래된 PRD의 Blueprint 중심 계획을 현재 구현으로 오인하지 않는다.
- 프레임워크: ANRController(APlayerController), ANRPlayer(ACharacter), ANRGameMode(AGameModeBase), ANRProp(AActor), 선언은 NRGame.h. API 매크로 NIGHTRULESPROTOTYPE_API.
- 시작 맵 /Engine/Maps/Entry, GlobalDefaultGameMode /Script/NightRulesPrototype.NRGameMode. 게임 시작 시 코드로 공간을 구성한다. 에디터의 빈 Entry 맵이 실제 플레이 맵 전체라는 가정은 금지.
- 주요 파일: NRArchitecture.cpp(구조), NRCoreProps.cpp(소품), NRCCTV.cpp(CCTV), NRInvestigation.cpp(조사), NRComplaintLog.cpp(일지), NRChoice.cpp(선택), NREndings.cpp(엔딩), NRPursuitPresentation.cpp(추격 연출).

## 입력 / UI / 플러그인 / 렌더
- DefaultInput.ini에는 legacy ActionMappings/AxisMappings와 EnhancedPlayerInput/EnhancedInputComponent 기본 클래스가 함께 있다. NRGame.cpp는 BindAxis/BindAction을 실제 사용한다. InputAction 기반으로 이미 전환되었다고 가정하지 않는다.
- UI 의존성은 Slate/SlateCore. UMG 스킬 사용 때문에 기존 UI를 자동 재작성하지 않는다.
- .uproject 명시 항목: PythonScriptPlugin=true(Editor), AndroidFileServer=false. 엔진 기본 활성 플러그인 전체 목록은 아직 조사하지 않았다.
- 새 GAS, Mass, Mover, StateTree, PCG, NavMesh 등은 설치된 스킬 이름만으로 현재 구현이라고 간주하지 않는다. 해당 작업에서 기존 구현과 모듈 의존성을 먼저 조사한다.
- DefaultEngine.ini: DX12, AutoExposure=False, DynamicGlobalIlluminationMethod=0, ReflectionMethod=0, MotionBlur=False. Lumen 등을 스킬 예제 때문에 일괄 활성화하지 않는다.
- 디스크 저장/Steam SDK/업적/클라우드의 완료 여부는 해당 코드와 실행 결과로 확인한다. README의 과거 기록만으로 현재 완료를 주장하지 않는다.

## 빌드 / QA
- `tools/build.ps1 -EngineRoot 'C:/Program Files/Epic Games/UE_5.8'`.
- 에셋 반입 필요 시 -ImportAssets, Windows 패키지 필요 시 -Package. 코드와 맞는 최신 빌드 여부 확인 후 PlayDemo.cmd 사용.
- tools/verify_ghost.ps1, verify_office_cctv.ps1, verify_protagonist.ps1, verify_demo.ps1 등 작업별 검증 스크립트를 먼저 읽고 적합한 것만 실행한다.
- 일반 테스트의 성공으로 2시간 플레이타임/공포감/전체 엔딩 QA를 입증하지 않는다.
- Git + LFS 사용. 에셋 수정 시 .gitattributes를 따른다. 별도 blog-writer 작업은 범위 밖이다.

## 스킬 사용
- UE 스킬은 UE 5.8 대상이며 로컬 엔진 헤더가 최종 API 기준이다.
- .agents/skills-lock.json에 설치 버전을 고정한다. 외부 스킬 업데이트는 프로젝트 설정을 보존한다.
- 이번 설정은 코드/CLI 작업용이다. Epic 공식 Unreal MCP 서버 및 Claude 플러그인은 설치/활성화하지 않았다. 에디터 연결이 있다고 주장하지 않는다.
