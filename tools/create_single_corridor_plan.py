"""Draw review-only floor plans from the current NRLayout anchors. No game edits."""
from pathlib import Path
import json
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Art/EnvironmentConcepts/v10-access'
OUT.mkdir(parents=True, exist_ok=True)
FONT = 'C:/Windows/Fonts/malgun.ttf'
BOLD = 'C:/Windows/Fonts/malgunbd.ttf'
BG, FG, MUTED = '#121b22', '#edf0e9', '#9fadb5'
WALL, HALL, ROOM = '#9aa29f', '#305852', '#4c4c48'
DOOR, WINDOW, CHANGE = '#f3c779', '#83c8df', '#d48677'
S = .34
OCCUPIED = {1: (101, 102, 104, 105, 107), 2: (203, 204, 206, 208, 211), 3: (301, 303, 305, 308, 311)}
INVESTIGABLE = {1: (103, 106, 109), 2: (201, 202, 209), 3: (302, 307, 310)}


def font(size=16, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)


def render(floor, current=False):
    image = Image.new('RGB', (1780, 850), BG)
    d = ImageDraw.Draw(image)

    def point(x, y):
        return (70 + (x + 800) * S, 160 + (230 - y) * S)

    def text(x, y, message, size=15, color=FG, anchor='mm', bold=False):
        d.text(point(x, y), message, font=font(size, bold), fill=color, anchor=anchor,
               align='center', spacing=5)

    def rect(x1, y1, x2, y2, fill, outline=WALL, width=2):
        a, b = point(x1, y1), point(x2, y2)
        box = (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))
        d.rectangle(box, fill=fill, outline=outline, width=width)

    def line(x1, y1, x2, y2, color=WALL, width=3):
        d.line([point(x1, y1), point(x2, y2)], fill=color, width=width)

    def opening(x1, y1, x2, y2, color=DOOR, swing=False):
        if color == DOOR:
            line(x1, y1, x2, y2, HALL, 9)
        line(x1, y1, x2, y2, color, 2 if swing else 6)
        if swing:
            # Diagrammatic inward door leaf and sweep; no art-generation guesswork.
            radius = math.hypot(x2-x1, y2-y1)
            start = math.atan2(y2-y1, x2-x1)
            stop = start - math.pi/2
            arc = [point(x1+radius*math.cos(start+(stop-start)*i/24),
                         y1+radius*math.sin(start+(stop-start)*i/24)) for i in range(25)]
            d.line(arc, fill=DOOR, width=2)
            line(x1, y1, x1+radius*math.cos(stop), y1+radius*math.sin(stop), DOOR, 3)

    def arrow(points, color=DOOR, width=3):
        import math
        points = [point(*p) for p in points]
        d.line(points, fill=color, width=width)
        a, b = points[-2:]
        ang = math.atan2(b[1]-a[1], b[0]-a[0])
        d.polygon([b, (b[0]-11*math.cos(ang-.5), b[1]-11*math.sin(ang-.5)),
                   (b[0]-11*math.cos(ang+.5), b[1]-11*math.sin(ang+.5))], fill=color)

    roof = floor == 4
    name = '옥상 · 4층 높이' if roof else f'{floor}층'
    state = '현재 구현 기준' if current else '수정안 · 이미지 검토 전용'
    d.text((70, 28), f'해담고시원   /   {name}', font=font(30, True), fill=FG)
    d.text((70, 77), state, font=font(17, True), fill=DOOR)
    sub = '실행 중인 게임은 변경하지 않았습니다. 구조 검토용 평면이며 건축 시공 도면이 아닙니다.'
    d.text((70, 109), sub, font=font(15), fill=MUTED)

    rect(-500, 230, 3900, -1300 if current else -900, '#273239', WALL, 3)
    if not current:
        # Rear strip is explicitly removed, not disguised as another passage.
        rect(-500, -905, 3900, -1300, '#211f24', '#634b4b', 1)
        for x in range(-500, 3800, 110):
            line(x, -1300, min(x+260, 3900), -910, '#3c3035', 1)
        text(1700, -1095, '기존 뒤 복도 4m 띠 공간 제외안 · 실내 통행 없음', 19, CHANGE, bold=True)

    def stair():
        rect(3500, -200, 3900, -900, '#514b5b')
        if current:
            for y in range(-230, -630, -26):
                line(3540, y, 3860, y, '#938b9b', 1)
            arrow([(3700, -240), (3700, -850)])
            text(3700, -750, '일자 계단\n위층 뒤 복도로', 13)
            if floor == 1:
                opening(3610, -200, 3790, -200)
            else:
                line(3500, -200, 3900, -200, WALL, 5)
            opening(3610, -900, 3790, -900)
        else:
            for y in range(-420, -690, -30):
                line(3540, y, 3670, y, '#b2a7bc', 1)
                line(3730, y, 3860, y, '#b2a7bc', 1)
            arrow([(3605, -410), (3605, -760), (3795, -760), (3795, -410)])
            text(3700, -300, '꺾임 계단', 15, bold=True)
            text(3700, -835, '반 층 계단참', 12)
            opening(3600, -200, 3800, -200)

    if roof:
        rect(-500, 230, 3500, -900, '#344e48')
        stair()
        text(3700, 20, '주계단 출입', 15, DOOR)
        # External escape stair is a proposed branch, not a second hallway.
        rect(-760, -70, -520, -850, '#514b5b', CHANGE)
        rect(-520, -70, -495, -200, HALL, HALL, 1)
        opening(-500, -90, -500, -180)
        text(-640, -430, '비상\n계단\n(외부)', 13)
        text(650, 40, '건물 외곽 안의 옥상 · 별도 주거층 없음', 17, bold=True)
        rect(2700, -370, 3380, -850, '#59645e')
        text(3030, -570, '처마 아래 세탁 자리\n세탁기 · 개수대\n바구니', 16)
        for i in range(3):
            y = -280 - i * 150
            line(750, y, 2180, y, '#bbbca4', 3)
            for x in (900, 1300, 1700):
                rect(x, y+30, x+180, y-40, '#b3b5a8', '#d6d4c6', 1)
        text(1470, -760, '빨래 건조 구역 · 천 사이 목격 / 조사', 17)
        rect(-350, -570, 350, -810, '#4f6064')
        text(0, -690, '물탱크 · 설비', 15)
        arrow([(3650, -100), (3000, -100), (2400, -100), (2400, -720), (520, -720), (520, -100), (-450, -100)], '#83b7a4')
        opening(3600, -200, 3800, -200)
    else:
        rect(-500, 230, 350, -200, '#305852')
        text(-60, 35, '현관' if floor == 1 else '층 앞쪽 공간', 17, bold=True)
        rect(350, -70, 3900, -200, HALL)
        line(350, -77, 350, -193, HALL, 6)
        text(1780, -137, '현재 폭 1.30m 유지 · 방 앞 복도 한 줄' if not current else '현재 주 복도 · 명목 폭 1.30m', 15, '#d3ebe0')
        for n in range(12):
            x = 350 + n * 230
            number = floor*100 + n + 1
            key = number in (104, 105, 202, 203, 301, 307)
            rect(x, 230, x+230, -70, '#675946' if key else ROOM)
            vacant = not current and number not in OCCUPIED[floor]
            if vacant:
                if number in INVESTIGABLE[floor]:
                    rect(x+138, 210, x+220, 32, '#675946', '#b8ab8a', 2)
                    for by in (175, 135, 95, 55):
                        line(x+138, by, x+220, by, '#b8ab8a', 1)
                    rect(x+15, 210, x+100, 163, '#83745d', '#b8ab8a', 1)
                text(x+67, 35, '조사' if number in INVESTIGABLE[floor] else '공실', 12, DOOR)
            else:
                rect(x+138, 210, x+220, 32, '#777a71', '#999b8e', 1)
                if not current:
                    text(x+67, 35, '거주', 12, '#b9ddbf')
            text(x+67, 120, str(number), 16, bold=key)
            opening(x+25, -70, x+95, -70)
            opening(x+115, 230, x+195, 230, WINDOW)
        text(1730, 305, '입주실 12개 유지 · 한 칸 2.30 × 3.00m 배치 모듈 (벽 두께 제외 전)' if current else '층당 5명 거주 · 조사 가능한 빈방 3곳 · 나머지 공실 4곳 / 방 크기 유지', 16, MUTED)
        if current:
            rect(3110, 230, 3900, -70, '#394047')
            text(3500, 100, '기존 복도 끝 구역', 14)
        else:
            rect(3110, 230, 3900, -200, HALL)
            line(3110, -77, 3110, -193, HALL, 6)
            text(3500, 90, '경계벽 철거 · 넓어진 복도 끝', 14)
            text(3500, 5, '계단 맞은편 / 외벽 유지', 12, MUTED)
        # Preserve office and its short side access, cut the old rear connection.
        rect(-140, -200, 140, -480, '#795e41')
        text(0, -335, '관리실' if floor == 1 else '관리 수납', 16, bold=True)
        if floor == 1:
            opening(-70, 230, 70, 230)
            opening(-130, -200, 130, -200, WINDOW)
        rect(150, -200, 430, -480 if not current else -900, HALL)
        line(160, -200, 420, -200, HALL, 6)
        opening(140, -266.5, 140, -353.5, swing=not current)
        if not current:
            text(280, -395, '옆문', 12)
            rect(-500, -480, 430, -900, '#394047')
            text(-35, -690, '기존 후면 여유부\n창고·설비 / 통과 불가', 15)
            opening(245, -480, 335, -480)
            rect(-500, -200, -140, -480, '#394047')
            text(-340, -345, '옆 수납방', 13)
            opening(-140, -275, -140, -365, swing=True)
            arrow([(110,-400),(-70,-400),(-70,-320),(-265,-320)], '#83b7a4', 2)
            if floor == 1:
                # Match the live office footprint and front-facing desk.
                rect(-132, -208, 132, -263, '#94794f', '#c5b389', 1)
                text(0, -236, '책상 264cm', 10)
                rect(-22, -350, 22, -395, '#6c7773', '#b9c2bb', 1)
                text(10, -445, '뒤쪽 휴식 여유', 10, MUTED)
                text(0, -170, '아래 벽 · 위 유리', 11, WINDOW)
            else:
                text(0, -445, '옆방 연결문 ←', 11, DOOR)
            rect(-760, -70, -520, -850, '#514b5b', CHANGE)
            rect(-520, -70, -495, -200, HALL, HALL, 1)
            opening(-500, -90, -500, -180)
            text(-640, -420, '비상\n계단\n(외부)', 13)
            text(-640, -805, '제안', 12, CHANGE)
        else:
            rect(-500, -200, -200, -900, HALL)
            rect(-140, -480, 140, -900, '#394047')
            rect(-500, -900, 3900, -1300, HALL)
            text(1730, -1100, '현재 뒤쪽 복도 · 폭 4m / 주방·휴게공간 뒤로 연결', 18, '#c4dfd2')
            opening(-450, -1300, 3850, -1300, WINDOW)
        rooms = [(430, 1300, '공용주방', '#655d40'),
                 (1350, 2150, '화장실 · 세면', '#3c5662'),
                 (2200, 3400, '휴게공간', '#535d4a')]
        expanded_kitchen = not current and floor in (2, 3)
        if expanded_kitchen:
            rooms = [(430, 2150, '공용주방 · 식사 공간', '#655d40'),
                     (2200, 2550, '별도 샤워실', '#456777'),
                     (2600, 3400, '화장실 · 세면', '#3c5662')]
        elif not current:
            rooms[2] = (2200, 3400, '별도 샤워실', '#456777')
        for left, right, title, color in rooms:
            rect(left, -200, right, -900, color)
            cx = (left+right)/2
            kitchen = not current and left == 430
            if kitchen:
                rect(cx-85, -200, cx+85, -370, '#426b58', '#65987b', 1)
                text(cx, -310, '문 앞 비움', 13)
                text(cx, -420, title + ' / 원형 식탁 2개', 14 if floor == 1 else 18, bold=True)
                for tx in ((680, 1070) if floor == 1 else (900, 1750)):
                    a, b = point(tx-75, -515), point(tx+75, -665)
                    d.ellipse((a[0], a[1], b[0], b[1]), fill='#967c51', outline='#d7bd8d', width=2)
                    for angle in range(0, 360, 60):
                        rad = math.radians(angle)
                        sx, sy = tx + 120*math.cos(rad), -590 + 120*math.sin(rad)
                        rect(sx-20, sy+20, sx+20, sy-20, '#8b886a', '#baba9e', 1)
                rect(left+80, -810, right-320, -880, '#767f7d')
                text((left+right-240)/2, -847, '문 반대편 조리대 · 싱크', 12)
                rect(right-250, -780, right-40, -880, '#767f7d')
                text(right-145, -835, '냉장고', 12)
                if floor == 3:
                    text(760, -730, '리모델링 마감 / 안쪽 보수 흔적 조사', 12, DOOR)
            elif not current and title == '별도 샤워실':
                text(cx, -295, '별도 샤워실', 13 if expanded_kitchen else 18, bold=True)
                if expanded_kitchen:
                    for top in (-375, -545, -715):
                        rect(left+155, top, right-20, top-150, '#648f9a')
                        opening(left+155, top-40, left+155, top-110)
                    text(left+65, -610, '통로', 11)
                else:
                    text(cx, -470, '탈의 · 수건 보관', 16)
                    for sx in (left+120, left+380, left+640, left+900):
                        rect(sx, -650, sx+180, -880, '#648f9a')
                        opening(sx+40, -650, sx+120, -650)
            elif not current and title == '화장실 · 세면':
                text(cx, -295, '화장실 · 세면만', 15, bold=True)
                for sy in (-410, -590):
                    rect(left+30, sy+60, left+140, sy-60, '#829e9f')
                    text(left+85, sy, '세면', 12)
                for top in (-365, -555):
                    rect(right-310, top, right-30, top-175, '#587079')
                    opening(right-310, top-50, right-310, top-120)
                    arrow([(right-70, top-87), (right-260, top-87)], '#d2ddda', 2)
                text(cx, -815, '샤워 시설 없음', 14)
            else:
                text(cx, -520, title, 19, bold=True)
                text(cx, -625, '앞 복도에서 출입' if not current else '기존 공용공간', 14)
            opening(cx-45, -200, cx+45, -200, swing=not current)
            if not current:
                arrow([(cx,-130),(cx,-260)], '#a9ead1', 3)
                text(cx+85, -235, '출입', 11, DOOR)
            if current and left != 1350:
                opening(cx-65, -900, cx+65, -900)
            elif not current:
                opening(cx-125, -900, cx+125, -900, WINDOW)
        stair()
        if floor == 3:
            text(-80, -120, '옛 비상문 조사', 12, DOOR)

    d.line((70, 730, 1700, 730), fill='#34424a', width=1)
    d.text((70, 750), '청록: 이동 공간    노랑: 출입구    하늘색: 창 / 유리    보라: 계단    빗금: 제외 제안', font=font(17), fill=FG)
    note = ('현행 코드의 좌표를 도식화했습니다. 기존 웹 평면도의 6실·4m 주 복도 표기는 과거 값입니다.' if current else
            '각 층 별도 샤워실 · 화장실은 변기/세면만 · 식탁 2개 · 계단 맞은편 복도 끝 개방 · 핵심 방 공실')
    d.text((70, 786), note, font=font(15), fill=MUTED)
    filename = f'{"current" if current else "proposed"}-{floor if not roof else "roof"}.png'
    image.save(OUT / filename)
    return filename


files = {str(n): render(n) for n in (1, 2, 3, 4)}
manifest = {
    'status': 'pending_image_review', 'date': '2026-10-12',
    'generator': 'deterministic Pillow diagram; not an edited AI render',
    'preserved_cm': {'room_pitch': 230, 'room_depth': 300, 'nominal_hall_width': 130,
                     'office_width': 280, 'office_depth': 280, 'office_side_door': 87},
    'routes': ['corridor -> kitchen', 'corridor -> toilets', 'corridor -> showers',
               'corridor -> side approach -> management room -> adjacent storage',
               'corridor -> side approach -> rear storage (dead end)'],
    'office': 'floor1 caretaker office; floors2/3 management storage, not new offices',
    'third_floor': 'renovated clean finishes; unchanged partition layout',
    'occupied_rooms': OCCUPIED, 'investigable_rooms': INVESTIGABLE,
    'images': files, 'game_changed': False,
}
(OUT/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
page = """<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>해담고시원 · 출입 동선 수정 v10</title><style>
*{box-sizing:border-box}body{margin:0;background:#121b22;color:#edf0e9;font:16px/1.8 system-ui,sans-serif}main{max-width:1600px;margin:auto;padding:30px 22px}h1{font-size:30px}p{color:#bdc9c7}nav{display:flex;gap:10px;flex-wrap:wrap;margin:24px 0}button{font:inherit;color:#eef3ec;background:#253b3d;border:1px solid #63827b;padding:9px 20px;cursor:pointer}button[aria-pressed=true]{background:#4c7667}img{display:block;width:100%;height:auto;border:1px solid #394c50}a{color:#a7dcc9}.callout{padding:16px 22px;background:#22312f;border-left:3px solid #f3c779}.office{max-width:1100px}strong{color:#f3c779}</style>
<main><h1>출입문과 연결 동선 · 수정 v10</h1><p>구조 검토용 평면 · 실제 게임은 아직 변경하지 않았습니다.</p>
<div class="callout"><strong>주방·화장실·샤워실에는 각각 복도에서 직접 들어가는 문이 있습니다.</strong><br>민트 화살표는 진입 방향, 노란 원호는 문이 열리는 방향입니다. 출입문 앞은 비워 둡니다.</div>
<nav><button data-floor="1" aria-pressed="true">1층</button><button data-floor="2" aria-pressed="false">2층</button><button data-floor="3" aria-pressed="false">3층 · 리모델링</button><button data-floor="4" aria-pressed="false">옥상</button></nav>
<p id="note"></p><a id="full" href="../Art/EnvironmentConcepts/v10-access/proposed-1.png"><img id="plan" src="../Art/EnvironmentConcepts/v10-access/proposed-1.png" alt="출입문이 표시된 층별 평면"></a>
<h2>관리실과 옆 수납방</h2><p>1층 관리실은 현재 게임의 약 2.8×2.8m 크기와 264cm 책상을 기준으로 복원합니다. 전면은 아래 130cm 벽·위 유리, 오른쪽 87cm 옆문으로 들어갑니다. 벽을 움푹 파서 문을 두지 않고 오른쪽 벽선을 뒤까지 이어갑니다. 새 연결문은 책상과 겹치지 않는 왼쪽 벽에 둡니다.</p>
<p>2·3층의 같은 위치는 <strong>관리 수납실</strong>입니다. 복도 → 오른쪽 짧은 접근 공간 → 관리 수납실 → 왼쪽 연결문 → 옆 수납방으로 들어갑니다. 뒤 창고는 짧은 접근 공간 끝의 문을 통해 들어가는 막힌 방이며, 두 번째 평행 복도로 연결되지 않습니다.</p>
<p>3층은 깨끗한 리모델링 마감, 1·2층은 기존 노후 마감입니다. 방 크기·공용공간·원형 식탁 2개는 유지합니다.</p>
<p><a href="meshy-map-preview.html?v=access-v10">외형 참고 이미지와 제작 시안</a> · <a href="building-access-v10.md">수정 기록</a></p></main>
<script>const notes={1:'주 복도에서 주방·화장실·샤워실로 각각 직접 출입합니다. 관리실 오른쪽 옆문과 왼쪽 수납 연결문을 표시했습니다.',2:'관리 수납실을 통과해 왼쪽 옆 수납방으로 들어갑니다. 공용공간 세 곳은 각자 복도 출입문이 있습니다.',3:'2층과 같은 출입 구조입니다. 3층의 깨끗한 마감과 307호 공실 설정을 유지합니다.',4:'옥상 출입은 오른쪽 주계단과 왼쪽 외부 비상계단으로 연결합니다.'};function choose(f){const p='../Art/EnvironmentConcepts/v10-access/proposed-'+(f===4?'roof':f)+'.png';document.querySelector('#plan').src=p;document.querySelector('#full').href=p;document.querySelector('#note').textContent=notes[f];document.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',Number(b.dataset.floor)===f))}document.querySelectorAll('button').forEach(b=>b.onclick=()=>choose(Number(b.dataset.floor)));choose(1);</script></html>"""
(ROOT/'docs/floor-plan.html').write_text(page, encoding='utf-8')
print('ACCESS_PLAN_RENDERED: four proposed floors; no game changes')
