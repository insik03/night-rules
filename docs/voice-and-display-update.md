# 한국어 음성 및 화면 개선 — 2026-10-09

> 후속 변경: [데모 보완 기록](demo-polish-2026-10-09.md). 현재 버전은 실제 대화 29줄만 더빙하며 문서·조사 설명·독백은 자막만 표시한다.

## 당시 적용 범위
- 민서의 첫 전화 3문장에 사전 생성 한국어 음성 적용. 다른 대사는 현재 자막만 사용한다.
- 모델: Supertone/supertonic-2, F1 기본 프리셋. 실존 인물 목소리 복제 없음.
- 원본 모델: https://huggingface.co/Supertone/supertonic-2
- 모델 라이선스: OpenRAIL-M. 원문은 Art/Voice/MODEL_LICENSE.txt 및 manifest.json 링크 참조.
- 생성 도구: tools/create_voice_sample.py. 로컬 ONNX 추론, seed 203, 8 steps, speed .92.
- 실행 조건: numpy, onnxruntime 및 tools/output/tts 아래 공식 모델의 onnx/voice_styles와 공식 Python helper.py 필요. 모델 자체는 Git 또는 게임 배포에 포함하지 않는다.
- 전화 음질 후처리: 240Hz~3800Hz 대역 제한, peak 0.65. 파일별 대사·길이·SHA256은 Art/Voice/manifest.json에 기록.
- Steam Content Survey 작성 시 게임에 포함된 사전 생성 AI 음성 3개를 AI 사용 내역에 포함한다. 기존 생성 이미지 등은 별도 내역과 합산한다.
- 최종 성우 연기 품질은 미확정이며, 사용자의 청취 후 프리셋·속도·문장 호흡을 조정한다.

## 조작과 제한
- 야간수칙: 벽에서 바로 읽고 E로 확대. 붉은 글씨도 스토리 상태에 따라 벽면에 나타난다.
- CCTV: 현장 카메라 갱신, 최근 약 60초의 2fps 화면 기록, 탐색 막대와 실시간 복귀. 음성 녹음이나 전체 세션 저장 기능은 없다.
- CCTV 기록은 현재 실행의 메모리에만 유지하며 체크포인트 복귀 시 초기화한다. 전원이 꺼지거나 이야기상 화면이 멈추면 새 영상을 기록하지 않는다.
- CCTV 확인 중에는 시간이 흐른다. 일반 문서와 일시정지에서는 사건 진행을 멈춘다.
- 자막: 배경 박스 제거, 외곽선과 그림자 유지. 조준점은 탐색 중 중앙에만 표시.
- Esc → 설정: 마우스 감도 0.2~3.0배, 전체 음량 0~100%. 즉시 적용 및 다음 실행에도 유지.
- 음성은 대사별로 재생하고, 자막 최소 유지시간을 음성 길이에 맞춘다. 일시정지/문서 열람 중 함께 멈추며 대사 교체·사망·체크포인트 복귀 시 중단한다.

## 검증
실행 검증은 tools/verify_experience.ps1로 수행한다. 소스 컴파일, 패키징과 함께 결과를 tools/output에 기록한다.

2026-10-09 최종 확인: Windows Development 패키징 성공. NRExperienceTest, NRPresentationTest, NRFeedbackTest, NRSmokeTest 모두 failures=0. 녹화 RGB 픽셀과 재생 프레임 일치 검증. 벽면 수칙·설정·자막·CCTV 되감기·책상 모니터 캡처를 직접 확인했다. UI용 불투명 머티리얼로 녹화 영상의 알파 때문에 화면이 사라지는 문제를 수정했고, CRT 표시 평면을 하우징 밖으로 옮겼다. 음성의 자연스러움과 연기는 사용자 청취 평가가 남아 있다.
