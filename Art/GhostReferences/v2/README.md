# 지워진 얼굴 — 추격 귀신 v2

사용자 피드백: v1 얼굴이 평범하고 무섭지 않음. 흐릿하거나 기괴한 얼굴이 필요.

내장 image_gen으로 정면을 수정하고 좌우 측면을 다시 생성했다. 후면은 v1과 동일한 디자인을 유지한다. 얼굴에는 피부에 묻힌 눈구멍, 거의 평평한 코, 비대칭으로 찢어진 듯한 작은 입을 적용했다. 단순 사진 블러가 아닌 형태 변화다. 측면의 자세·주름은 정면과 정밀하게 일치하지 않으므로 모델링 참고로만 사용한다.

Meshy는 사용자 요청에 따라 제작 경로에서 제외했다. 유료 가입이나 외부 이미지 업로드 없이 로컬 Blender 모델로 진행한다.

프롬프트 변경: Preserve full-body A-pose, gray pajamas and proportions; replace ordinary face with skin-sealed asymmetric deep eye hollows, nearly flattened nose, tiny crooked off-center mouth slit, waxen smoothed facial planes, slightly elongated lower face, no blood, no normal eyeballs. Side views preserve the erased-face design.

현재 3D 파일은 `../../Ghost/haedam_ghost.blend`. 로컬 코드로 제작한 메시와 스켈레톤에 정면·후면 참조를 투영한 초안이며 AI 3D 복원 결과물이 아니다. 측면 텍스처 늘어짐과 관절 연결부, 손발 디테일은 후속 아트 작업 대상이다.
