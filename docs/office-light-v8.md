# 관리실 조명 위치·밝기 수정

2026-10-12. 사용자가 관리실 내부가 지나치게 어둡다고 지적한 화면 기준으로 수정.

## 원인과 변경

- 형광등 모델은 OfficeAssembly와 함께 옮겨졌지만 실제 PointLight는 기본 정적 광원 상태에서 SetWorldLocation을 호출하고 있었다. 이전 캡처 로그에도 광원을 옮기려면 Movable이어야 한다는 경고가 있었다.
- 관리실 광원을 처음부터 최종 위치 `(270, -620, 235)`에 생성한다. 이전 위치에서 이동시키던 코드는 제거했다.
- 관리실 광원을 Movable로 설정하고 기본 입력 밝기를 1800에서 3200으로 조정했다. 기존 70% 배율 적용 후 실제 강도는 2240이다. 적용 범위 600cm, SourceRadius 12cm, SourceLength 80cm로 천장 형광등의 부드러운 조명을 만든다.
- 색은 약간 따뜻한 중성 백색으로 조정했다. 복도·손전등 강도와 화면 노출은 변경하지 않았다.
- 기존 InteriorLights와 LightIntensities에 등록되므로 정전과 복구 시 같은 광원이 제어된다.

## 확인

Windows 패키지 빌드 성공 (`tools/output/build-office-light-v8.log`). 최종 실행파일에서 관리실 내부·현관·규칙표·손전등 조명 없이 보기의 4개 화면을 `Art/Previews/Architecture-v8`에 촬영했다.

손전등 스포트라이트 표시를 끄고도 책상·전화·서류가 보이는 것을 확인했다. 해당 캡처는 `ShowFlag.SpotLights 0`을 사용하며 이미지 밝기를 후처리하지 않았다.

- NRDemoTest: failures=0. 실제 조명 정전, 퓨즈로 전력 복구, 체크포인트 조명 복구 통과.
- NRFeedbackTest: 추격 중 복도 깜빡임과 관리실 점등 유지 항목 통과. 전체 검사에서는 서랍 카트리지 시선 검사 1건 실패. 이 검사는 NRFeedback.cpp에서 이전 관리실 좌표 Eye(-100,-346,147)를 고정 사용하며, 현재 배치에 맞춘 별도 점검이 필요하다. 이번 조명 변경으로 서랍 동작·좌표는 변경하지 않았다.
- 검사 기록: `tools/output/office-light-v8-tests.log`. 전체 검사 통과로 표기하지 않는다.

실행파일은 `Builds/Windows/NightRulesPrototype.exe`, 전후 비교는 `docs/office-light-v8.html`.
