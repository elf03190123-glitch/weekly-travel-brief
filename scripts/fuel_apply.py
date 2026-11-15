"""유류할증료 패치(JSON)를 data/brief-data.json 의 fuelTab · fuelTabTrn 에 반영한다.

사용:
  python3 -I scripts/fuel_apply.py <patch.json>            # 반영 (오류가 있으면 아무것도 바꾸지 않음)
  python3 -I scripts/fuel_apply.py <patch.json> --dry-run  # 검사만
  python3 -I scripts/fuel_apply.py --card                  # fuelTab 최신 월 기준 주간 판본 fuel 카드 JSON 출력

패치 형식 (필요한 항목만 넣는다):
{
  "month": "2026-12",                         # 적용 월 (fuelTab.year 와 같은 해만)
  "ke":  {"lvl": 23, "zones": {"~499": 50000, "500~999": 70000, ...}},   # 대한항공 구간표. 키 = fuelTab.zones[].band
  "roe": 1340.123456,                         # 그 달 적용 ROE (KRW/USD)
  "oz":  {"하와이": 251900, "뉴욕": 301200, "샌프란시스코": 301200, "스페인": 301200},  # 아시아나 계정별 편도
  "trn": {"groups": {"1군": 43400, "2군": 76000, ...}},                     # 트리니티항공 부과군표
  "ko":  {"zoneNote": "...", "note": "..."},   # 선택: 안내문 교체 (fuelTab)
  "en":  {"note": "..."},                      # 선택: 영문 안내문 교체 (fuelTab.en)
  "source": "대한항공 한국발 유류할증료 통보(2026.11.16)"   # 보고용
}
"""
import datetime, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data', 'brief-data.json')
BANDKEY = {'nyc': '6,500~9,999', 'sfo': '5,000~6,499', 'hnl': '4,000~4,999', 'bkk': '2,000~2,999',
           'ceb': '1,500~1,999', 'hkg': '1,000~1,499', 'tyo': '500~999'}
TBK = {'tg1': '1군', 'tg2': '2군', 'tg3': '3군', 'tg4': '4군', 'tg5': '5군', 'tg7': '7군'}
OZ_ACC = ['하와이', '뉴욕', '샌프란시스코', '라스베가스', '스페인', '타히티']


def today():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y.%m.%d')


def num(v, what, errs):
    if v is None:
        return None
    if isinstance(v, str):
        v = v.replace(',', '').replace('원', '').strip()
    try:
        f = float(v)
    except (TypeError, ValueError):
        errs.append(f'{what}: 숫자가 아님 ({v!r})')
        return None
    if f < 0:
        errs.append(f'{what}: 음수 ({v})')
    return int(round(f)) if float(f).is_integer() or what != 'roe' else f


def slot(tab, mo, errs, label):
    """tab.months 에서 mo(1~12)월 칸 index. 다음 달이면 칸을 만든다."""
    n = len(tab['months'])
    if mo <= n:
        return mo - 1
    if mo == n + 1:
        tab['months'].append({'m': f'{mo}월', 'lvl': None, 'roe': None})
        for s in tab['series']:
            s['vals'].append(None)
        for z in tab.get('zones') or []:
            z['vals'].append(None)
        return mo - 1
    errs.append(f'{label}: {n}월 다음은 {n + 1}월이어야 합니다({mo}월은 사이가 비어 반영하지 않음)')
    return None


def apply(D, P):
    errs, warn, done = [], [], []
    ym = str(P.get('month') or '')
    if len(ym) != 7 or ym[4] != '-':
        return [f'month 형식은 YYYY-MM ({ym!r})'], warn, done
    year, mo = ym[:4], int(ym[5:])
    F, T = D['fuelTab'], D.get('fuelTabTrn')
    if year != str(F['year']):
        return [f'{year}년 자료입니다. fuelTab 은 {F["year"]}년 탭이라 연도 전환이 필요합니다 — 사람이 정할 일이라 반영하지 않습니다.'], warn, done
    if not (1 <= mo <= 12):
        return [f'월이 잘못됨 ({mo})'], warn, done

    if P.get('ke') or P.get('roe') is not None or P.get('oz'):
        i = slot(F, mo, errs, '대한항공 탭')
        if i is not None:
            ke = P.get('ke') or {}
            zones = ke.get('zones') or {}
            bands = {z['band']: z for z in F['zones']}
            for b in zones:
                if b not in bands:
                    errs.append(f'대한항공 구간 {b!r} 가 탭에 없음 (있는 구간: {", ".join(bands)})')
            if zones:
                for b, z in bands.items():
                    if b in zones:  # 패치에 없는 구간은 그대로 둔다(정정할 때 일부 구간만 넣을 수 있음)
                        z['vals'][i] = num(zones[b], f'구간 {b}', errs)
                    v = z['vals'][i]
                    prev = z['vals'][i - 1] if i > 0 else None
                    if v is None:
                        warn.append(f'구간 {b}: 값 없음(빈칸)')
                    elif prev and abs(v - prev) / prev > 0.6:
                        warn.append(f'구간 {b}: 전월 {prev:,} → {v:,} ({(v - prev) / prev:+.0%}) 변동이 큼')
                for s in F['series']:
                    s['vals'][i] = bands[BANDKEY[s['id']]]['vals'][i]
                seq = [z['vals'][i] for z in F['zones'] if z['vals'][i] is not None]
                if seq != sorted(seq):
                    warn.append('먼 구간일수록 금액이 커야 하는데 순서가 맞지 않는 구간이 있음')
                if 'lvl' in ke:
                    F['months'][i]['lvl'] = num(ke['lvl'], 'lvl', errs)
                done.append(f'대한항공 {mo}월 구간표 ({len(zones)}개 구간)')
            if P.get('roe') is not None:
                r = num(P['roe'], 'roe', errs)
                if r is not None and not (800 <= r <= 2500):
                    errs.append(f'ROE {r} 가 범위(800~2500) 밖')
                F['months'][i]['roe'] = float(r) if r is not None else None
                done.append(f'{mo}월 ROE {r}')
            elif zones and F['months'][i].get('roe') is None:
                warn.append(f'{mo}월 ROE 가 없어 달러 탭의 {mo}월 값이 비어 보입니다 — ROE 자료 필요')
            if P.get('oz'):
                accs = {a['acc']: a for a in F.get('accounts') or []}
                for k, v in P['oz'].items():
                    if k not in OZ_ACC:
                        errs.append(f'아시아나 계정 {k!r} 를 모름 ({", ".join(OZ_ACC)})')
                    elif k in accs:
                        accs[k]['oz'] = num(v, f'아시아나 {k}', errs)
                F['oz'] = {'m': f'{mo}월', 'roe': F['months'][i].get('roe')}
                done.append(f'아시아나 {mo}월 계정별 값 {len(P["oz"])}개')
            for k, v in (P.get('ko') or {}).items():
                if k in ('zoneNote', 'note', 'sub', 'cycle'):
                    F[k] = v
            for k, v in (P.get('en') or {}).items():
                if k in ('note', 'sub', 'cycle'):
                    F.setdefault('en', {})[k] = v
            if done:
                F['updated'] = today()
                F['src'] = [F['src'][0], today()]
                if F.get('en', {}).get('src'):
                    F['en']['src'] = [F['en']['src'][0], today()]

    if P.get('trn'):
        if not T:
            errs.append('fuelTabTrn 이 없음')
        elif str(T['year']) != year:
            errs.append(f'트리니티 탭은 {T["year"]}년 탭이라 {year}년 자료를 넣지 않습니다')
        else:
            j = slot(T, mo, errs, '트리니티 탭')
            if j is not None:
                g = P['trn'].get('groups') or {}
                known = {z['k'] for z in T.get('zones') or []}
                for k in g:
                    if k not in known:
                        errs.append(f'트리니티 부과군 {k!r} 를 모름')
                for z in T.get('zones') or []:
                    if z['k'] in g:
                        z['vals'][j] = num(g[z['k']], f'트리니티 {z["k"]}', errs)
                for s in T['series']:
                    if TBK.get(s['id']) in g:
                        s['vals'][j] = num(g[TBK[s['id']]], f'트리니티 {TBK[s["id"]]}', errs)
                T['updated'] = today()
                done.append(f'트리니티항공 {mo}월 부과군표 ({len(g)}개 군)')
    if not done and not errs:
        errs.append('반영할 내용이 없음 (ke·roe·oz·trn 중 하나는 있어야 함)')
    return errs, warn, done


def card(D):
    """fuelTab 최신 월(대한항공 값이 있는 마지막 달) 기준 주간 판본 fuel 카드."""
    F = D['fuelTab']
    i = max(k for k in range(len(F['months'])) if any(s['vals'][k] is not None for s in F['series']))
    mo = int(F['months'][i]['m'].rstrip('월'))
    ke = {s['id']: s['vals'][i] for s in F['series']}
    oz = {a['acc']: a.get('oz') for a in F.get('accounts') or []}
    oz_m = (F.get('oz') or {}).get('m')
    keymap = {'하와이': 'hnl', '뉴욕': 'nyc', '샌프란시스코': 'sfo', '라스베가스': 'sfo', '스페인': 'sfo', '타히티': None}
    en = {'하와이': 'Hawaii', '뉴욕': 'New York', '샌프란시스코': 'San Francisco', '라스베가스': 'Las Vegas',
          '스페인': 'Spain', '타히티': 'Tahiti'}
    f = lambda v: None if v is None else f'{v:,}'
    rows = [{'acc': a, 'accen': en[a], 'ke': f(ke[keymap[a]]) if keymap[a] else None,
             'oz': None if a in ('라스베가스', '타히티') else f(oz.get(a))} for a in OZ_ACC]
    months_en = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
                 'October', 'November', 'December']
    note = '라스베가스는 아시아나 직항이 없어 대한항공(KE)만 해당합니다. 타히티는 대한항공·아시아나 모두 직항이 없어 해당없음으로 표시했습니다.'
    noteen = 'Las Vegas has no Asiana nonstop, so only Korean Air (KE) applies. Tahiti has no nonstop service on either carrier, shown as N/A.'
    if oz_m and oz_m != f'{mo}월':
        note += f' 대한항공(KE)은 유류할증료 탭의 {mo}월 구간표 값이며, 아시아나항공(OZ)은 {mo}월 표가 아직 반영되지 않아 {oz_m} 값을 그대로 두었습니다.'
        noteen += (f' Korean Air (KE) figures follow the {months_en[mo - 1]} zone table in the fuel surcharge tab; Asiana (OZ) '
                   f'figures still reflect the {months_en[int(oz_m.rstrip("월")) - 1]} table because the {months_en[mo - 1]} table has not yet been loaded.')
    return {'month': f'{F["year"]}년 {mo}월', 'monthen': f'{months_en[mo - 1]} {F["year"]}',
            'sub': '대한항공(KE)·아시아나항공(OZ) 국제선 편도 유류할증료 · 관광청 계정별 매칭',
            'suben': 'Korean Air (KE) and Asiana (OZ) one-way international fuel surcharge, matched to tourism board accounts',
            'rows': rows, 'note': note, 'noteen': noteen,
            'src': ['AVIAREPS Korea 유류할증료 집계 (국적사 공지 기준)', F['updated']]}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    D = json.load(open(DATA, encoding='utf-8'))
    if '--card' in sys.argv:
        print(json.dumps(card(D), ensure_ascii=False, indent=1))
        return
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    P = json.load(open(args[0], encoding='utf-8'))
    errs, warn, done = apply(D, P)
    for w in warn:
        print('주의:', w)
    if errs:
        for e in errs:
            print('오류:', e)
        sys.exit(f'오류 {len(errs)}건 — 반영하지 않았습니다.')
    for d in done:
        print('반영:', d)
    if '--dry-run' in sys.argv:
        print('(검사만 함)')
        return
    with open(DATA, 'w', encoding='utf-8') as fh:
        json.dump(D, fh, ensure_ascii=False, indent=0)
    res = os.path.join(os.path.dirname(os.path.abspath(args[0])), 'result.json')
    json.dump({'month': P['month'], 'done': done, 'warn': warn, 'source': P.get('source')},
              open(res, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('저장:', os.path.relpath(DATA, ROOT), '·', os.path.relpath(res, ROOT))


if __name__ == '__main__':
    main()
