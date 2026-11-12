# 문 파손 표시와 벽지 복구

2026-10-12. 기존 문 디자인과 벽지 이미지를 유지하며 제작·적용 오류 수정. 신규 AI 생성 및 크레딧 사용 없음.

## 문

Meshy GLB의 분리된 꼭짓점을 연결하지 않고 면 수를 줄이면서 UV 경계의 면들이 독립적으로 단순화되었다. 기존 게임용 문은 8,387개 꼭짓점, 9,000면, 열린 경계 6,938개였다. 이미 줄인 모델을 나중에 연결해도 열린 경계 4,278개가 남았다.

원본 GLB에서 먼저 가까운 꼭짓점을 연결하고 면 방향을 정리했다. 문은 원본 37,346면을 유지했다. Blender 결과는 18,675개 꼭짓점, 열린 경계 0개. 원본 텍스처와 손잡이, 경첩 기준점 및 78×200cm 문짝 크기를 유지했다. 문 FBX와 Unreal SM_CP_Door를 갱신했다. 후속 재생성에도 같은 처리가 적용된다.

면을 복구한 후에도 남던 큰 삼각형 무늬는 텍스처 스트리밍에 따른 저해상도 표시 문제였다. Blender 원본·FBX·Unreal 재출력의 UV 좌표가 같은 것을 확인했고, 문 텍스처의 Never Stream 설정을 켜자 실제 게임 화면에서 나뭇결과 손잡이가 정상으로 돌아왔다. 이 설정은 재임포트 시에도 적용한다. 변형 전 표면 방향이 남지 않도록 Unreal에서 노멀·탄젠트를 다시 계산한다.

문 인스턴스들은 같은 메시와 텍스처를 공유한다. 다만 기존보다 면 수가 늘고 문 텍스처가 메모리에 상주하므로, 저사양 노트북의 최종 성능 검증과 최적화는 별도로 필요하다.

## 벽지

실제 맵의 ArchitecturePanel이 M_Wallpaper 대신 M_AM_PlasterV2 색상 마감으로 덮어쓰고 있었다. 기존 T_Wallpaper를 세계 좌표 기준 100cm 크기로 투영하는 M_AM_WallpaperV3와 M_AM_CleanWallpaperV3를 연결했다. 1·2층은 낡은 베이지색, 리모델링한 3층은 밝은 톤. 주방·화장실 타일벽은 벽지가 아닌 기존 타일 재질을 사용한다. 관리실과 공용주방 사이의 공유벽은 벽지로 유지하여 관리실 안쪽에 타일이 들어오지 않게 했다.

## 확인

Windows 실행파일 빌드 성공. `tools/output/build-door-wallpaper-v7-resident.log`에 BUILD SUCCESSFUL 확인.

`Art/Previews/Architecture-v7/`의 8개 화면을 최종 패키지에서 재촬영했다. 관리실 정면·내부, 문 앞면·뒷면·열린 출입구, 벽지 근접, 1층·3층 복도에서 문 표면과 벽지 적용을 확인했다. 합성·이미지 생성으로 대체하지 않았다.

최종 실행파일 검사 4개 모두 failures=0 (`tools/output/architecture-v7-final-tests.log`):

- NRArchitectureTest: 벽 충돌과 출입구 통과.
- NRMapTest: 실제 이동 입력으로 관리실→복도→계단→202호 경로.
- NRChoice202Test: UV 판단 후 202호에 들어가지 않고 DAY 1 완료.
- NRInvestigationTest: 조사 단서·규칙·CCTV 진행.

실행파일: `Builds/Windows/NightRulesPrototype.exe`. 갤러리: `docs/door-wallpaper-v7.html`.
