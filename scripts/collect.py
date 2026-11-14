"""주간 트래블 브리프 기사 수집기 (LLM 없이 동작).

대부분의 RSS는 최근 1~4일치만 보여 주므로, 매일 실행해 data/inbox/ 에 쌓아 두고
주간 발행 때 그 주 기간만 잘라 후보 목록을 만든다.

사용 (프로젝트 폴더에서):
  python -I scripts/collect.py                       # 수집만 (매일 실행)
  python -I scripts/collect.py --window 2026-11-09T10:00 2026-11-16T10:00 --label 2026-W46
                                                      # 수집 + 기간 후보 목록 → runs/<label>/
결과:
  data/inbox/items.jsonl   누적 기사(링크 기준 중복 제거)
  data/inbox/health.jsonl  실행별 소스 상태
  runs/<label>/candidates.md / candidates.json / fx.json
"""
import argparse, datetime as dt, email.utils, html, json, os, re, sys, urllib.request

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX = os.path.join(ROOT, 'data', 'inbox')
KST = dt.timezone(dt.timedelta(hours=9))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) WeeklyBriefCollector/2.0'}

# (이름, URL, 종류, 메모)  종류: rss / gtn
SOURCES = [
    ('트래블데일리', 'https://www.traveldaily.co.kr/rss/allArticle.xml', 'rss', '약 4일치'),
    ('여행신문', 'https://www.traveltimes.co.kr/rss/allArticle.xml', 'rss', '약 9일치'),
    ('트래비', 'https://www.travie.com/rss/allArticle.xml', 'rss', '약 3주치'),
    ('디스커버리뉴스', 'https://www.discoverynews.kr/rss/allArticle.xml', 'rss', '약 1일치 · 지자체 기사 혼재'),
    ('TTL뉴스', 'https://www.ttlnews.com/rss/allArticle.xml', 'rss', '약 1일치'),
    ('인사이트코리아', 'https://www.insightkorea.co.kr/rss/allArticle.xml', 'rss', '1일 미만'),
    ('이데일리', 'http://rss.edaily.co.kr/edaily_news.xml', 'rss', '약 1시간치 · 전체 뉴스'),
    ('연합뉴스', 'https://www.yna.co.kr/rss/economy.xml', 'rss', '경제'),
    ('연합뉴스', 'https://www.yna.co.kr/rss/industry.xml', 'rss', '산업'),
    ('연합뉴스', 'https://www.yna.co.kr/rss/culture.xml', 'rss', '문화'),
    ('뉴시스', 'https://newsis.com/RSS/economy.xml', 'rss', '경제'),
    ('뉴시스', 'https://newsis.com/RSS/culture.xml', 'rss', '문화'),
    ('세계여행신문', 'https://www.gtn.co.kr/home/news/news.asp', 'gtn', 'RSS 없음 · 목록(날짜 없음)'),
    ('Rio Times Online', 'https://riotimesonline.com/feed/', 'rss', '남미'),
    ('Further Africa', 'https://furtherafrica.com/feed/', 'rss', '아프리카'),
]
# 종합지(연합·뉴시스·이데일리)는 여행·항공 관련 키워드가 제목에 있을 때만 보관
GENERAL = {'연합뉴스', '뉴시스', '이데일리', 'Rio Times Online', 'Further Africa'}
TRAVEL_KW = ['여행', '관광', '항공', '공항', '출국', '해외', '면세', '호텔', '크루즈', '환율', '유가', '유류할증료', '비자', '여권',
             '노선', '취항', '증편', '운항', '소비자심리', 'CCSI', '소비자동향', 'OTA', '숙박', '패키지', '하나투어', '모두투어',
             'airline', 'airport', 'tourism', 'travel', 'route', 'flight', 'Airways', 'Air ', 'LATAM', 'Azul', 'Gol', 'Avianca',
             'Copa', 'Ethiopian', 'Kenya Airways', 'safari', 'hotel', 'cruise']

# 제목에 있으면 후보 목록에서 절대 빠지면 안 되는 키워드 (skill 「누락 방지 스캔」)
MUST = {
    '대상사': ['하나투어', '모두투어', '참좋은여행', '노랑풍선', '롯데관광', '교원투어', '롯데JTB', '한진관광', '홈앤쇼핑',
             '놀유니버스', '마이리얼트립', '트립닷컴', '여기어때', '클럽로뎀', '타이드스퀘어', '레드캡'],
    '계정': ['뉴욕', '샌프란시스코', '하와이', '라스베가스', '라스베이거스', '스페인', '바르셀로나', '마드리드', '타히티',
            '폴리네시아', 'Hawaii', 'New York', 'San Francisco', 'Las Vegas', 'Spain', 'Tahiti'],
    '계정 캐리어': ['에어프레미아', '아웃리거', '팜투어', '하와이안항공', '알래스카항공', '에어타히티누이', '이베리아', '델타',
              '유나이티드', '아메리칸항공', '트리니티항공', '티웨이'],
    '아프리카·남미': ['아프리카', '남미', 'LATAM', '아줄', 'Azul', '아비앙카', 'Avianca', '코파항공', 'Copa', '에티오피아항공',
                'Ethiopian', '케냐항공', 'Kenya Airways', '남아공', '사파리', '케이프타운', '상파울루', '부에노스아이레스', '리우',
                'Africa', 'South America'],
    '지표': ['소비자심리지수', 'CCSI', '소비자동향조사', '환율', '원·달러', '원/달러'],
}
DROP_KW = ['인사', '승진', '부고', '수상', '시상', '채용', '봉사', '기부', '축제']  # 표시만, 지우지 않음


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    for enc in ('utf-8', 'euc-kr', 'cp949'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', 'ignore')


def clean(t):
    t = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', t or '', flags=re.S)
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', html.unescape(t)).strip()


def parse_date(s):
    s = (s or '').strip()
    if not s:
        return None
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?$', s)
    if m:  # 국내 뉴스 솔루션(ndsoft) 형식: KST 로 간주
        y, mo, d, h, mi, se = (int(x or 0) for x in m.groups())
        return dt.datetime(y, mo, d, h, mi, se, tzinfo=KST)
    try:
        d = email.utils.parsedate_to_datetime(s)
        return d if d.tzinfo else d.replace(tzinfo=KST)
    except Exception:
        return None


def parse_rss(xml):
    out = []
    for it in re.findall(r'<item\b.*?</item>', xml, re.S):
        g = lambda tag: (re.search(r'<' + tag + r'\b[^>]*>(.*?)</' + tag + '>', it, re.S) or [None, ''])[1]
        link = clean(g('link')) or clean(g('guid'))
        out.append({'title': clean(g('title')), 'link': link, 'date': parse_date(clean(g('pubDate')) or clean(g('dc:date'))),
                    'desc': clean(g('description'))[:300]})
    return out


def parse_gtn(page):
    out = []
    for seq, title in re.findall(r"news_view\.asp\?news_seq=(\d+)'\">\s*<div class=\"title\">(.*?)</div>", page, re.S):
        out.append({'title': clean(title), 'link': f'https://www.gtn.co.kr/home/news/news_view.asp?news_seq={seq}',
                    'date': None, 'desc': ''})
    return out


def flags(title):
    f = [g for g, kws in MUST.items() if any(k.lower() in title.lower() for k in kws)]
    return f


def load_inbox():
    items = {}
    p = os.path.join(INBOX, 'items.jsonl')
    if os.path.exists(p):
        for line in open(p, encoding='utf-8'):
            if line.strip():
                x = json.loads(line)
                items[x['link']] = x
    return items


def collect():
    os.makedirs(INBOX, exist_ok=True)
    items = load_inbox()
    now = dt.datetime.now(KST)
    health, new = [], 0
    for name, url, kind, memo in SOURCES:
        try:
            body = fetch(url)
            got = parse_rss(body) if kind == 'rss' else parse_gtn(body)
            kept = 0
            for x in got:
                if not x['link'] or not x['title']:
                    continue
                if name in GENERAL and not any(k.lower() in x['title'].lower() for k in TRAVEL_KW):
                    continue
                kept += 1
                if x['link'] in items:
                    continue
                items[x['link']] = {
                    'source': name, 'title': x['title'], 'link': x['link'],
                    'date': x['date'].astimezone(KST).isoformat(timespec='minutes') if x['date'] else None,
                    'seen': now.isoformat(timespec='minutes'), 'desc': x['desc'], 'flags': flags(x['title']),
                    'drop_hint': [k for k in DROP_KW if k in x['title']],
                }
                new += 1
            dates = [x['date'] for x in got if x['date']]
            health.append({'source': name, 'url': url, 'ok': True, 'items': len(got), 'kept': kept,
                           'oldest': min(dates).astimezone(KST).isoformat(timespec='minutes') if dates else None})
        except Exception as e:
            health.append({'source': name, 'url': url, 'ok': False, 'error': f'{type(e).__name__}: {str(e)[:120]}'})
    with open(os.path.join(INBOX, 'items.jsonl'), 'w', encoding='utf-8') as f:
        for x in sorted(items.values(), key=lambda x: x.get('date') or x['seen']):
            f.write(json.dumps(x, ensure_ascii=False) + '\n')
    with open(os.path.join(INBOX, 'health.jsonl'), 'a', encoding='utf-8') as f:
        f.write(json.dumps({'at': now.isoformat(timespec='minutes'), 'new': new, 'sources': health}, ensure_ascii=False) + '\n')
    bad = [h for h in health if not h['ok']]
    print(f'수집 {now:%Y-%m-%d %H:%M} · 새 기사 {new}건 · 누적 {len(items)}건 · 실패 소스 {len(bad)}개')
    for h in bad:
        print('  실패:', h['source'], h['error'])
    return items, health


def fx():
    try:
        j = json.loads(fetch('https://open.er-api.com/v6/latest/USD'))
        return {'krw': j['rates']['KRW'], 'updated': j.get('time_last_update_utc'), 'src': 'https://open.er-api.com/v6/latest/USD'}
    except Exception as e:
        return {'error': f'{type(e).__name__}: {e}'}


def window(items, start, end, label):
    s = dt.datetime.fromisoformat(start).replace(tzinfo=KST)
    e = dt.datetime.fromisoformat(end).replace(tzinfo=KST)
    sel, undated = [], []
    for x in items.values():
        d = dt.datetime.fromisoformat(x['date']) if x.get('date') else None
        if d is None:
            seen = dt.datetime.fromisoformat(x['seen'])
            if s <= seen <= e + dt.timedelta(days=1):
                undated.append(x)
        elif s <= d < e:
            sel.append(x)
    sel.sort(key=lambda x: (x['source'], x['date']))
    out = os.path.join(ROOT, 'runs', label)
    os.makedirs(out, exist_ok=True)
    json.dump({'window': [start, end], 'items': sel, 'undated': undated}, open(os.path.join(out, 'candidates.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    f = fx()
    json.dump(f, open(os.path.join(out, 'fx.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    must = [x for x in sel + undated if x['flags']]
    lines = [f'# {label} 후보 기사', '', f'- 기간: {start} ~ {end} (KST)', f'- 후보 {len(sel)}건 + 날짜 없음 {len(undated)}건 (GTN 목록 등)',
             f'- 누락 금지 키워드 매칭 {len(must)}건 — 채택하지 않더라도 검토 기록을 남길 것',
             f"- 환율: {f.get('krw', '실패')} ({f.get('updated', f.get('error', ''))})", '']
    by = {}
    for x in sel:
        by.setdefault(x['source'], []).append(x)
    for src, xs in by.items():
        lines += [f'## {src} ({len(xs)})', '', '| 날짜 | 제목 | 플래그 |', '|---|---|---|']
        for x in xs:
            fl = ', '.join(x['flags']) + (' · 제외후보:' + ','.join(x['drop_hint']) if x['drop_hint'] else '')
            lines.append(f"| {x['date'][5:16].replace('T', ' ')} | [{x['title'].replace('|', '/')}]({x['link']}) | {fl} |")
        lines.append('')
    if undated:
        lines += ['## 날짜 없음 (발행일 확인 필요)', '', '| 출처 | 제목 | 플래그 |', '|---|---|---|']
        for x in undated:
            lines.append(f"| {x['source']} | [{x['title'].replace('|', '/')}]({x['link']}) | {', '.join(x['flags'])} |")
    open(os.path.join(out, 'candidates.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    cover = {}
    for x in sel:
        cover.setdefault(x['source'], []).append(x['date'])
    print(f'{label}: 후보 {len(sel)}건 · 날짜 없음 {len(undated)}건 · 필수 키워드 {len(must)}건 → runs/{label}/candidates.md')
    for src, ds in sorted(cover.items()):
        print(f'  {src}: {len(ds)}건 ({min(ds)[5:10]} ~ {max(ds)[5:10]})')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--window', nargs=2, metavar=('START', 'END'), help='KST, 예: 2026-11-09T10:00 2026-11-16T10:00')
    ap.add_argument('--label', help='예: 2026-W46')
    ap.add_argument('--no-fetch', action='store_true', help='새로 수집하지 않고 쌓인 기사만 사용')
    a = ap.parse_args()
    items = load_inbox() if a.no_fetch else collect()[0]
    if a.window:
        window(items, a.window[0], a.window[1], a.label or a.window[1][:10])
