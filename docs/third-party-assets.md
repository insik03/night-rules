# 외부 에셋 기록

2026-10-09: Poly Haven 공식 API에서 아래 6종의 2K Blender 원본 및 텍스처를 다운로드했다. 각 파일의 MD5를 공식 응답과 대조했다. 모두 CC0 1.0이며 Steam 상업용 게임에 사용할 수 있다. 원작자 정보와 다운로드 URL은 `Art/ThirdParty/PolyHaven/<asset>/source.json`에 보관한다.

공식 라이선스: https://polyhaven.com/license

| 원본 | 사용 위치 |
|---|---|
| https://polyhaven.com/a/metal_office_desk | 관리실 및 입주실 책상 |
| https://polyhaven.com/a/plastic_monobloc_chair_01 | 관리실·주방·휴게공간 의자 |
| https://polyhaven.com/a/steel_frame_shelves_03 | 관리실 및 주방 수납 선반 |
| https://polyhaven.com/a/vintage_microwave | 공용주방 전자레인지 |
| https://polyhaven.com/a/vintage_electric_kettle | 공용주방 전기주전자 |
| https://polyhaven.com/a/pot_enamel_01 | 공용주방 냄비 |
| https://polyhaven.com/a/television_02 | 관리실 CCTV·명단 CRT 모니터 |
| https://polyhaven.com/a/security_camera_01 | 복도 CCTV 카메라 본체 |
| https://polyhaven.com/a/korean_fire_extinguisher_01 | 복도 소화기 |
| https://polyhaven.com/a/wall_clock | 관리실 벽시계 |
| https://polyhaven.com/a/old_bed_frame | 입주실 철제 침대 |
| https://polyhaven.com/a/oak_veneer_01 (텍스처 1k) | 입주실 문·문틀·붙박이 책상·선반 |

2026-10-09 추가: 위 6종을 같은 방식으로 받았다. 새 모델은 Poly Haven 실측 크기를 유지한다. `tools/create_gosiwon.py`는 오크 무늬목 텍스처로 입주실 문·문틀·상부장 책상·벽선반·벽걸이 에어컨을 직접 모델링한다. 메시 형태는 자체 제작이고 텍스처만 CC0다. 문 메시 원점은 경첩 모서리에 있으며, 도어락·번호판은 복도 쪽(Blender -Y)에 있다. 투명도 맵(`_alpha_`=유리, `_opacity_`=마스크)은 임포터가 반투명·마스크 재질로 연결한다.

Blender에서 원본 UV를 유지하고 메시를 결합했다. 바닥 기준 원점과 게임 공간에 맞는 크기로 조정한 FBX 및 PNG 재질 맵을 Prepared 폴더에 생성한다. 언리얼 재질은 Base Color·Roughness·Metallic·Normal을 연결하고 OpenGL 노멀의 녹색 채널을 반전한다. 원본은 별도 폴더에 보존한다.

재생성 순서:

1. `python tools/fetch_cc0_assets.py`
2. Blender에서 `tools/prepare_cc0_assets.py`와 `tools/create_gosiwon.py` 실행.
3. `tools/build.ps1 -EngineRoot <엔진 경로> -ImportCC0 -Package`로 언리얼 가져오기와 Windows 빌드를 실행한다. 빌드 도구는 한글 경로용 ASCII 별칭과 스크립트 완료 마커를 검증한다.

이 에셋은 생성형 AI로 만든 에셋으로 기록하지 않는다. 기존 자체 제작 소품 및 AI 이미지에 대한 기록은 `docs/ai-assets.md`에 유지한다. 냉장고·싱크대·조리대 등은 아직 자체 제작 임시 모델이다.

검증: Windows 패키징 성공, 게임 실행 화면에서 주방 재질 확인, NRSmokeTest 20개 통과, 실제 키 입력 기반 NRMapTest 12개 이동 구간 통과. 프리뷰는 `Art/Previews/kitchen_cc0.png`, 모델 검토 렌더는 `Art/Previews/cc0-assets.png`에 저장했다.

2026-10-10 추가: `tools/create_gosiwon.py`에서 분전함·봉인 점검구·점검 장부(바인더)·예비 퓨즈·307호 열쇠표를 자체 모델링했다. 색상 상수 재질만 쓰며 외부 메시나 텍스처는 쓰지 않는다. 손바닥 크기의 소품이라 박스 충돌을 명시적으로 만들어 상호작용 판정에 쓴다. `import_cc0_unreal.py`는 `import.json`과 `door_import.json`에 있는 메시만 가져온다. `NR_IMPORT_ONLY`로 일부만 가져올 수 있다.
# Footstep / chair impact foley (2026-10-18)

- Source: [Kenney Impact Sounds](https://kenney.nl/assets/impact-sounds), CC0.
- Archive and original license: `Art/Footsteps/Source/kenney_impact-sounds.zip`, `Art/Footsteps/Source/License.txt`.
- Concrete/wood footsteps and soft/wood impacts processed locally with EQ, pitch and layered heel/body sound. No paid generation.
- Reproducible processing: `tools/design_footsteps.py`; output hashes: `Art/Footsteps/manifest.json`.
- Used in the game and showcase soundtrack. Existing voice recordings are unchanged.


## 2026-11-09 Tripo Studio 입주민 6명 및 소품 3개
- 서비스: Tripo Studio 웹 계정. API/CLI 잔액 사용 없음. 생성/후처리 합계 825 credits, UI 최종 잔액 2265.
- 입주민: `Art/Characters/Residents-Tripo-v1/manifest.json` 및 `input-prompts.json`, 실제 원본 `models/*/source-animated.glb`.
- 반입: `/Game/PrototypeAssets/ResidentsV1/`의 6인 SkeletalMesh / Mixamo rigs / Studio preset idle 또는 wait / 2K PBR.
- 소품: `Art/GeneratedProps/tripo-studio-batch-2026-11-09/ledger-final.json`. 변기·세면대·밥솥 원본/경량본 저장, 목표 치수 차이로 런타임 배치 보류.
- 입력 이미지: 기존 승인 캐릭터 시트 기반 생성 이미지. 생성물/프리셋의 서비스 이용권 증빙은 계정 기록과 함께 출시 전 최종 정리 대상이며, 이 기록은 별도 라이선스 취득을 주장하지 않음.
- 현재 실행파일은 미갱신. 상세 적용/검증 구분: `docs/residents-tripo-v1.md`.
