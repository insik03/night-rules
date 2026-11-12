# AI 생성 에셋 기록

- **2026-10-12 귀신 교체:** 사용자가 승인한 웃는 얼굴·검은 눈구멍·화상 피부 시안을 내장 image_gen으로 A 포즈화하고 Meshy CLI 0.4.0에서 이미지→3D와 자동 리깅을 수행했다. 이번 사용량 35크레딧. `Art/GhostMeshy/Approved`에 원본·입력·후처리 파일과 작업 ID를 보관한다. Blender에서 714,682→89,999면으로 줄이고 기괴한 달리기와 걷기를 수정해 `/Game/PrototypeAssets/GhostMeshy`로 연결한다. 사전 생성 AI 메시·텍스처가 포함된다. 학생 할인 유료 계정 사용은 사용자 확인 사항이며 계정별 상업 이용 조건의 증빙은 출시 전 보관한다. 아래의 ‘Meshy 제외/외부 3D 생성물 미포함’ 문구는 과거 버전 기록이다.

- 데모 확장: `Art/DemoAudio/*.wav` 12종은 로컬 Python으로 직접 합성한 원본 파형이다. 외부 녹음·AI 음성 서비스·인물 음성 모방 없음. 생성 코드 작성에는 AI 개발 보조 사용. 현재 기본 환경음과 사건 효과음에 사용하며 `chase_pulse`는 예비 파일이다. 수치와 루프 정보는 manifest.json 참조.

- 2026-10-09 귀신 v2: `Art/GhostReferences/v2`의 정면·좌우 이미지를 내장 image_gen으로 생성/수정. 후면은 v1 유지. `Art/Ghost/haedam_ghost.blend`와 FBX는 로컬 Blender 스크립트로 모델링·리깅했으며 참조 정면/후면을 재질로 사용한다. Unreal `/Game/PrototypeAssets/Ghost`에 적용하는 사전 생성 AI 이미지 포함 에셋이다. Meshy는 업로드 차단 및 사용자 무료 플랜 피드백 후 제작 경로에서 제외했다. 외부 3D 생성·유료 결제 없음.

- 2026-10-09: `Art/GhostReferences/01_front.png` ~ `04_right.png`는 Codex 내장 image_gen으로 생성한 추격 귀신 4방향 참조다. 게임 빌드에는 미포함. 디자인과 제작 상태는 해당 폴더 README.md에 기록했다. Meshy 업로드는 브라우저 권한 거절로 차단되었으며 아직 외부 3D 모델은 생성하지 않았다.

Steam Content Survey (사전 생성 AI 콘텐츠 공개) 대응용. PRD §24.7.

**사용하는 시점에 바로 기록한다. 출시 직전에 소급 정리하지 않는다.**

| 파일 경로 | 도구/버전 | 생성 | 후처리 | 상업 라이선스 확인 | 최종 빌드 포함 |
|---|---|---|---|---|---|
| | | | | | |

## 현재 프로토타입의 제작 기록

- `Art/Generated/haedam_props.blend`와 FBX 6종: Blender 5.2.2에서 로컬 절차적 모델링 스크립트로 생성. 스크립트 작성에 AI 개발 보조 사용.
- WAV 3종: Python 파형 합성 스크립트로 생성. 녹음·상용 음원·외부 AI 음성 서비스 사용 없음.
- 이미지 프리뷰: Blender 및 실제 Unreal 게임 렌더 결과. 외부 이미지 생성 서비스 사용 없음.
- Meshy 등 외부 AI 생성물과 Fab 구매 에셋은 아직 포함하지 않았다. 실제 출시 빌드의 AI 공개 범위는 포함 콘텐츠와 Steam Content Survey 기준에 맞춰 검토한다.

## 2026-10-09 재질 및 환경 모델

| 파일 | 제작 도구 | 용도 | 출시 전 확인 |
|---|---|---|---|
| Art/Textures/T_Wallpaper.png | Codex 내장 image_gen | 낡은 크림색 벽지 알베도 | 이용약관 및 Steam AI 공개 검토 |
| Art/Textures/T_Linoleum.png | Codex 내장 image_gen | 회녹색 장판 알베도 | 이용약관 및 Steam AI 공개 검토 |
| Art/Generated/haedam_environment.blend | Blender 5.2.2, 로컬 모델링 스크립트 | CRT 모니터, 형광등 및 기존 소품 | 직접 제작 메시 |

이미지 원본은 수정하지 않고 Unreal 월드 좌표 재질로 투영한다. 색상 텍스처이며 완성된 PBR 세트는 아니다. 이전의 ‘외부 이미지 생성 서비스 사용 없음’ 기록은 초기 버전에 해당한다.

벽지 프롬프트: square seamless tiling base color, old cream-beige vinyl wallpaper, tiny embossed woven grain, subtle yellowing and scuffs, flat orthographic scan, uniform diffuse light, no text or objects.
장판 프롬프트: square seamless tiling base color, worn grey-green vinyl linoleum, fine mineral flecks and wax wear, flat orthographic scan, no grout, text, objects or shadows.

- 2026-10-09: `Art/Generated/haedam_entrance.blend` 및 `SM_EntranceDoor.fbx`는 Blender 로컬 스크립트로 모델링한 현관문이다. 추가 이미지 생성 없이 Unreal 절차적 재질을 사용했다.

- 연결 맵 v0.2: haedam_furnishings.blend 및 haedam_sanitary.blend는 Blender 5.2.2 로컬 메시 스크립트로 제작했다. 냉장고·전자레인지·조리대·식탁·침대·수납장·세면대·변기를 포함한다. 새로운 이미지 생성물이나 외부 구매 에셋은 추가하지 않았다.

- 2026-10-09: Art/MeshyReferences의 냉장고·싱크대·신발장·환풍기 이미지 4장을 Codex 내장 image_gen으로 생성했다. Meshy Image to 3D 입력용이며 현재 게임 빌드에는 미포함이다. 프롬프트와 목표 크기는 같은 폴더의 prompts.json 및 README.md에 기록했다. Meshy 결과물을 가져올 때 생성 모델·플랜·라이선스·표시 의무를 별도로 기록한다.
