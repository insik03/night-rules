# 추격 귀신 Blender 프로토타입

- 원본: haedam_ghost.blend (참조 텍스처 포함)
- Unreal 입력: SK_ErasedGhost.fbx
- 방식: 로컬 절차적 모델링, 수동 정의 스킨 웨이트, 16개 뼈, 약 1만 삼각형.
- 얼굴: 지워진 눈·코·입 디자인. 이미지 생성 참조를 알베도로 사용.
- 동작: 30fps, 40프레임 보행 루프. 최종 추격 애니메이션이 아닌 동작 확인용.
- Meshy 및 유료 외부 생성 서비스 사용 없음.

재생성: Blender --background --factory-startup --python tools/create_ghost.py

Unreal 가져오기: tools/build.ps1 -EngineRoot <UE_5.8 경로> -ImportGhost

현재 재질은 사진 참조의 조명까지 포함한 투영 방식으로, 최종 PBR 텍스처가 아니다. 어깨·목 연결과 손발, 측면 UV는 추가 수정이 필요하다. 정면 참조와 완전히 동일한 고품질 캐릭터를 자동 생성한 것으로 취급하지 않는다.
