# Apple Silicon macOS 시연 준비 (2026-11-23)

상태: Mac 전용 설정과 빌드 도구 추가. Windows에서 정적 검사(스크립트 문법·arm64 명령 구성·LFS 포인터 거부)를 완료했으며 실제 Mac 컴파일·패키징·플레이 성공은 아직 확인하지 않았다. 이 문서와 소스 묶음은 `.app` 실행파일이 아니다. Intel Mac은 이번 범위 밖이다.

## 실행만 하는 맥에는 엔진이 필요하지 않음
UE와 Xcode는 `.app`을 만드는 **빌드용 맥 한 대**에만 필요하다. 완성된 `Builds/Mac` 패키지를 받은 플레이어는 UE, Xcode, Python 없이 앱을 실행한다. Windows `.exe`나 소스 ZIP 자체는 Mac 실행파일이 아니다. 현재 연결된 Windows에서는 Mac `.app`을 생성하지 않았다.

## GitHub에서 받기
Git과 Git LFS를 설치한 맥에서:

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone --branch feature/apple-silicon-support-20261123 https://github.com/insik03/night-rules.git
cd night-rules
git lfs install --local
git lfs pull --include="NightRulesPrototype/Content/**" --exclude=""
```

이 브랜치는 Mac 지원만 분리한 것으로, 별도 로컬 UV/소품 수정의 공유를 포함하지 않는다. GitHub Download ZIP에는 실제 LFS 에셋이 빠질 수 있으므로 위 명령을 사용한다.

## 맥에서 준비
1. Epic Games Launcher로 **Unreal Engine 5.8 (가능하면 5.8.3)** Mac 버전을 설치한다. Windows용 엔진/실행파일을 복사해 사용하지 않는다.
2. **전체 Xcode**를 설치하고 한 번 열어 초기 구성 및 약관 단계를 직접 완료한다. Command Line Tools만으로는 부족하다. Python 3도 필요하다.
3. 이 맥 지원 브랜치를 clone하고 Git LFS로 Content를 받거나, 제공된 소스 ZIP을 맥의 쓰기 가능한 로컬 폴더에 푼다. ZIP에는 별도의 미공유 게임 변경도 포함되어 있으므로 브랜치와 동일한 스냅샷은 아니다.
4. 터미널에서 프로젝트 루트(clone한 `night-rules` 또는 압축을 푼 `NightRules-Mac-Source`)로 이동한다. 아래 명령은 그 폴더 기준이다.

```bash
python3 tools/mac.py check
bash BuildMac.command
python3 tools/mac.py verify
bash PlayMac.command
```

엔진 경로 기본값은 `/Users/Shared/Epic Games/UE_5.8`이다. 다른 위치에 설치했다면:

```bash
python3 tools/mac.py check --engine "/설치한/UE_5.8"
bash BuildMac.command --engine "/설치한/UE_5.8"
```

에디터로 직접 열기: `python3 tools/mac.py editor`. .command 파일을 더블클릭할 경우 먼저 `chmod +x BuildMac.command PlayMac.command`를 할 수 있다. 위 `bash` 실행은 실행 권한 변경 없이 가능하다.

## 환경 요구와 확인 범위
Epic의 UE 5.8 문서는 개발 환경을 macOS 14.5 이상, Xcode 26.0 이상(26.1.1 권장)으로 안내하고, Xcode 26.4는 비호환이라고 명시한다. 설치된 5.8.3의 SDK JSON에는 더 넓은 허용 범위(macOS 14.0/Xcode 15.2~27.9)가 기록되어 있어 차이가 있다. 이 도구는 첫 빌드에서 공식 권장 범위를 보수적으로 사용한다. 실제 맥의 버전은 아직 확인하지 않았다. 이는 에디터 개발 환경 기준이며 게임의 최종 최소 사양/프레임 보장이 아니다.

공식 근거:
https://dev.epicgames.com/documentation/unreal-engine/macos-development-requirements-for-unreal-engine?application_version=5.8

## 변경
- `Config/Mac/MacEngine.ini`: arm64, Metal SM5, Nanite/가상 섀도/레이 트레이싱 비활성화. M1 계열에서 먼저 검증할 보수적 설정이며 기존 모델의 fallback 렌더 결과는 Mac 실기에서 확인해야 한다.
- `Config/Mac/MacGameUserSettings.ini`: 최초 1280×720 창 모드, VSync/60fps 제한. 기존 저장 설정은 우선 적용될 수 있다.
- Mac 로컬 테스트용 Sign to Run Locally. 유료 Apple 계정·팀 ID를 임의로 만들지 않는다. 공개 배포 서명·공증 및 Steam Mac depot 작업은 별도다.
- `tools/mac.py`: Git LFS 포인터·필수 런타임 파일·Mac/arm64·엔진·Xcode/Metal 검사, Editor 빌드, Mac cook/package, 실행 및 기존 런타임 검사.
- Windows 코드/그래픽, 맵 치수, 이야기, 유료 에셋은 변경하지 않는다. DX12 설정은 원래 Windows 플랫폼 섹션에만 적용되어 있어 삭제할 필요가 없다.

## 결과와 검증
패키지: `Builds/Mac` 아래 `NightRulesPrototype.app`. 실제 게임 코드는 이 앱과 동봉 패키지 파일을 함께 배포해야 하므로 앱만 임의로 떼어내지 않는다.

`verify`는 개발 빌드에서 NRInvestigationTest/NRScoreTest를 각각 실제 실행하고 현재 실행 로그의 failures=0을 확인한다. 렌더러를 끄지 않으며 화면이 잠시 열린다. 로그는 `Builds/MacVerification`에 저장한다. 성공 후에도 다음은 직접 확인한다:
- WASD/마우스 시점, Esc 메뉴와 복귀, 음량/감도 저장과 재실행
- 한글 자막·수칙·전화 및 효과음·CoreAudio 출력
- 일반 손전등에서는 손바닥이 숨겨지고 UV 빛에서만 보이는지
- CCTV 화면/주인공, 문·서랍, 기어다니기·추격·체크포인트
- 최종밤 3개 분기 테스트와 15분 이상 플레이 성능/발열

현재 Windows 정적 검사 성공을 Mac 실행 성공으로 해석하지 않는다. Mac 테스트 로그를 받은 뒤 호환성 문제를 고친다. 공개 배포 전에는 별도 서명/공증과 최종 사양 검증을 해야 한다.
