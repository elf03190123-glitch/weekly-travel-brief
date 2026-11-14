# 한국 주간 트래블 브리프 V2 — 작업 규칙

이 폴더(= GitHub 저장소 `weekly-travel-brief`)에서 작업하는 Claude 세션은 이 문서를 따른다. 사람이 연 세션, Orca 세션, GitHub Actions 안의 Claude 모두 해당한다.

## 배포 (2026-11-15 사용자 결정)

- **배포: GitHub Pages** — 공개 저장소 `elf03190123-glitch/weekly-travel-brief`. 공개 범위는 사용자가 알고 정한 것이다.
- **수집: GitHub Actions** (`.github/workflows/collect.yml`, 6시간마다).
- **작성: GitHub Actions 안의 Claude** (`.github/workflows/weekly.yml`, 매주 월 10:00 KST). 저장소 Secret `CLAUDE_CODE_OAUTH_TOKEN`(Claude 구독 토큰, `claude setup-token`으로 발급) 또는 `ANTHROPIC_API_KEY`(선불 API 크레딧)가 있어야 돈다. 둘 다 있으면 구독 토큰을 쓴다. 모델은 저장소 변수 `BRIEF_MODEL`(없으면 `claude-sonnet-5-5`).
- **게재: GitHub Actions** (`.github/workflows/pages.yml`) — `data/`·`src/`가 바뀌어 push되거나 weekly 실행이 끝나면 `build.py`로 빌드해 Pages에 올린다.
- **아티팩트로 배포하지 않는다.** 미리보기로 만든 V2 아티팩트(https://claude.ai/artifact/AWgnMffftFo9pfrKJvuqbb)와 V1 아티팩트(9qyt3S…)는 건드리지 않는다. 기존 스킬의 「산출물」「5단계 · 발행」(아티팩트 재발행) 절은 V2에 적용하지 않는다.

## 개인 정보

- **업로더 개인 메일을 어디에도 넣지 않는다.** 작성자·문의처는 "AVIAREPS Korea"로 쓴다. 스킬이 고정 표기로 메일을 지정해도 이 규칙이 우선한다. `build.py`가 결과물에 개인 메일이 있으면 빌드를 멈춘다.
- 구독 신청 버튼은 `data/brief-data.json`의 `subscribeTo`(메일 주소)가 있을 때만 나온다. 지금은 비어 있어 숨겨져 있다. 개인 메일은 넣지 않는다.
- 커밋 작성자는 GitHub noreply 주소를 쓴다.

## 파일 구조

| 경로 | 내용 | 직접 수정 |
|---|---|---|
| `src/template.html` | 화면 코드(V1 + 관광청 필터 + 브라우저 다운로드). 데이터 자리는 `__BRIEF_DATA__` | 화면을 고칠 때만 |
| `data/brief-data.json` | 전체 데이터: `sections`·`std`·`roster`·`urls`·`bsp`·`fuelTab`·`fuelTabTrn`·`editions`, 추가 영문명 `tagenx`·`outenx`, `subscribeTo` | 스크립트로만 |
| `data/inbox/items.jsonl` | 수집 기사 누적(링크 기준 중복 제거) | 하지 않음 |
| `data/inbox/health.jsonl` | 수집 실행별 소스 상태 | 하지 않음 |
| `runs/<YYYY-Www>/` | 주차별 작업 폴더: `candidates.md/json`, `fx.json`, `edition.json`, `report.md` | 작업 중 |
| `dist/` | 빌드 결과(저장소에 올리지 않음) | 하지 않음 |
| `scripts/collect.py` | RSS 수집 + 기간 후보 목록 | |
| `scripts/add_edition.py` | 판본 JSON을 데이터에 추가하고 검사 | |
| `scripts/build.py` | 검사 + 개인 메일 검사 + `dist/index.html` 빌드 + 스크립트 문법 검사 | |
| `scripts/make_template.py` | V1 → V2 1회성 이관 도구. 로컬 전용 원본(`src/v1-live.html`, 저장소 제외)이 있어야 돈다. **다시 실행하지 않는다** | |
| `.claude/skills/korea-weekly-travel-report/SKILL.md` | 편집 기준(선별·작성 규칙) 사본. 개인 메일은 지운 판 | 기준이 바뀔 때 |

Python은 `python -I`(Actions에서는 `python3 -I`)로 실행한다.

## 수집이 0건으로 막혔던 이유와 V2 방식

- 10월 이후 claude.ai 클라우드 예약 실행에서 웹 가져오기 도구가 사전 승인되지 않은 RSS 주소를 막았다(`PROVENANCE_REQUIRED`). W42(10/13–19) 이후 발행이 멈춘 원인이다.
- V2는 `scripts/collect.py`가 RSS를 직접 받는다(LLM 도구를 쓰지 않음). 2026-11-14 이 PC와 GitHub Actions(미국 서버) 모두에서 15개 소스가 성공했다.
- 대부분의 RSS는 최근 1~4일치만 보여 준다(디스커버리뉴스·TTL뉴스·인사이트코리아·연합·뉴시스 약 하루, 이데일리 한 시간). 그래서 수집은 6시간마다, 작성은 매주 한다.
- W43–W46(10/19 이후) 공백은 소급하지 않고 건너뛴다(2026-11-15 결정).

## 주간 실행 (매주 월요일 10:00 KST · weekly.yml이 1~2단계를 미리 해 둔다)

1. **기간과 라벨**: 직전 월요일 10:00 ~ 이번 월요일 10:00(KST). 라벨은 기간 시작일의 ISO 주차(`2026-W46`), 판본 key는 `w46`.
2. **후보 목록**: `python3 -I scripts/collect.py --window <START> <END> --label <라벨>` → `runs/<라벨>/candidates.md`, `fx.json`.
3. **보강 발견**: 후보에 없는 것만 WebSearch로 찾는다. Section 10(아프리카·남미)은 스킬 「1단계 · C」, 기관·관광청 본사는 「1단계 · B」. 접근 실패는 실패로 기록하고 다른 경로를 반복해서 찾지 않는다. ECOS·bok.or.kr은 호출하지 않는다.
4. **선별·정독·작성**: 스킬 `korea-weekly-travel-report`의 「2단계 · 선별」「3단계 · 정독」「4단계 · 작성」「고정 표기」를 따른다(작성자 표기는 AVIAREPS Korea). `candidates.md`에서 누락 금지 플래그가 붙은 기사는 채택하지 않더라도 `runs/<라벨>/report.md`에 검토 사유를 남긴다.
5. **판본 JSON**: `runs/<라벨>/edition.json`. 형식은 직전 판본과 같다.
   - `key`, `label`, `sublabel`(예: `NOV 9–15`), `issue {no, range, count}`, `meta`(수록·수집·채택·제약·작성=AVIAREPS Korea), `ind`, `fuel`, `board`, `items`, `gap`, `foot`
   - `ind`: 환율은 `fx.json` 값, `ken`·`suben` 필수. CCSI는 새 발표가 없으면 직전 값 유지.
   - `fuel`: 새 유류할증료 자료가 없으면 직전 판본 값을 복사. `fuelTab`은 주간 실행에서 건드리지 않는다.
   - `board`: 6개 계정 모두. 수는 그 계정 `acc` 태그 기사 수.
   - 새 매체·태그는 최상위 `"outenx"`·`"tagenx"`에 영문명을 넣는다.
   - 시사점(So-What)은 쓰지 않는다.
6. **추가·검사**: `python3 -I scripts/add_edition.py runs/<라벨>/edition.json` — 오류 0건이 될 때까지 고친다.
7. **빌드 확인**: `python3 -I scripts/build.py`.
8. **보고**: `runs/<라벨>/report.md` — 지표 2개 값, 유류할증료 유지/갱신, 섹션별·계정별 건수, 소스별 수집 건수와 실패 소스, 누락 금지 키워드 검토 결과, 사람 확인 필요 항목.
9. **게시**: Actions에서는 Claude가 끝나면 워크플로가 `data/`·`runs/`를 커밋하고 Pages 배포를 부른다. 로컬 세션에서는 `git add data runs && git commit && git push`로 올리면 pages.yml이 배포한다.

### 수집이 거의 없을 때

후보가 30건 미만이면 판본을 만들지 말고 `runs/<라벨>/report.md`에 원인(수집 실행 날짜, 실패 소스)을 적고 끝낸다.

## 관광청 필터 (V2 화면)

- 상단 `관광청` 줄: 전체 · 하와이 · 뉴욕 · 샌프란시스코 · 라스베가스 · 스페인 · 타히티. 기준은 기사의 `acc` 태그. `장거리 공통 기사 포함`(기본 켬)이면 `장거리 전 계정` 태그 기사도 보인다.
- 필터를 고르면 본문·스코어보드·유류할증료 카드·워치리스트와 `문서 만들기`(뉴스레터 복사·PDF·Word·HTML)가 그 계정 기준으로 바뀌고, 제목이 「하와이 계정 주간 브리프」처럼 바뀐다.
- 계정별 링크: 주소 끝에 `#hawaii` `#new-york` `#san-francisco` `#las-vegas` `#spain` `#tahiti`.
- 계정 태그가 정확해야 계정별 보고서가 맞게 나온다.

## 아직 정하지 않은 것

- 유류할증료 월간 갱신: Pages에는 업로드 기능이 없다. 자료를 받으면 `data/brief-data.json`의 `fuelTab`을 스킬 「0-C단계」대로 고쳐 push한다(입력 방식은 미정).
- 구독 신청 받을 주소(`subscribeTo`).
