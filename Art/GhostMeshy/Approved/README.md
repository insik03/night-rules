# 해담고시원 — 웃는 전임 총무 (2026-10-12)

사용자가 승인한 `concept-approved.png`를 기준으로 제작한 Meshy 모델이다.
기존 폴더 상위의 거절된 모델 및 기존 `/Game/PrototypeAssets/Ghost` 임시 모델과 구분한다.

## 파일

- `reference-a-pose.png`: 승인한 디자인을 한 명의 정면 A 포즈로 정리한 생성 입력.
- `textured.glb`: Meshy 원본, 714,682면.
- `rig-input.glb`, `optimized-source.blend`: Blender에서 89,999면, 키 215cm로 정리한 모델.
- `rigged.glb`, `walking.glb`, `running.glb`: Meshy가 반환한 원본 뼈대와 기본 모션.
- `A_CaretakerRun.blend`: 기괴한 달리기로 수정한 Blender 작업 파일.
- `A_CaretakerWalk.blend`: 걷기 작업 파일.
- `Unreal/`: 재현 가능한 FBX 3종과 BaseColor/Normal/ORM 텍스처.
- `meshy-preview.png`: Meshy 실제 모델의 렌더 미리보기.
- `run-pose-04.png`, `run-pose-12.png`: 수정된 뼈대의 실제 Blender 렌더.
- `creepy-run-preview.mp4`: 게임의 최대 추격 속도에 맞춘 재생률로 렌더한 달리기 영상. 이동 없는 스튜디오 프리뷰다.
- `provenance.json`: 작업 ID, 비용, 출처 및 AI 공개 기록. 임시 서명 URL은 Git에 넣지 않는다.

## 게임 연결

`/Game/PrototypeAssets/GhostMeshy/SK_SmilingCaretaker`와 같은 폴더의
`A_CaretakerWalk`, `A_CaretakerRun`, `M_Caretaker`를 사용한다.
옛 전면/후면 이미지 투영 재질을 덮어씌우지 않는다.
기존 출현·추격·사망 사건의 타이밍은 유지하며 모델과 움직임을 교체한다.

달리기는 머리를 26도 기울여 고정하고 상체를 앞으로 기울였다.
오른팔은 늘어뜨리고 왼팔은 크게 움직여 비대칭을 만들었다.
다리에는 보폭 보정과 바닥 침범 보정을 적용했다.
추격 속도는 260→340cm/s, 주인공은 걷기 220/달리기 350cm/s다.
실제 이동량에 따라 모션 재생 속도와 발소리 간격을 조절한다.

## 재현

Blender에서 `tools/optimize_meshy_ghost.py` → `tools/prepare_meshy_ghost.py` 순서로 실행한다.
첫 단계 이후의 Meshy 리깅은 이미 완료돼 있으므로 다시 결제해 생성할 필요가 없다.
모션 수정만 할 때는 `prepare_meshy_ghost.py`부터 실행한다.
`tools/build.ps1 -EngineRoot <UE 경로> -ImportMeshyGhost -Package`로 가져오고 패키징한다.
`tools/preview_meshy_ghost.py`는 실제 포즈와 발 높이를 확인한다.

## 생성 입력 요약

내장 image_gen으로 승인된 시트의 인물 한 명을 회색 배경의 정면 A 포즈로 정리했다.
입과 눈, 화상 피부, 대머리, 긴 목과 팔, 총무 조끼와 열쇠를 보존하도록 지정했다.
Meshy에는 이 이미지와 다음 텍스처 지시를 사용했다:

> Bald burned night caretaker. Realistic pale human skin with fused burn scar folds. Empty black sunken eye sockets with no eyes or highlights. Extremely wide sinister smile with small human teeth. Scorched navy vest, dirty beige shirt, dark grey trousers, bare feet. Preserve the reference face and clothing, no scales, no glowing eyes.

모델+4K 텍스처 30, 리깅+기본 걷기/달리기 5, 이번 제작 합계 **35크레딧**.
추가 리메시·특수 애니메이션 유료 생성 없이 Blender에서 수정했다.
원본 작업 ID와 폴더는 `provenance.json`에 있다.

## 검증

- Windows Development 패키징 성공.
- `NRGhostPreview`: 새 스켈레탈 메시/모션 로드. 처음 발견한 회색 기본 재질 문제는 슬롯 구조체 재할당으로 수정하고 재촬영해 PBR 색상 표시를 확인했다.
- `NRSmokeTest`, `NRChaseTest`: failures=0. 복도에서 초당 340cm 이동 로그 확인, 코너를 돌아 정지한 플레이어 포획 및 사망 확인.
- `NRPolishTest`: failures=0. 새 `LeftLeg` 뼈대의 실제 변형, 대사, 계단 이동 확인.
- `NRFeedbackTest`: failures=0. WASD/Shift/앉기 입력 등 기존 기능 확인.
- `NRRunPreview`: 최종 재질이 적용된 기울어진 고개와 비대칭 팔 달리기를 실행본에서 촬영했다.
- Blender의 20개 샘플 프레임에서 최저 표면 높이 약 0.004m. 공중 동작 구간은 최대 약 0.114m다.
- 발 디딤 구간의 추정 속도 367.4cm/s를 기준으로 게임 이동 속도에 맞춰 재생률을 조절한다.

실제 게임 스크린샷은 `Art/Previews/NRGhostPreview.png`, `Art/Previews/NRRunPreview.png`.
6개 주요 확인 항목을 통과했으나 추격 난이도의 체감은 사용자 플레이테스트로 추가 조정한다.
모델의 피부 세부는 이미지 시안을 3D로 재구성한 결과이며 시안과 픽셀 단위로 동일하지 않다.

## 추가 모션 — 기어가기 (2026-11-03)

- Meshy Animation API, action 340 `Crawl_and_Look_Back`, 기존 리깅 작업 `01a12c22…`에 적용. 작업 ID `01a1a174-d129-76de-83f3-9d2386e6049b`, **3크레딧**(사용자 승인).
- 원본 `crawl.glb` → `tools/prepare_meshy_crawl.py`(Blender) → `Unreal/A_CaretakerCrawl.fbx` → `tools/import_meshy_crawl.py`.
- 6.92초, 24fps, 앞으로 약 3.7m 이동(루트 모션 유지). 측정값과 렌더: `crawl-inspection.json`, `crawl-pose-0..3.png`.
- 게임: 정전 중 복도를 바라볼 때 6.5m 앞에서 한 번 등장(`NRScore.cpp` TickCrawlScare). 서명 URL은 저장하지 않았다.
