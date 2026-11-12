# Tripo 입주민 반입 v1 — 2026-11-09

## 완료와 미완료
- 입주민 6명: 실제 생성, 리토폴로지, Mixamo 리깅, 대기 동작, FBX 변환, 2K 재질, Unreal SkeletalMesh/AnimSequence 반입 완료.
- 원본 GLB의 Icosphere 뷰어 보조 메시 제거. 몸 비율은 균등 스케일만 사용.
- 실제 3D 렌더: `Art/Characters/Residents-Tripo-v1/residents-board.png`, 각 `models/<id>/render.png`.
- C++ 방 배치 및 문틈 대화 연결 완료. MSVC /Zs 문법 검사 통과. 게임 빌드·패키징·실플레이는 수행하지 않음(이전 사용자 지시). 기존 실행파일은 이 변경 전 상태다.
- 새 인물의 이동·립싱크·새 음성은 아직 없다. 이번 적용은 대기 동작과 문 앞 대화다.
- 소품 변기·세면대·밥솥은 생성/경량화/FBX 준비까지만 완료. 목표와 실제 치수 차이가 있어 런타임 배치/기존 메시를 바꾸지 않았다. 배치 제안은 확정하지 않았다.

## 변경 파일
- `NightRulesPrototype/Source/NightRulesPrototype/NRResidents.cpp`: 6인 배치, 대기, 문틈·걸쇠, 대화 종료 시 문 닫기, 최종밤 대피 상태.
- `NRGame.h`, `NRGame.cpp`: 초기화/틱/대화 연결. 다른 기존 변경 보존.
- `NightRulesPrototype/Content/Data/day1.json`: 204·208·301호 선택적 인사 3개 추가. 새 단서/엔딩 게이트 없음.
- `NightRulesPrototype/Content/PrototypeAssets/ResidentsV1/`: 여섯 모델, 스켈레톤, 재질, 텍스처, 대기 동작, LOD.
- `tools/prepare_residents_tripo.py`, `tools/import_residents_tripo_unreal.py`: 재현용 반입 절차.
- `tools/prepare_tripo_batch_props.py`: 소품 후처리. 밥솥의 중복 면 2개는 추가 로컬 검증으로 제거.
- `Art/Characters/Residents-Tripo-v1/manifest.json`, `prepared.json`, `placement-audit.json`, `unreal-import.json`: 출처·치수·반입 실측.
- `Art/GeneratedProps/tripo-studio-batch-2026-11-09/ledger-final.json`: 최종 비용 825 / 잔액 2265. 이번 차수 주문은 종료했으며 별도 재생성 없음.

## 입주민 위치 (cm)
|인물|방|X|Y|Z(발 기준)|기준 키|
|---|---:|---:|---:|---:|---:|
|김민서|203|855.0|15.0|320.5|163|
|이태오|301|395.0|15.0|640.5|175|
|오정숙|105|1315.0|15.0|0.5|158|
|박준호|204|1093.0|15.0|320.5|176|
|윤지우|208|2005.0|15.0|320.5|162|
|아룬|104|1093.0|15.0|0.5|172|

키는 이번 게임 배치용 임시 스케일이며 공식 캐릭터 설정 확정이 아니다. 준호·아룬은 기본 X 위치에서 +8cm 보정. 최초 표본에서 각각 벽 겹침 2.04cm/0.23cm를 발견했고 수정 후 벽 여유 5.96cm/7.77cm.
최종밤 민서: 기존 3층 샤워실 (2375, -320, 640.5)로 이동. 대피 완료 시 숨김. 다른 입주민은 해당 층 대피 플래그에 따라 숨김.

## 소품 치수 (폭×깊이×높이, cm)
|소품|목표|균등 변환 후 실측|상태|
|---|---|---|---|
|변기|42×70×75|39.6×74.7×75.0|비율 왜곡 없이 원본/경량본 보존, 적용 보류|
|세면대|55×60×85|49.7×47.6×85.0|비율 왜곡 없이 원본/경량본 보존, 적용 보류|
|밥솥|38×32×32|41.9×44.5×32.0|비율 왜곡 없이 원본/경량본 보존, 적용 보류|

## 확인한 검증
- Unreal 반입 로그 `RESIDENTS_IMPORT_COMPLETE count=6`, Python 오류 없음.
- Unreal imported bounds 키 158~176cm, 각 기준값과 0.001cm 이내. idle 6초 또는 15.333초 확인.
- 모델별 원본 18,142~19,057 triangles → Unreal LOD 3단계 생성.
- Blender 대기 동작 4프레임 간격 표본의 AABB와 C++ 명목 가구 영역 비교. 수정 후 6명 모두 양의 벽/침대/옷장 여유. 실제 UE collision QA는 아님.
- `tools/output/residents-tripo-2026-11-09/NRResidents.cpp.syntax.log`, `NRGame.cpp.syntax.log` MSVC 문법 검사 성공. NRGame 기존 float 변환/Slate 경고 남음.
- Git 커밋 없음. 기존 가구 설계·옷장 불일치·제작 제안 상태를 임의 확정하지 않음.

## Claude 빌드/실플레이 인계
1. 새 `NRResidents.cpp`를 포함하여 Editor/Game 빌드 및 패키징. 자산은 이미 반입되어 반복 유료 생성 불필요.
2. 전화/첫 민원 일지 이후 104·105·203·204·208·301호를 방문. 문은 10도만 열리고 통과 불가, 얼굴은 어두운 문틈 안쪽.
3. 대화 교체·완료·거리 이탈·일시정지·사망·체크포인트 복원 시 문/걸쇠/대기 동작 상태 확인.
4. 민서 후반의 목소리 이상 이벤트에서는 이번 기본 주민 문틈 연결을 실행하지 않음. 기존 공포 이벤트 타이밍 확인.
5. 최종밤 샤워실 민서 구조/대피: 중복 인물 없음, 대피 플래그에 맞춰 숨김, 3개 엔딩 회귀 확인.
6. CCTV에서 인물의 크기/방향/그림자, LOD 변경, 발의 부유 및 문짝/침대 간섭을 실제 게임에서 확인.
7. 기존 실행파일을 새 반영 완료로 소개하지 말 것. 이 문서의 이미지는 Blender 렌더다.
