# 야간수칙 / 해담고시원 — 프로젝트 작업 기준

## 작업 시작
- 이 파일이 있는 폴더를 프로젝트 루트로 사용한다. 이전 `바탕 화면/Game_pm` 절대 경로를 하드코딩하지 않는다.
- UE 작업은 `.agents/ue-project-context.md`, Blender 작업은 `.agents/blender-project-context.md`를 먼저 읽는다.
- `.agents/skills/`의 스킬은 관련 작업에 필요한 것만 읽는다. 전체 묶음을 한꺼번에 로드하지 않는다.
- 최신 사용자 지시와 현재 프로젝트의 실제 코드/API가 외부 스킬의 일반 예제보다 우선한다. 외부 예제의 자동 장면 초기화, 자동 모듈 전환, 자동 게시를 그대로 실행하지 않는다.

## 작업별 스킬
| 작업 | 우선 읽을 스킬 |
|---|---|
| 귀신 추격·이동 | ue-ai-navigation, ue-character-movement, ue-animation-system |
| 숨소리·발소리·의자 소리 | ue-audio-system |
| 조사·일지·엔딩·저장 | ue-data-assets-tables, ue-serialization-savegames, ue-testing-debugging |
| CCTV·UV·조명 | ue-materials-rendering, ue-testing-debugging |
| 입력·메뉴·자막 | ue-input-system, ue-ui-umg-slate; 실제 legacy binding/Slate 구조 유지 |
| 가구·맵 모듈 | text-to-blender, blender-modeling, reference-to-3d |
| 검수·게임 반입 | reference-analysis-validator, blender-uv-texturing, blender-export |
| 스토리 문서·데이터 대조 | story-consistency-check |
| 사용자 플레이 피드백 정리 | playtest-report |
| 일정·범위 계획과 점검 | milestone-plan |

## 설계와 치수
- 현행 검토 도면: `docs/floor-plan.html`, 설명: `docs/floor-plan-unified-v15.md`.
- 배치·목표 치수: `Art/EnvironmentConcepts/unified-v15/furniture-layout.json`. 모델링 검토본 실측: `Art/EnvironmentConcepts/dimensioned-furniture-v1/dimensions.json`.
- 런타임 구조: `NRGame.h`의 NRLayout, `NRArchitecture.cpp`, `NRGame.cpp`. 설계도와 코드가 다르면 차이를 보고하고 임의로 어느 쪽도 승인된 새 설계로 바꾸지 않는다.
- 수치는 cm로 명시한다. 폭·깊이·높이와 배치 회전을 구분하고, 벽 중심선 치수를 유효 통로 폭으로 보고하지 않는다.
- 최종 비율에 맞춰 처음부터 형상을 제작한다. 완성 모델의 비균등 스케일로 폭을 억지로 맞추지 않는다. 균등 단위 변환과 Apply Scale은 왜곡 수정의 대체가 아니다.
- 옷장 두 개는 침대 발치에 나란히 두는 배치가 기준이다. 현행 검토본은 각 45×45×175cm이다. 더 얇게 만들자는 후속 제안은 거절/미확정이므로 확정 치수로 채택하지 않는다. 발치 여유 39.5cm는 유지한다. 2026-11-01 Blender 검토 v2에서 각 옷장을 21.5cm 문짝 두 개로 바꿔 90도 개방 시 침대 여유 약19cm를 확보했다. 기준 모델은 Art/EnvironmentConcepts/furniture-review-v2/haedam-furniture-reviewed.blend이며 런타임 반입은 별도다.
- 문·서랍·옷장문은 별도 부품과 실제 회전/슬라이드 축을 갖게 한다. 닫힌 상태, 열린 상태, 플레이어 통행을 각각 검사한다.
- 수치 일치 외에도 실제 렌더를 확인한다. 도면/Blender 프리뷰를 게임 반영 완료나 런타임 충돌 통과의 증거로 제시하지 않는다.

- 최신 가구 개폐 검토: `docs/furniture-review-v2.html`, 실측: `Art/EnvironmentConcepts/furniture-review-v2/audit.json`. v1은 원본 보존용이며 단문 재생성 결과를 최신 수정본으로 덮어쓰지 않는다.

## 제품과 검증
- 현재 제품 목표는 첫 회차 약 2시간, 5일, 엔딩 3개다. 시제품 상태와 목표를 분리한다. 기존 PRD의 4개 엔딩/70~100분을 최신 요구사항으로 되돌리지 않는다.
- 일반광에서는 UV 손자국을 숨기고 UV에서만 보이게 한다. 관찰 가능한 증거를 설명 자막이 대신 정답으로 알려주지 않는다.
- 추격 빈도는 낮게 유지하고 이야기 맥락·전조를 연결한다. 귀신 이동 거리와 발 접촉/애니메이션 속도를 함께 확인한다.
- Meshy/Tripo 등 유료 생성의 현재 지시는 추가 크레딧 사용 금지다. 새 유료 생성은 사용자가 새로 허용한 범위에서만 한다. 소품/맵 생성 전 이미지 검토라는 기존 요청도 유지한다.
- 엔진/Blender 원본, 생성 프리뷰, 임포트 결과, 패키지 실플레이를 구분해서 보고한다. 실제 실행하지 않은 검증을 통과했다고 쓰지 않는다.
- 수정 후 관련 빌드/검증만 실행한다. Git의 사용자 변경을 보존한다. 이번 스킬 설정은 게임 바이너리·에셋·스토리를 변경하는 작업이 아니다.

## 팀 공유 환경 (2026-11-12)
- 현재 공용 저장소: https://github.com/insik03/night-rules (public).
- 첫 설치: docs/team-setup.md, 작업 규칙: CONTRIBUTING.md.
- main 직접 수정/푸시보다 작업 브랜치와 Pull Request를 사용한다.
- .agents/skills 패키지는 공개 저장소에 포함하지 않는다. 설치되지 않은 스킬을 실행한 것처럼 보고하지 않는다. 필요하면 skills-lock.json의 원본 저장소에서 설치한다.
- 과거 개발 기록의 절대 경로를 새 팀원의 PC에 그대로 적용하지 않는다. 프로젝트 루트 기준 상대 경로를 우선한다.
- CI 저장소 검사 통과와 Unreal 빌드/패키징/실플레이 성공을 구분한다.
