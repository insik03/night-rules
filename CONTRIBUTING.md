# 팀 협업 규칙

## 작업 순서
1. 작업 내용을 Issue에 적고 담당 파일을 정합니다.
2. 에디터를 닫고 최신 `main`을 받습니다.
3. `feature/<작업>`, `fix/<작업>`, `art/<작업>`, `docs/<작업>` 브랜치를 만듭니다.
4. 같은 맵·블루프린트·Blender 파일을 동시에 수정하지 않습니다. 바이너리 파일은 먼저 LFS 잠금을 획득합니다.
5. 관련 파일만 커밋한 후 브랜치를 올리고 Pull Request를 엽니다.
6. 다른 팀원의 검토 1명과 `repository-checks` 통과 후 합칩니다.
7. 합친 뒤 잠금을 해제합니다. 실행에 영향을 주는 변경은 별도로 Unreal 빌드·플레이 확인 결과를 PR에 적습니다.

```powershell
git switch main
git pull --ff-only
git switch -c art/room-wardrobe
git lfs lock "Art/path/to/wardrobe.blend"
# 수정 후 관련 파일만 add
git add "Art/path/to/wardrobe.blend"
git commit -m "art: adjust wardrobe door clearance"
git push -u origin art/room-wardrobe
# PR 병합 후
git lfs unlock "Art/path/to/wardrobe.blend"
```

## 보호하는 기준
- `main`에 직접 푸시·강제 푸시·브랜치 삭제를 하지 않습니다.
- 문법/데이터 CI 통과를 엔진 빌드나 플레이테스트 통과로 표현하지 않습니다.
- cm 단위, 설계와 런타임 차이 보고, 개폐 부품 분리, UV 관찰 원칙은 [AGENTS.md](AGENTS.md)를 따릅니다.
- 새로운 설계·스토리 확정은 PR에서 팀과 합의합니다. 임의 비균등 스케일로 가구 치수 문제를 숨기지 않습니다.
- AI 에셋 생성은 검토한 이미지와 예산 범위 안에서 진행하고 출처·비용을 기록합니다.
- 에셋 이름 변경/이동은 Unreal 에디터에서 하고 Redirector 수정 및 참조 검사를 수행합니다. 파일 탐색기에서 `.uasset`만 이동하지 않습니다.
- 다른 사람의 작업이나 자동 생성된 전체 폴더를 확인 없이 일괄 커밋하지 않습니다.
- API 키·쿠키·토큰·서명 다운로드 URL·학번·연락처·개인 제출 서류를 커밋하지 않습니다.

## 코드와 에셋
C++/JSON 변경은 텍스트 병합이 가능하지만, `.uasset`, `.umap`, `.blend`, `.fbx`, `.glb`는 잠금 후 한 명씩 편집합니다. Git LFS 잠금은 작업 브랜치와 별개로 저장소 파일 경로에 적용됩니다.

```powershell
git lfs locks
```

에셋 작성자는 원본과 반입 결과를 같은 PR에 포함하고, 수정 전후 이미지·cm 실측·개폐 여유를 함께 적습니다. 모델링 원본을 받는 방법은 [설치 안내](docs/team-setup.md)를 참고하세요.
