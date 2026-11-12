"""Offline A1-A16 and 2026-10-14 decision contracts. Engine tests run separately."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'NightRulesPrototype/Content/Data'
SRC = ROOT / 'NightRulesPrototype/Source/NightRulesPrototype'
day = json.loads((DATA / 'day1.json').read_text(encoding='utf-8'))['documents']
end = json.loads((DATA / 'endings.json').read_text(encoding='utf-8'))['documents']
game = (SRC / 'NRGame.cpp').read_text(encoding='utf-8')
demo = (SRC / 'NRDemo.cpp').read_text(encoding='utf-8')
log = (SRC / 'NRComplaintLog.cpp').read_text(encoding='utf-8')
final = (SRC / 'NREndings.cpp').read_text(encoding='utf-8')
experience = (SRC / 'NRExperience.cpp').read_text(encoding='utf-8')

assert 'NRMechanics::SecondCallAllowed' in game
for key in ('resident_203', 'resident_203_safe'):
    assert '전 방에서 나오지 않았어요' not in day[key]
assert '사칭' not in day['second_call']

# A2: west wall mounting clears door opening, window and corridor approach.
assert 'FVector(-486,-35,452)' in demo
assert 'Face(P,FVector2D(1,0))' in demo
panel_y = (-35-24, -35+24)
door_y = (-135-43.5, -135+43.5)
assert panel_y[0] > door_y[1]
assert -486+3 < -190  # westmost window edge is -190
for key in ('rules', 'manager_call', 'sealed_panel', 'log_plan_choices'):
    assert '서쪽(왼쪽) 비상문' in day[key]
steps = json.loads((DATA / 'demo-walk.json').read_text(encoding='utf-8'))['steps']
panel_i = next(i for i, s in enumerate(steps) if s.get('id') == 'sealed_panel')
assert steps[panel_i-1]['at'] == [-350, -50, 410]

assert '태오' not in end['final_exit_open'] and '복도 쪽에서 태오' in end['final_exit_taeo']
assert '(Finale.CheckedFloors & 4)' in final  # A3
assert '307' not in end['final_minseo_rescued']  # A4
for key in ('final_line_on', 'final_unsealed'):
    assert '취소' not in end[key]  # A5: submission is required for the appended line
assert final.count('const bool Submitted=Finale.ReportSubmitted;') == 2
assert 'Submitted && Finale.LineEnabled' in final and 'Submitted && !Finale.Sealed' in final
assert '수화기 · 다른 목소리' in game and '나 · 목소리' in final  # A6
assert 'FSubtitleLine{Part,Hold,Speaker}' in game and 'TEXT("나 · 독백")' in game

assert 'FirstComplaintWritten() && Evidence.Contains(TEXT("manager_call"))' in log  # A7
manager_i = next(i for i, s in enumerate(steps) if s.get('evidence') == 'manager_call')
assert next(i for i, s in enumerate(steps) if s['kind'] == 'investigation_plan') > manager_i
residents = {101,102,104,105,107,203,204,206,208,211,301,303,305,308,311}
roster_rows = dict(re.findall(r'^(\d{3})호\s+(.+)$', day['roster'], re.M))
assert {int(n) for n, v in roster_rows.items() if '공실' not in v} == residents  # A8
assert all('공실' in roster_rows[n] for n in ('202', '307'))
for name in ('아룬', '오정숙', '김민서', '박준호', '윤지우', '이태오'):
    assert name in day['roster']

assert '오늘' not in day['service_ledger'] and '{{time}}' in day['service_ledger_new']  # A9
assert 'ComplaintLog.LedgerLine.IsEmpty()' in log and '*Row.Time' in log
assert 'ComplaintCheckpoint=ComplaintLog' in game and 'ComplaintLog=ComplaintCheckpoint' in game
assert 'Row.Time=ComplaintClock()' in log and '{{time}}' in day['complaint_anomaly_avoided']  # A10
assert 'CCTVFrameTimes[HistoryHead]=Elapsed' in experience and 'CCTVClock' not in experience
assert 'CCTVStoppedAt=Elapsed' in demo and '3*3600+14*60' not in game
assert '03:14' in day['rules'] and '03:14 수칙에 적힌 것처럼 1분' in day['manager_call']
assert '문을 열지 않고 202호 앞을 떠났다' in day['202_avoided']  # A11
assert '관리실 옆 창고' in day['breaker_fixed'] and '관리실 뒤 창고' not in day['breaker_fixed']  # A12
assert 'CAM 04 · 2층 복도' in day['cctv_recovered'] and 'CAM 01 · 관리실.' in day['cctv_recovered']  # A13
assert '관리실 옆문' not in day['cctv_recovered']
assert all('근무일지' not in text for text in day.values())  # A14
assert '야간 업무일지' not in (ROOT / 'tools/create_story_props.py').read_text(encoding='utf-8')
assert 'InvestigationPlanName' not in final
assert 'NRMechanics::NeedsEuro' in log  # A15: actual Korean tests are in test_mechanics/NRComplaintLogTest
assert '202호 손잡이 옆 벽을 비추' not in game and '흔적이 남았을 만한 곳' in game  # A16

# B1: exact RED scripts, including unanswered and absent DAY 1 history.
original = '‘이번에는 문 좀 열어주세요.’'
heard = [
    '‘오늘부터 야간 근무 맡으시는 분이죠?’',
    '수화기 너머에서 첫날의 인수인계가 다시 시작된다.',
    '벨이 울리고, 누군가 받는다. 숨을 죽인 채 기다린다. 첫날의 나처럼.',
    '내 입에서, 그날 들었던 말이 나온다.', original,
]
unheard = [
    '벨이 한 번, 두 번 울린다. 저쪽은 받지 않는다.',
    '세 번, 네 번. 첫날의 나처럼.',
    '다섯 번째 벨이 끊기기 직전, 수화기가 들린다.',
    '나는 한 번도 들어 본 적 없는 말을, 처음부터 알고 있던 것처럼 한다.', original,
]
assert original in day['final_call']
assert end['final_scene_RED'].splitlines() == heard
assert end['final_scene_RED_unheard'].splitlines() == unheard
assert end['final_ending_RED'].splitlines()[-2:] == [original, '이번이 몇 번째인지, 나는 모른다.']
assert 'const bool Heard=Evidence.Contains(TEXT("final_call"));' in final
assert 'SceneKey=Heard?TEXT("final_scene_RED"):TEXT("final_scene_RED_unheard");' in final
assert 'Heard?TEXT("전화 너머 · 관리자"):TEXT("나 · 독백")' in final
assert '*It!=TEXT("final_call") && *It!=TEXT("final_call_ignored")' in final
assert 'Checkpoint.Found=Evidence' in game and 'Evidence=Checkpoint.Found' in game
ending_tests = (SRC / 'NREndingsTest.cpp').read_text(encoding='utf-8')
assert 'History<3' in ending_tests and 'RestoreCheckpoint();ClearEnd(this);' in ending_tests

# A1 decision: only second-call hearing selects a real-Minseo denial variant.
denial = '“전화요? 저 관리실에 전화한 적 없는데요. 202호 문도 안 열었어요.”'
meetings = ('minseo', 'resident_203', 'resident_203_safe',
            'final_minseo_located', 'final_minseo_rescued', 'final_minseo_waiting')
for key in meetings:
    docs = end if key.startswith('final_') else day
    variant = key + '_second_call'
    assert denial not in docs[key], key
    assert docs[variant].count(denial) == 1, variant
    assert docs[variant].replace(denial + '\n', '').replace('\n' + denial, '') == docs[key], variant
    for text in (docs[key], docs[variant]):
        assert '잠깐 열어' not in text and '문을 열어 봤' not in text, key
assert 'Evidence.Contains(TEXT("second_call")) && Documents.Contains(HeardVariant)?HeardVariant:Key' in game
assert 'StartDocumentVoice(DialogueKey)' in game and 'BeginComplaintDialogue(Key)' in game
assert 'Evidence.Add(Key); Record(TEXT("read"),Key);' in game
choice_tests = (SRC / 'NRChoice.cpp').read_text(encoding='utf-8')
assert all(f'TEXT("{key}")' in choice_tests for key in meetings)
assert 'unheard second call never adds Minseo denial' in choice_tests
assert 'checkpoint-preserved second-call hearing adds Minseo denial' in choice_tests

# B2: authored clues and actual prop placement agree, without changing RED triggers.
assert '307호 문 앞' in end['final_manager']
assert '문 앞 열쇠와 방 안의 회선함' in end['final_plan']
assert '문 앞에 떨어진 열쇠표' in end['final_box_locked']
assert 'NRLayout::DoorAnchor(2,6)+FVector(0,-25,2)' in final
assert '640.1f-Key->Mesh->Bounds.GetBox().Min.Z' in final
assert 'key pickup is safe and independent of entry or door closing' in ending_tests
for name in ('story-plan-v03.md', 'story-draft.md', 'endings-v1.md'):
    text = (ROOT / 'docs' / name).read_text(encoding='utf-8')
    assert '문 앞' in text and '방 안 회선함' in text, name
    assert '307호 안에 열쇠' not in text and '307호 안의 열쇠' not in text, name
    assert '307호 문밖 수납함' not in text, name
plan = (ROOT / 'docs/story-plan-v03.md').read_text(encoding='utf-8')
assert '의도된 부정확함' in plan and '사칭 존재' in plan
assert '이전 희생자였을 수 있음을 함의하나 확정하지 않는다' in plan
verification = (ROOT / 'docs/story-verification-2026-10-13.md').read_text(encoding='utf-8')
assert verification.count('결정됨(2026-10-14)') == 3
# No UHT-incompatible multi-declarator struct definitions.
assert not re.search(r'}\s*\w+\s*,\s*\w+\s*;', (SRC / 'NRGame.h').read_text(encoding='utf-8'))
print('STORY_REGRESSIONS_OK: A1-A16, RED hearing branches, conditional Minseo denial and key location; engine tests require a rebuilt package')
