"""Claude Agent SDK로 주간 판본을 작성한다 (GitHub Actions의 weekly.yml이 실행).

Max 요금제에 포함된 월 API 크레딧은 Claude Agent SDK에는 쓰이고 Claude Code에는 쓰이지 않는다.
그래서 claude-code-action 대신 이 스크립트를 쓴다.

사용: python3 -I scripts/write_edition.py --label 2026-W46 --start 2026-11-09T10:00 --end 2026-11-16T10:00
      python3 -I scripts/write_edition.py --smoke      # 크레딧으로 처리되는지 짧게 확인
필요: 환경 변수 ANTHROPIC_API_KEY. 선택: BRIEF_MODEL (기본 claude-opus-5-5), BRIEF_MAX_TURNS (기본 200)

공개 저장소의 Actions 로그는 누구나 볼 수 있으므로 대화 내용은 출력하지 않고 결과 요약만 남긴다.
"""
import argparse, asyncio, json, os, sys

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.environ.get('BRIEF_MODEL') or 'claude-opus-5-5'
MAX_TURNS = int(os.environ.get('BRIEF_MAX_TURNS') or 200)

TOOLS = ['Read', 'Write', 'Edit', 'Glob', 'Grep', 'WebSearch', 'WebFetch',
         'Bash(python3 -I scripts/collect.py:*)', 'Bash(python3 -I scripts/add_edition.py:*)',
         'Bash(python3 -I scripts/build.py:*)', 'Bash(python3 -I scripts/fuel_apply.py --card)', 'Bash(ls:*)', 'Bash(wc:*)', 'Bash(head:*)']


def prompt_for(label, start, end):
    return f"""저장소 루트의 CLAUDE.md 「주간 실행」 절차를 따라 이번 호를 작성하라.
- 기간: {start} ~ {end} (KST), 라벨: {label}
- 1~2단계(기간 계산, 후보 목록)는 이미 끝났다: runs/{label}/candidates.md, runs/{label}/fx.json, runs/{label}/ccsi.json
- 편집 기준은 .claude/skills/korea-weekly-travel-report/SKILL.md 의 2~4단계와 고정 표기를 따른다. 그 문서의 산출물·발행 절은 무시한다.
- runs/{label}/edition.json 을 쓰고, python3 -I scripts/add_edition.py runs/{label}/edition.json 으로 오류 0건까지 고친 뒤 python3 -I scripts/build.py 가 통과하는지 확인한다.
- 고객사별 보고서(CLAUDE.md 「고객사별 보고서」): 01–03이 아닌 기사에 cl 배치, 0건 고객사는 clientNotes 워치리스트. 시사점(so)은 쓰지 않는다.
- 지표 CCSI는 한국은행 원자료 기준: runs/{label}/ccsi.json 의 달이 직전 값보다 새 달이면 그 값·공표일·src(한은 보도자료 URL)로 갱신, 아니면 직전 값 유지. ccsi.json 이 실패면 WebSearch 보도 2곳 이상 일치할 때만 갱신. ECOS 호출 금지(CLAUDE.md 「주간 실행」 5단계 ind).
- runs/{label}/report.md 에 보고를 남긴다(고객사별 건수와 시사점 초안 포함).
- git 은 쓰지 않는다(워크플로가 커밋한다). 개인 메일 주소는 어디에도 쓰지 않는다. 작성자 표기는 EJ Park(meta의 ["작성","EJ Park"]).
- 끝나면 마지막 답으로 섹션별 채택 건수와 총 건수만 한 줄로 쓴다."""


async def run(prompt, max_turns, tools):
    opts = ClaudeAgentOptions(
        cwd=ROOT,
        model=MODEL,
        system_prompt={'type': 'preset', 'preset': 'claude_code'},
        setting_sources=['project'],
        allowed_tools=tools,
        permission_mode='dontAsk',
        max_turns=max_turns,
    )
    result = None
    async for m in query(prompt=prompt, options=opts):
        if isinstance(m, ResultMessage):
            result = m
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--label'); ap.add_argument('--start'); ap.add_argument('--end')
    ap.add_argument('--smoke', action='store_true')
    a = ap.parse_args()
    if a.smoke:
        r = asyncio.run(run('OK 라고만 답하라.', 1, []))
    else:
        if not (a.label and a.start and a.end):
            sys.exit('--label --start --end 가 필요합니다')
        r = asyncio.run(run(prompt_for(a.label, a.start, a.end), MAX_TURNS, TOOLS))
    if r is None:
        sys.exit('결과 메시지를 받지 못했습니다.')
    summary = {'model': MODEL, 'subtype': r.subtype, 'is_error': r.is_error, 'stop_reason': r.stop_reason,
               'num_turns': r.num_turns, 'total_cost_usd': r.total_cost_usd,
               'result': (r.result or '')[:500], 'errors': getattr(r, 'errors', None)}
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    if not a.smoke:
        json.dump(summary, open(os.path.join(ROOT, 'runs', a.label, 'agent-result.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
    if r.is_error:
        sys.exit(1)


if __name__ == '__main__':
    main()
