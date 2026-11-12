# Blender Project Context — 해담고시원
확인일: 2026-11-01

## 실행 방식
- Blender 5.2.2 LTS: `C:/Program Files/Blender Foundation/Blender 5.2/blender.exe`.
- 기본 백엔드는 이 실행파일의 background Python이다. 이번 설치로 MCP 연결을 추가하거나 사용자의 열린 Blender 장면을 제어하지 않는다.
- `text-to-blender`에는 프로젝트용 CLI 어댑터를 추가했다. 다른 스킬의 MCP 호출 예제는 bpy 코드를 작성해 파일로 저장한 뒤 아래 방식으로 실행한다. 도구가 없는데 성공했다고 흉내내지 않는다.
```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --factory-startup --python-exit-code 1 --python '<작업 스크립트 절대 경로>'
```
- 기존 .blend 작업은 별도 프로세스에서 복사본/새 출력 파일로 저장한다. 위 factory-startup은 새 프로세스의 초기 장면에만 적용한다. 기존 파일을 연 뒤 월드·재질을 무조건 초기화하지 않는다.
- `tools/build_dimensioned_furniture.py`는 기존 로컬 치수 모델 생성기다. 실행 전 출력 경로를 확인한다. 그 스크립트의 실행은 Unreal 반입과 별개다.
- CLI에서 viewport 도구 대신 카메라 렌더와 JSON 실측 보고서를 파일로 내보낸다. 숫자와 이미지 모두 확인한 뒤 결과를 보고한다.

## 치수 / 작업 계약
- 루트 AGENTS.md의 도면/치수/공간 기준을 따른다. 외부 스킬의 평균 가구 치수는 확정 프로젝트 치수보다 우선하지 않는다.
- Blender 좌표는 이 프로젝트 생성기에서 m 단위(입력 cm를 100으로 나눔)로 작성한다. scene unit scale을 확인하고 실제 평가 메시의 경계를 cm로 보고한다.
- 대상별 width/depth/height, 로컬 축, 피벗, 적용 회전, 목표 크기, 허용오차를 먼저 명시한다. 진단용 단순 가구 외형의 임시 허용오차는 0.1cm이며 실제 게임의 모든 소품에 동일한 정밀도를 보장한다는 뜻이 아니다.
- 손잡이/경첩/두께/다리 비율을 유지하며 치수에 맞게 제작한다. 비균등 스케일로 만든 왜곡을 Apply Scale로 숨기지 않는다.
- 분리 부품: 책상 서랍, 옷장문, 냉장고문, 출입문. 피벗·개방각·충돌 여유를 기록한다.
- 신설 에셋은 기존 프로젝트 SM_/SK_/M_/T_ 명명과 임포트 스크립트를 따른다. Blender 외부 스킬의 GEO- 명명 때문에 기존 에셋을 일괄 바꾸지 않는다.
- 정면/측면/배치 렌더와 치수 결과를 확인한다. 기존 장면에서 재질/조명을 수정하지 않는 작업에는 렌더 스타일 초기화를 적용하지 않는다.
- 임포트 전 텍스처 경로·UV·노멀·삼각형 수·피벗·충돌 메시·실측 단위를 확인한다. 실제 UE 반입 후 100배 크기 오류, 부유, 겹침, 개폐, 통행을 별도 확인한다.

## 적용 범위
- 이미지 분석/윤곽 추출 스킬 중 OpenCV/SciPy를 요구하는 기능은 필요할 때 해당 Python 환경의 의존성을 확인한다. 기본 모델링/FBX 점검은 Blender 내장 bpy/mathutils로 실행한다.
- Meshy/Tripo/외부 모델 생성은 기본적으로 실행하지 않는다. 이번 설치의 크레딧 사용량은 0이다.
- 원본 스킬의 Blender 5.1.1 검증 주장은 작성자의 결과다. 이 프로젝트의 5.2.2 호환성은 실행한 기능만 검증 완료로 표시한다.

## 최신 가구 검토 (2026-11-01)
- 기준 .blend: `Art/EnvironmentConcepts/furniture-review-v2/haedam-furniture-reviewed.blend`. 기존 v1 원본 보존.
- 재현: `tools/review_furniture_v2.py`, 페이지: `tools/publish_furniture_v2.py`. 프레임1 닫힘 / 91 열림.
- 옷장 45×45×175cm 두 개 유지, 각21.5cm 양문. 91개 상태 실측과 회전반경 계산으로 침대 여유 최소18.97cm 확인.
- 발치 틈은 통로가 아니며 옆에서 접근한다. 실제 Unreal 반입·게임 충돌은 아직 수행하지 않았다.
