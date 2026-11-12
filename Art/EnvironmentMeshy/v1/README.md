# 해담고시원 건축 제작 v1

승인 기준: `Art/EnvironmentConcepts/v14-fixture-access/floor1-master.png`.
범위: 3개 거주층과 옥상, 단일 복도, 관리실/창고, 독립 주방·화장실·샤워실.
신규 작은 소품은 제외한다. 기존 문/가구는 재사용한다.

Meshy 원본 4종: A01 문틀 벽, A02 창문 벽, A03 타일 코너, A04 외부 비상계단.
2026-10-12 CLI make --dry-run 견적: 이미지당 30, 합계 120크레딧.
기존 승인 상한 300 안에서 진행하며 재생성/추가 유료 단계는 자동 실행하지 않는다.
작업 전 확인 잔액 735. 실제 사용량은 완료 작업의 consumed_credits로 기록한다.

네 작업 모두 SUCCEEDED, 각 consumed_credits=30, 실제 합계 **120**.
작업 후 확인 잔액 **615**. 추가 유료 보정 작업은 없다.
원본 GLB는 `models/*/source.glb`, Blender 보정 파일은 `architecture-modules.blend`,
Unreal용 FBX·텍스처·manifest는 `Unreal/`에 있다. 실제 게임에 적용했으며
검토 이미지는 `docs/architecture-built-v1.html`에서 확인한다.

참조 이미지는 승인된 v8 부품 시트를 기반으로 내장 imagegen에서 개별 분리 제작했다.
정확한 문 개구부/계단 보행/벽 접합은 생성 결과를 그대로 신뢰하지 않고 로컬에서 보정한다.
벽·바닥 표면은 Meshy 원본에서 평평한 닫힌 메시로 베이크했다. 삼각형 수는 벽/바닥 12, 문틀 36, 창틀 60, 외부 계단 17,999다. Blender 원본에는 베이크 소스도 보존한다.
3층은 같은 구조에 깨끗한 마감 변형을 적용한다.

원본과 처리 결과는 보존하며, CLI 작업 기록과 서명 URL은 Git 제외된 meshy_output 안에 보관한다.
