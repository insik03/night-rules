# 치수 기반 Blender 가구 검토

- 추가 크레딧 0. Meshy/Tripo/API 호출 없음.
- 원본: haedam-dimensioned-furniture.blend. 각 층은 별도 Scene이며 MODEL 컬렉션을 실제 cm 치수로 제작하고 인스턴스로 배치.
- tools/build_dimensioned_furniture.py 재현 가능. tools/publish_dimensioned_furniture.py 검증·검토 페이지 생성.
- 전체 장면과 확대 모두 같은 모델. 평면 도면은 unified-v15/furniture-layout.json.
- 형태·치수 검토용. Unreal 반영, 게임 충돌 검증, 재질 제작은 하지 않음.
- 옷장 두 개를 침대 발치로 이전하고 통합 도면과 동기화. 의자와 벽 구조 유지.
- 기존 AI 생성 GLB와 rejected preparation은 이 모델에 사용하지 않음.
