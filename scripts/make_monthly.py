"""주간 브리프에 실린 기사를 기사 날짜(매달 1일~말일) 기준으로 모아 월간 브리프를 만든다 (LLM 없이 동작).

- 결과는 data/brief-data.json 의 최상위 `monthly` 배열에 월별 판본으로 저장한다(주간 `editions` 와 분리).
- 같은 기사(첫 출처 URL 기준)가 여러 주에 실렸으면 가장 최근 호의 것을 쓴다.
- 고객사 배치(cl)가 없는 예전 주간 기사는 관광청 계정 태그·섹션으로 칸을 추정해 채운다(화면의 추정 규칙과 같음).
- 시사점(clientNotes.<id>.so)은 쓰지 않는다. 이미 사람이 적어 둔 시사점은 다시 만들어도 보존한다.

사용: python -I scripts/make_monthly.py            # 기사가 5건 이상인 모든 달
      python -I scripts/make_monthly.py 2026-10    # 한 달만
"""
import calendar, json, os, sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'data', 'brief-data.json')
D = json.load(open(P, encoding='utf-8'))

COMMON = {'s1', 's4', 's2'}
OLDMAP = {'s5': 'B', 's3': 'C', 's6': 'C', 's9': 'C', 's7': 'D', 's8': 'E', 's10': 'B'}
PREFIX = {'s1': 'PE', 's4': 'CS', 's2': 'OB', 's5': 'AL', 's3': 'TT', 's6': 'PL', 's9': 'PK', 's7': 'CD', 's8': 'CW', 's10': 'AS'}
SECORDER = [s['id'] for s in D['sections']]
CLIENTS = D.get('clients', [])
MON = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
MIN_ITEMS = 5


def adate(i):
    return str(i['src'][0][1])  # 'YYYY.MM.DD'


def derive_cl(i):
    """cl 이 없는 예전 기사 → 화면(slotOf)과 같은 규칙으로 고객사 칸 추정."""
    if i['sec'] in COMMON:
        return []
    tags = [t[0] for t in i.get('tags', [])]
    acc = {t[0] for t in i.get('tags', []) if t[1] == 'acc'}
    common = '장거리 전 계정' in tags
    out = []
    for c in CLIENTS:
        if c.get('acc') and (c['acc'] in acc or common):
            out.append({'c': c['id'], 's': OLDMAP.get(i['sec'], 'C')})
    if i['sec'] == 's10':
        if '아프리카' in tags:
            out.append({'c': 'airlink', 's': 'B'})
        if '남미' in tags:
            out.append({'c': 'azul', 's': 'B'})
    return out


def build(month, weekly, old):
    y, m = map(int, month.split('-'))
    last = calendar.monthrange(y, m)[1]
    pick, srcs = {}, []
    for E in weekly:
        has_cl = any(i.get('cl') for i in E['items'])
        used = False
        for i in E['items']:
            d = adate(i)
            if d[:7].replace('.', '-') != month:
                continue
            x = json.loads(json.dumps(i))
            if not has_cl and not x.get('cl'):
                cl = derive_cl(x)
                if cl:
                    x['cl'] = cl
            x['wk'] = E['label']
            pick[str(x['src'][0][2])] = x  # 같은 기사는 최근 호가 덮어씀
            used = True
        if used:
            srcs.append(E)
    items = list(pick.values())
    if len(items) < MIN_ITEMS:
        return None
    items.sort(key=lambda i: (SECORDER.index(i['sec']) if i['sec'] in SECORDER else 99, adate(i)))
    n = {}
    for i in items:
        p = PREFIX.get(i['sec'], 'XX')
        n[p] = n.get(p, 0) + 1
        i['code'] = f'{p}-{n[p]:02d}'
    latest = srcs[-1]
    first_d, last_d = min(adate(i) for i in items), max(adate(i) for i in items)
    # 계정 스코어보드(관광청 6곳): 이번 달 acc 태그 기사 수
    board = []
    for c in [c for c in CLIENTS if c.get('acc')]:
        hits = [i for i in items if any(t[1] == 'acc' and t[0] == c['acc'] for t in i['tags'])]
        board.append({'n': len(hits), 'nm': c['acc'],
                      'ds': (hits[-1]['koh'][:40] + ' 등') if hits else '이번 달 직접 연결 기사 없음'})
    board.sort(key=lambda b: -b['n'])
    for k, b in enumerate(board):
        if b['n'] <= 1:
            b['cold'] = True
        elif k < 3:
            b['hot'] = True
    labels = [E['label'] for E in srcs]
    gaps = [g for g in D.get('gaps', []) if g['from'][:7] <= month <= g['to'][:7]]
    gap_txt = (' 주간 발행이 없었던 기간(' + ', '.join(f"{g['label']} {g['from'][5:]}~{g['to'][5:]}" for g in gaps) +
               ')의 기사는 포함되지 않습니다.') if gaps else ''
    notes = {}
    for c in CLIENTS:
        cnt = sum(1 for i in items if any(x['c'] == c['id'] for x in i.get('cl', [])))
        prev = (old.get('clientNotes') or {}).get(c['id'], {})
        note = {}
        if prev.get('so'):
            note['so'] = prev['so']  # 사람이 적은 시사점 보존
        if cnt == 0:
            note['watch'] = [[c['en'].upper(), f"{c['full']} — 이번 달 주간 브리프에 실린 관련 기사 없음"]]
        if note:
            notes[c['id']] = note
    E = {
        'kind': 'monthly',
        'key': f'm{month}',
        'label': f'{month} 월간',
        'sublabel': f'{MON[m - 1]} 1–{last}',
        'issue': {'no': month, 'range': f'{MON[m - 1]} 1–{last}, {y}', 'count': len(items)},
        'meta': [['수록', f'{len(items)}건 (기사 날짜 {first_d}~{last_d})'],
                 ['원천', '주간 브리프 ' + ' · '.join(labels) + ' 발췌, 중복 제외'],
                 ['작성', 'AVIAREPS Korea']],
        'ind': latest.get('ind', []),
        'board': board,
        'items': items,
        'gap': latest.get('gap'),
        'foot': (f'이 월간 브리프는 주간 브리프({" · ".join(labels)})에 실린 기사 중 기사 날짜가 {y}년 {m}월인 건을 모아 '
                 f'고객사별로 다시 묶은 것입니다. 지표·유류할증료·워치리스트는 이 달의 마지막 주간 호({latest["label"]}) 기준입니다.' + gap_txt),
        'clientNotes': notes,
    }
    if latest.get('fuel'):
        E['fuel'] = latest['fuel']
    return E


def main():
    # 팀 수집본(manual)은 W35와 같은 주라 먼저 넣고 자동 주간판이 같은 기사를 덮어쓰게 한다(manual 에만 있는 기사도 포함)
    manual = [E for E in D['editions'] if E.get('key') == 'manual']
    weekly = manual + [E for E in D['editions'] if E.get('key') != 'manual']
    months = sorted({adate(i)[:7].replace('.', '-') for E in weekly for i in E['items']})
    if len(sys.argv) > 1:
        months = [sys.argv[1]]
    old = {E['key']: E for E in D.get('monthly', [])}
    out = {E['key']: E for E in D.get('monthly', [])}
    for mo in months:
        E = build(mo, weekly, old.get(f'm{mo}', {}))
        if E:
            out[E['key']] = E
            print(f"{mo}: {E['issue']['count']}건 · 원천 {E['meta'][1][1]}")
        else:
            print(f'{mo}: 기사 {MIN_ITEMS}건 미만 → 건너뜀')
    D['monthly'] = [out[k] for k in sorted(out)]
    json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
