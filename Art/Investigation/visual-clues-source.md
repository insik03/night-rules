# 시각 단서 원본

2026-10-12. `T_ClueHandprint.png`는 내장 image_gen으로 생성한 투명 손자국 텍스처다. Meshy 생성이나 크레딧 사용은 없다. 원본은 수정하지 않고 복사했다. 최초 일반광 버전에서 후속 사용자 요청으로 UV 전용으로 변경했으며 Unreal 재질은 알파만 사용하여 UV 조사 시에만 형광 잔류물로 표시한다. 상처·혈흔·실제 손 모델이 아니다. 상용 빌드 AI 사용 기록에 포함할 대상이다.

생성 프롬프트:

> Create a single production game decal texture, isolated on genuinely transparent background. One realistic adult human handprint left on an old surface by dusty grey-brown grime, fingers upwards, palm down. It is a TRANSFER PRINT ONLY, no actual hand or flesh, no surface/background. Anatomically correct FIVE digits, four long fingers and one angled thumb. Broken uneven pigment, recognizable palm pads, subtle skin crease negative spaces, mildly smeared downwards by 2 cm with a small wrist rub. Readable strong central silhouette with fine irregular edges. Neutral grey-brown dust, not blood, no glow, no UV purple, no symbols, no words, no lettering, no frame, no shadows or background. Front-on orthographic flat texture. Whole handprint centered with generous empty transparent margin, square composition. Real-world scale about 18x25cm. For a grounded realistic Korean horror game clue on a metal access panel. Save output as a local PNG if supported.

UV 표식 `T_UVDoor.png`, `T_UVFragment.png`는 기존 편집 가능한 생성 코드 `tools/create_uv_marks.py`의 선형 표식이다. 이전 한글 경고/화살표를 제거하고 가운데가 끊긴 세 줄만 사용한다. 생성형 이미지가 아니며 두 표식의 대조 가능성은 실제 게임 화면에서 확인한다.

문틀의 휘어진 금속판·잠금 홈·나사 주변 긁힘은 Unreal 기본 메시를 조합한 런타임 디테일이며 별도 외부 모델을 사용하지 않는다. 최종 고품질 문 모델을 대체했다고 간주하지 않는다.
