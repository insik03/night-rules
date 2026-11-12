# 노트북 개인 시연 빌드

2026-10-12: 현재 DAY 1 프로토타입을 Windows x64 독립 실행 ZIP으로 묶었다.

- 대상 사용자 사양: Intel i7 11세대 / NVIDIA MX450 / RAM 16GB.
- 파일: `Builds/Portable/NightRules-Demo-20261012.zip` (659.2 MiB).
- `Play_Laptop.cmd`: 1280×720 창 모드, 렌더 해상도 80%, 최대 30fps, 그림자/효과/텍스처 품질 1, 후처리 0.
- `Play_Standard.cmd`: 같은 창 크기, 렌더 해상도 100%, 최대 60fps, 위 품질 값 3.
- Visual C++ x64 런타임 설치파일, 한국어 안내 및 에셋 출처 문서 포함.
- 개발 로그, 저장 데이터, 디버그 심볼 제외. Unreal Editor 또는 Steam 설치 불필요.

재생성: `python tools/package_portable_demo.py --tag <새 버전 이름>`.
기존 ZIP을 덮어쓰지 않으므로 변경할 때 새 태그를 지정한다.

검증: ZIP 전체 CRC 검사 통과. 별도 폴더로 압축을 푼 실행파일을 노트북용 옵션과 함께 실행하여 `NR_DEMO_COMPLETE failures=0`, 종료 코드 0 확인.
테스트 로그: `tools/output/portable-demo-test.log`.
실제 MX450 노트북 프레임, 새 Windows 설치 환경 및 런처 수동 더블클릭은 아직 검증하지 않았다. 30fps는 설정 상한이며 보장 성능이 아니다.
