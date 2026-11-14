"""주간 판본 JSON 하나를 data/brief-data.json 의 editions 끝에 추가(같은 key면 교체)한다.

사용: python -I scripts/add_edition.py runs/2026-W46/edition.json
- 'manual' 판본은 절대 바꾸지 않는다.
- 추가 영문명(tagenx/outenx)을 edition 파일 최상위에 "tagenx": {...}, "outenx": {...} 로 넣으면 데이터에 합친다.
- 합친 뒤 build.py --check 로 최신 판본을 검사한다.
"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
src = sys.argv[1]
E = json.load(open(src, encoding='utf-8'))
extra = {k: E.pop(k) for k in ('tagenx', 'outenx') if k in E}
if E.get('key') == 'manual':
    sys.exit("'manual' 판본은 바꿀 수 없습니다.")
dp = os.path.join(ROOT, 'data', 'brief-data.json')
D = json.load(open(dp, encoding='utf-8'))
for k, v in extra.items():
    D.setdefault(k, {}).update(v)
keys = [e['key'] for e in D['editions']]
if E['key'] in keys:
    D['editions'][keys.index(E['key'])] = E
    print('교체:', E['key'])
else:
    D['editions'].append(E)
    print('추가:', E['key'])
E.setdefault('issue', {})['count'] = len(E.get('items', []))
json.dump(D, open(dp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
r = subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'scripts', 'build.py'), '--check'])
sys.exit(r.returncode)
