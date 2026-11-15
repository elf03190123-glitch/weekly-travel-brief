"""data/brief-data.json 을 src/template.html 에 넣어 dist/index.html 을 만들고, 발행 전 규칙을 검사한다.

사용: python -I scripts/build.py            → 검사 + 빌드 (최신 판본에 오류가 있으면 실패)
      python -I scripts/build.py --check    → 검사만
검사 결과: 오류(ERROR)는 최신 판본만 발행을 막고, 과거 판본 문제는 경고(WARN)로만 보여 준다.
"""
import json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
HANGUL = re.compile(r'[가-힣]')
ACCS = ['하와이', '뉴욕', '샌프란시스코', '라스베가스', '스페인', '타히티']

tpl = open(os.path.join(ROOT, 'src', 'template.html'), encoding='utf-8').read()
D = json.load(open(os.path.join(ROOT, 'data', 'brief-data.json'), encoding='utf-8'))

def js_map(name):
    m = re.search(r'var ' + name + r'=\{(.*?)\};', tpl, re.S)
    return set(re.findall(r"'([^']+)':", m.group(1))) if m else set()
TAGEN = js_map('TAGEN') | set(D.get('tagenx', {}))
OUTEN = js_map('OUTEN') | set(D.get('outenx', {}))
SECS = {s['id'] for s in D['sections']}
CLIENTS = {c['id'] for c in D.get('clients', [])}
SLOTS = {s['id'] for s in D.get('clientSlots', [])}

def check_edition(E):
    errs = []
    def e(msg): errs.append(f"[{E.get('key')}] {msg}")
    for k in ('key', 'label', 'sublabel', 'issue', 'meta', 'board', 'items', 'foot'):
        if k not in E: e(f'필드 없음: {k}')
    for x in E.get('ind', []):
        if not x.get('ken') or not x.get('suben'): e(f"지표 영문(ken/suben) 누락: {x.get('k')}")
        if HANGUL.search((x.get('ken') or '') + (x.get('suben') or '')): e(f"지표 영문에 한글: {x.get('k')}")
    f = E.get('fuel')
    if f:
        for k in ('monthen', 'suben', 'noteen'):
            if not f.get(k): e(f'유류할증료 영문 필드 누락: fuel.{k}')
        accs = [r.get('acc') for r in f.get('rows', [])]
        if sorted(accs) != sorted(ACCS): e(f'유류할증료 rows 가 6개 계정과 다름: {accs}')
        for r in f.get('rows', []):
            for k in ('ke', 'oz'):
                if r.get(k) == '': e(f"유류할증료 빈 문자열(null 이어야 함): {r.get('acc')}.{k}")
    codes = set()
    for it in E.get('items', []):
        c = it.get('code')
        if c in codes: e(f'기사 코드 중복: {c}')
        codes.add(c)
        for k in ('code', 'sec', 'tags', 'koh', 'kop', 'enh', 'enp', 'src'):
            if not it.get(k): e(f'{c}: 필드 없음 {k}')
        if it.get('sec') not in SECS: e(f"{c}: 알 수 없는 섹션 {it.get('sec')}")
        if HANGUL.search((it.get('enh') or '') + (it.get('enp') or '')): e(f'{c}: 영문 요약에 한글')
        for t in it.get('tags', []):
            if len(t) != 2 or t[1] not in ('acc', 'mkt', 'fn'): e(f'{c}: 태그 형식 오류 {t}')
            elif t[0] not in TAGEN and HANGUL.search(t[0]): e(f'{c}: TAGEN 에 없는 태그 "{t[0]}" (템플릿 TAGEN 에 영문명 추가 필요)')
            if t[1] == 'acc' and t[0] not in ACCS: e(f'{c}: acc 태그는 6개 계정만 가능 "{t[0]}"')
        for x in it.get('cl', []) or []:
            if x.get('c') not in CLIENTS: e(f"{c}: 알 수 없는 고객사 id {x.get('c')} (data.clients 에 있는 id 만 가능)")
            if x.get('s') not in SLOTS: e(f"{c}: 고객사 칸은 A–E 만 가능: {x.get('s')}")
        if it.get('cl') and it.get('sec') in ('s1', 's4', 's2'):
            e(f'{c}: 공통 섹션(01–03) 기사에는 cl 을 붙이지 않는다')
        for s in it.get('src', []):
            if len(s) != 4: e(f'{c}: 출처는 [매체, 날짜, URL, 제목] 4개여야 함'); continue
            out = s[0]
            base = re.sub(r'\s*보도자료\s*\(1차 출처\)$', '', out)
            if HANGUL.search(out) and out not in OUTEN and base not in OUTEN:
                e(f'{c}: OUTEN 에 없는 매체 "{out}" (템플릿 OUTEN 에 영문명 추가 필요)')
            if not str(s[2]).startswith('http'): e(f'{c}: 출처 URL 형식 오류')
            if not re.match(r'^\d{4}\.\d{2}\.\d{2}$', str(s[1])): e(f'{c}: 출처 날짜 형식(YYYY.MM.DD) 오류 {s[1]}')
    for k in (E.get('clientNotes') or {}):
        if k not in CLIENTS: e(f'clientNotes: 알 수 없는 고객사 id {k}')
    if E.get('issue', {}).get('count') not in (None, len(E.get('items', []))):
        e(f"issue.count({E['issue']['count']}) ≠ 기사 수({len(E.get('items', []))})")
    return errs

eds = D['editions']
latest = eds[-1]
problems = 0
for E in eds:
    errs = check_edition(E)
    lvl = 'ERROR' if E is latest else 'WARN'
    for m in errs: print(lvl, m)
    if E is latest: problems = len(errs)
print(f'판본 {len(eds)}개 검사 · 최신 {latest["key"]} 오류 {problems}건')
for E in D.get('monthly', []):  # 월간은 make_monthly.py 가 주간 기사로 만든다 — 문제는 경고로만 보여 준다
    for m in check_edition(E): print('WARN(월간)', m)
print(f"월간 {len(D.get('monthly', []))}개")

if problems:
    sys.exit('최신 판본 오류가 있어 빌드를 멈춥니다.')
if '--check' in sys.argv:
    sys.exit(0)

blob = json.dumps(D, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
html = tpl.replace('__BRIEF_DATA__', blob)

# 개인 메일 금지 (워크스페이스 규칙): 결과물에 하나라도 있으면 빌드 실패.
# 공개 저장소라 주소를 그대로 적지 않고 SHA-256 으로만 비교한다.
import hashlib
BLOCKED = {'2500fea5b3ad48160327f31a7169c34ef64643c9aa28736a2e7281373eab60d0',
           '311f5463740aa658db25f397823bfe171c523e6cfe4aa1f74b21047153ce7b4b'}
for m in set(re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', html)):
    if hashlib.sha256(m.lower().encode()).hexdigest() in BLOCKED:
        sys.exit('개인 메일이 결과물에 있습니다 — 데이터/템플릿에서 지우고 AVIAREPS Korea 로 바꾸세요.')
os.makedirs(os.path.join(ROOT, 'dist'), exist_ok=True)
out = os.path.join(ROOT, 'dist', 'index.html')
open(out, 'w', encoding='utf-8').write(html)

# 스크립트 문법 검사 (node 가 있으면)
scripts = re.findall(r'<script>(.*?)</script>', html, re.S)
try:
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as t:
        t.write('\n;\n'.join(scripts)); tmp = t.name
    r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True, encoding='utf-8')
    os.unlink(tmp)
    if r.returncode != 0:
        sys.exit('스크립트 문법 오류:\n' + r.stderr[:2000])
    print('스크립트 문법 검사 통과')
except FileNotFoundError:
    print('node 없음 → 문법 검사 건너뜀')
print('dist/index.html 저장:', round(len(html.encode('utf-8')) / 1024), 'KB')
