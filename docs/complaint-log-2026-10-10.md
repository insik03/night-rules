# 민원 장부 직접 기입

책상 왼쪽 뒤의 `complaint_log`를 E로 열고 숫자키 1~3으로 호수, 내용을 고른다. 첫 통화 줄은 0.05초/자 기입을 끝내야 관리실 문이 열린다. 이후 민원은 빈 줄을 남기며 선택 기입한다. Esc로 기입 중 닫으면 해당 줄의 잉크를 취소하고 다시 선택할 수 있다.

접수 시각은 대화를 시작할 때 보존한다. 첫 통화를 02:13으로 놓고 게임의 Elapsed 60초마다 1분이 지난다. 접수 대상은 first_call, second_call, manager_call, minseo, resident_104, resident_105_early, resident_105, resident_203, resident_203_safe다. 재열람으로 같은 민원 줄을 중복 생성하지 않는다.

202호 관리실 각성 또는 미입실 보고가 이상 줄을 준비한다. 이후 실물 장부를 다시 열 때 마지막 완성 줄 바로 아래에 02:37의 문장이 이미 적혀 있다. 같은 폰트와 잉크색을 사용하며 펜 소리만 0.3초 난다. 노출 즉시 체크포인트에 보존하므로 복원 후 다시 추가하지 않는다. `/Game/Audio/pen_scratch.pen_scratch`가 없으면 무음이다.

PC의 야간·미입실·재실 보고는 `{{complaints}}` 자리에 완성된 플레이어 줄을 넣는다. 빈 줄과 이상 줄은 보고에서 제외한다. 보고 시점의 본문을 별도로 보존해 J 기록에서도 같은 보고를 읽는다. 장부 줄, 접수 중인 대화, 보고 본문, 이상 줄 준비·노출·분기는 모두 체크포인트 복사에 포함한다.

선택지는 day1.json의 `complaint_rooms_<source>`, `complaint_contents_<source>`에 있다. voices.json은 수정하지 않았다. 동적 보고와 전임 총무 장부는 오래된 voices.json 자막을 읽지 않도록 처리했다. 사용자가 tools/create_day1_voices.py 실행 및 언리얼 임포트를 수행한다.

새 Evidence는 `complaint_log`, `complaint_blank_<source>`, `complaint_choice_<source>_room_<1~3>`, `complaint_choice_<source>_content_<1~3>`, `complaint_written_<source>`, `complaint_anomaly`다. actions.jsonl에는 complaint_blank, complaint_choice, complaint_written, complaint_anomaly 이벤트가 남는다. 정답이나 진위 판정은 없다.

검증 대상:

- `-NRComplaintLogTest`: 책상 접지·겹침·서 있는 눈높이 조준, 대화 종료 후 빈 줄, 시각 보존, 목표와 첫 기입 필수, 두 단계 선택과 0.05초/자 잉크, 선택 Evidence, 선택 취소, 중복 접수 방지, 선택 줄·빈 줄 복원, PC 보고 반영, 이상 줄 시점·두 분기·1회·복원, 이상 줄 보고 제외, J 열람, 전임 장부 대비.
- `-NRDemoWalkTest`: demo-walk.json에 전화 종료 후 책상 앞 이동, E, 숫자 1, 숫자 1, 기입 완료 대기, Esc를 추가했다. 이동은 의자 뒤를 돌아 장부 앞에 선다.
- `-NRSmokeTest`: 첫 통화 종료 후 문이 닫혀 있고, 첫 줄 기입 완료 후 열린다는 기대값으로 수정했다.
- `-NRPolishTest`: 선택지 문서와 동적 보고 때문에 전체 자막 행 수를 고정하지 않고, 기존 32개 대사와 원문 일치를 검사한다.

MSVC `/Zs /Y- /std:c++20`로 수정한 C++ 7개 파일을 검사했다. 빌드, UHT, 패키지 플레이 테스트, 음성 재생성, 에셋 임포트는 실행하지 않았다. 실제 패키지에서 배치·조준·숫자키·펜 소리 확인이 남아 있다.
