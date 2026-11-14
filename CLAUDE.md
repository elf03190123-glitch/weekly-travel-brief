# 한국 주간 트래블 브리프 V2 — 작업 규칙

이 폴더(= GitHub 저장소 `weekly-travel-brief`)에서 작업하는 Claude 세션은 이 문서를 따른다. 사람이 연 세션, Orca 세션, GitHub Actions 안의 Claude 모두 해당한다.

## 배포 (2026-11-15 사용자 결정)

- **배포: GitHub Pages** — 공개 저장소 `elf03190123-glitch/weekly-travel-brief`. 공개 범위는 사용자가 알고 정한 것이다.
- **수집: GitHub Actions** (`.github/workflows/collect.yml`, 6시간마다).
- **작성: GitHub Actions 안의 Claude Agent SDK** (`.github/workflows/weekly.yml` → `scripts/write_edition.py`, 매주 월 10:00 KST). 저장소 Secret `ANTHROPIC_API_KEY`를 쓴다. 이 키의 Console 조직에 Max 요금제 월 API 크레딧($100)이 연결돼 있다. 모델은 저장소 변수 `BRIEF_MODEL`(없으면 `claude-opus-5-5`).
  - **claude-code-action(=Claude Code)을 쓰지 않는다.** Max 요금제 API 크레딧은 Claude Code에는 적용되지 않아 "Credit balance is too low"로 실패한다(2026-11-15 확인). Agent SDK는 크레딧 대상이다(같은 날 시험 실행 성공).
  - 크레딧이 바닥나면 다음 결제 주기까지 API가 멈춘다. 월 사용액은 `runs/<라벨>/agent-result.json`의 `total_cost_usd`(추정치)로 본다.
  - 수동 실행: Actions → weekly → Run workflow. `smoke`를 켜면 짧은 확인만 한다.
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
| `scripts/write_edition.py` | Actions에서 Agent SDK로 주간 실행 3~8단계를 맡기는 스크립트(대화 내용은 로그에 남기지 않음) | |
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
   - **고객사 배치 `cl`** (아래 「고객사별 보고서」): 01–03(s1·s4·s2)이 아닌 기사마다, 관련 고객사와 칸을 `"cl":[{"c":"hawaii","s":"B"}, …]`로 넣는다. 한 기사가 여러 고객사에 들어갈 수 있다. 관련 고객사가 없으면 `cl`을 빼고 내부 전체판에만 둔다.
   - **고객사 메모 `clientNotes`**: 이번 호에 기사가 0건인 고객사는 `"clientNotes":{"<id>":{"watch":[["<영문 대문자 키>","<상시 모니터링 대상 — 이번 호 신규 없음>"]]}}`를 넣는다. `so`(시사점)는 **쓰지 않는다** — 사람이 확정한다. 시사점 초안은 report.md에만 쓴다.
   - 시사점(So-What)은 쓰지 않는다.
6. **추가·검사**: `python3 -I scripts/add_edition.py runs/<라벨>/edition.json` — 오류 0건이 될 때까지 고친다.
7. **빌드 확인**: `python3 -I scripts/build.py`.
8. **보고**: `runs/<라벨>/report.md` — 지표 2개 값, 유류할증료 유지/갱신, 섹션별·계정별 건수, 소스별 수집 건수와 실패 소스, 누락 금지 키워드 검토 결과, 사람 확인 필요 항목.
9. **게시**: Actions에서는 Claude가 끝나면 워크플로가 `data/`·`runs/`를 커밋하고 Pages 배포를 부른다. 로컬 세션에서는 `git add data runs && git commit && git push`로 올리면 pages.yml이 배포한다.

### 섹션 분류 결정 기록

- **2026-11-15 (EJ 지시)**: Section 06 이름을 「OTA · 플랫폼 · 여행사 동향」(OTA, Platform & Travel Agency Watch)으로 바꿨다. **BSP 발권 상위 여행사(스킬의 BSP 명단)의 동향은 Section 06에 싣는다** — 예약 추이·실적·전략·채널·제휴. 소비자 심리(02)나 여행업계(05)에 넣지 않는다. 패키지 상품 기획·럭셔리 출시는 계속 Section 07. Section 05에는 유통구조·KATA 제도·명단 밖 업계 일반 건이 남는다. 첫 적용: W46 교원투어 4분기 중국 예약 기사를 02 → 06(PL-03)으로 옮김.

### 수집이 거의 없을 때

후보가 30건 미만이면 판본을 만들지 말고 `runs/<라벨>/report.md`에 원인(수집 실행 날짜, 실패 소스)을 적고 끝낸다.

## 고객사별 보고서 (2026-11-15 EJ 결정)

고객사 14곳 — 목록과 역할은 워크스페이스 `_shared/clients.md`, 화면·작성용 정의는 `data/brief-data.json`의 `clients`(id·이름·유형·목적지 `dest`·브랜드 `kw`·경쟁 목록 `comp`).

- **구조**: 공통 01 정치·경제 · 02 소비자 심리 · 03 아웃바운드 동향(모든 고객사 같은 내용) + 고객사별 A–F.
- **고객사 칸** (`clientSlots`):
  - **A 목적지 수요** — 그 고객사 목적지(`dest`)의 검색·예약·출국 데이터, 목적지 수요 기사
  - **B 항공·접근성** — 그 목적지 노선·좌석·운임·항공사 제휴. 항공 고객사(Airlink·Azul)는 자사·연결 항공 동향
  - **C 판매 채널** — 여행사·OTA·홈쇼핑 상품과 판매, 기업 출장·MICE, BSP·GDS(항공 GSA 고객사)
  - **D 경쟁 동향** — 고객사의 `comp` 목록(경쟁 목적지·호텔·항공사)에 해당하는 기사
  - **E 고객사 소식** — 고객사 본사·브랜드·현지 파트너 발표, 고객사 목적지 홍보 콘텐츠
  - **F 시사점·액션** — 사람이 `clientNotes.<id>.so`에 확정. Claude는 쓰지 않는다
- **찾는 범위**: `candidates.md`의 `고객사` 플래그 기사, 그리고 매주 WebSearch로 고객사 브랜드 소식(예: Regal Hotels Hong Kong, Ascott Vietnam/Indonesia(Somerset·Citadines·Oakwood·lyf), Renaissance Honolulu, Halekulani Okinawa, Mandarin Oriental 신규 오픈·한국 활동, Airlink, Azul)을 확인한다. 고객사마다 1건 이상이 목표지만, 억지로 채우지 않고 0건이면 `clientNotes` 워치리스트를 남긴다.
- **겹치는 고객사**: 하와이 = 하와이관광청 + 르네상스 호놀룰루. 오키나와 = 할레쿨라니 오키나와의 목적지이면서 하와이의 경쟁 목적지. 같은 기사를 각 고객사 칸에 따로 배치하고, 다른 고객사를 낮추는 표현은 쓰지 않는다.
- **건수**: 공통 01–03은 기존 기준. 전체 기사 수는 30건 안팎(최대 36건)까지 허용한다.

## 화면 (V2)

- 상단 `고객사` 줄: 전체(내부용) · 관광청 6 · 호텔 6 · 항공 2. 고객사를 고르면 공통 01–03 + 그 고객사 A–F 보고서가 되고, 유류할증료 카드·워치리스트·`문서 만들기`(뉴스레터 복사·PDF·Word·HTML)도 그 형태로 나간다.
- 링크: 주소 끝에 고객사 id — `#hawaii` `#new-york` `#san-francisco` `#las-vegas` `#spain` `#tahiti` `#regal-hk` `#ascott-vietnam` `#ascott-indonesia` `#renaissance-honolulu` `#halekulani-okinawa` `#mandarin-oriental` `#airlink` `#azul`.
- `cl`이 없는 예전 판본(W35–W42)은 관광청 `acc` 태그와 섹션으로 칸을 추정해 보여 준다(호텔 고객사는 비어 있다).
- 전체(내부용)는 기존 10개 섹션 그대로다.

## 아직 정하지 않은 것

- 유류할증료 월간 갱신: Pages에는 업로드 기능이 없다. 자료를 받으면 `data/brief-data.json`의 `fuelTab`을 스킬 「0-C단계」대로 고쳐 push한다(입력 방식은 미정).
- 구독 신청 받을 주소(`subscribeTo`).
