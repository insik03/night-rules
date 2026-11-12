# 추격 귀신 참조 v1

2026-10-09 / Codex 내장 image_gen 생성. 아직 게임 빌드에 포함하지 않은 디자인 초안.

- `01_front.png`: 정면. Meshy 단일 이미지 입력용 기준 이미지.
- `02_back.png`: 후면.
- `03_left.png`: 화면 왼쪽을 바라보는 측면.
- `04_right.png`: 화면 오른쪽을 바라보는 측면.

수척한 성인 남성, 짧은 검은 머리, 창백한 피부, 물때가 묻은 회색 잠옷, 맨발. 목표 신장 185cm. 정면과 후면은 A 포즈. 측면 이미지는 팔 각도와 주름이 완전히 일치하지 않으므로 정밀 설계도가 아닌 모델링 보조 참조로 사용한다. 얼굴과 체형의 기준은 정면이다.

## 생성 프롬프트 요약

Front: full-body orthographic adult male ghost, gaunt human anatomy, gray pallid skin, sunken eyes, short clumped black hair, worn ash-gray cotton button-front pajama shirt and straight loose trousers, subtle water stains, barefoot, symmetrical A-pose, plain pale gray background, even studio lighting, realistic PBR game character, no gore, no text.

Back / left / right: edit the front reference, preserve exact character, clothes and proportions, rotate to orthographic back / left-facing profile / right-facing profile, same background and lighting, full body, no text.

## 현재 상태

이미지 4장 완료. Meshy 웹 화면에서 Meshy 6 Lite 및 CC BY 4.0 설정을 확인했으나 파일 업로드가 브라우저 권한 거절로 차단되었다. 생성 버튼은 누르지 않았으며 이 작업으로 Meshy 생성 크레딧을 소비하지 않았다. 3D 메시, 리깅, 애니메이션 및 Unreal 적용은 미완료다.

모델 확보 후 Blender에서 신장·원점·방향·손가락 및 메시를 확인하고, 뼈대와 보행 애니메이션을 연결한 후 기존 추격 귀신을 교체해야 한다. 실제 모델 생성 서비스와 플랜, 라이선스 및 출처 표시 조건은 모델을 확보할 때 별도로 기록한다.
