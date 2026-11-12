# 야간수칙 AI 스킬 설정
2026-11-01. 프로젝트 범위 설치: 언리얼 31개, 블렌더 30개.

## 출처 / 적용
- [quodsoler/unreal-engine-skills](https://github.com/quodsoler/unreal-engine-skills): UE 5.8 개발 지침.
- [RobLe3/cc-blender-skill](https://github.com/RobLe3/cc-blender-skill): 모델링, 참고 비교, UV, 내보내기 지침.
- 정확한 commit, 설치 파일 해시, MIT 라이선스는 `.agents/skills-lock.json`, `.agents/licenses/`에 보관한다.
- root `AGENTS.md`가 작업별 스킬을 연결한다. UE는 `.agents/ue-project-context.md`, Blender는 `.agents/blender-project-context.md`를 먼저 읽는다.
- 전체 스킬은 서로 참조하는 자료를 보존하기 위해 설치했지만 작업별 필요한 것만 로드한다. 네트워킹/GAS 등은 설치됐다는 이유로 게임에 도입하지 않는다.
- Blender 실행은 기존 로컬 CLI 방식. `text-to-blender/SKILL.md` 라우팅만 로컬 실행에 맞춰 수정했다. 외부 업데이트 후 이 어댑터와 설정을 유지한다.
- Epic 공식 Unreal MCP 및 Blender MCP 서버는 이번 설치 대상에 포함하지 않았다. 게임 엔진 플러그인/런타임 에셋은 변경하지 않는다.

## 사용 예
- “귀신의 실제 이동속도와 달리기 모션이 맞는지 검사해줘.”
- “통합 도면 치수로 옷장을 모델링하고 열린 문과 침대 간섭을 보여줘.”
- “UV 흔적이 일반광에서 숨겨지는지 확인하고 게임에서 캡처해줘.”
- “세 엔딩 조건과 재시작/저장 상태의 누락을 검사해줘.”

## 검증
설치 파일, frontmatter, 로컬 경로와 커밋 고정 여부를 검사한다.
`tools/verify_blender_skill_backend.py`는 42×44×80cm 테스트 메시를 별도 프로세스에서 만들고 FBX export/import 후 치수를 검증한다. 결과는 `tools/output/skill-backend-check/result.json`이며 이 검사만으로 Unreal 반입이나 모든 Blender 기능의 호환성을 보장하지 않는다.

## 알려진 제작 문제
옷장 두 개의 발치 배치는 유지하지만 현재 도면의 문 90도 개방 간섭은 미해결이다. 35cm 축소 제안을 승인된 규격으로 적용하지 않는다. 기존 치수 검토본의 정확도가 모든 기존 게임 에셋에 적용된 것은 아니다.

현재 프로젝트를 연 다음 턴부터 스킬 검색 대상이 된다. 프로젝트가 예전 경로로 열려 있으면 `바탕 화면/AI작업/Game_pm` 폴더로 다시 연다.

## 이번 설치 검증 결과
- 61개 스킬 메타데이터와 221개 설치 파일 해시 확인 통과.
- Blender 5.2.2 LTS에서 테스트 메시 42×44×80cm의 FBX 내보내기/재반입 치수 오차 0.1cm 이내 통과.
- 결과: `.agents/skills-verification.json`. 게임 에셋 변경 및 Unreal 임포트/빌드는 이번 작업에서 수행하지 않음.
- 외부 유료 생성 및 크레딧 사용 없음. 기존 Git 변경은 그대로 보존함.
