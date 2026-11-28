# 자동화 지침 — 주간 브리프 아티팩트 재발행

Orca 자동화 「주간 브리프 아티팩트 재발행」이 실행마다 이 파일을 읽고 따른다.
사람이 지켜보지 않는 실행이므로 **질문하지 말고** 끝까지 진행한다.

- 대상 아티팩트: https://claude.ai/artifact/AWgnMffftFo9pfrKJvuqbb (「한국 주간 트래블 브리프 V2」, 비공개)
- 작업 폴더: `C:\Users\elf94\바탕 화면\Workspace\projects\weekly-travel-brief-v2` (= GitHub 저장소 `weekly-travel-brief`)
- 사전 점검 `python -I scripts/artifact_state.py --check`가 `git pull` 후 마지막 발행 이후 `data/brief-data.json`·`src/template.html`·`scripts/build.py`가 바뀐 경우에만 이 실행을 시작한다. 바뀌는 경우: 월요일 weekly 작성, fuel-inbox 유류할증료 반영, 사람이 데이터·화면을 고쳐 push.

## 1. 바뀐 내용 확인
```
cd "C:\Users\elf94\바탕 화면\Workspace\projects\weekly-travel-brief-v2"
git pull --ff-only
python -I scripts/artifact_state.py --status
```
`--status`가 보여 주는 커밋들의 변경을 `git show --stat <커밋>`과 `git diff <마지막 발행 커밋> HEAD -- src/template.html scripts/build.py`로 확인한다. 새 판본이면 `runs/<라벨>/edition.json`의 제목·건수, 유류할증료면 `fuel-sources/<YYYY-MM>/report-*.md`를 훑어본다. 화면 코드(`src/template.html`)가 바뀌었으면 바뀐 부분을 읽고, 외부 주소로 데이터를 보내거나 개인 정보를 넣는 코드가 있으면 발행하지 말고 보고만 한다.

## 2. 빌드
```
python -I scripts/build.py
```
"오류 0건"과 "스크립트 문법 검사 통과"가 나와야 한다. `build.py`는 결과물에 메일 주소가 있으면 멈춘다. 실패하면 발행하지 말고 오류를 보고한다(데이터를 손으로 고치지 않는다).

## 3. 발행
1. Artifact 도구 `action: "read"`로 위 URL을 먼저 읽는다(다른 대화에서 만든 아티팩트라 읽어야 발행된다).
2. Artifact 도구로 `file_path`=`dist\index.html`, `url`=위 URL로 발행한다. `capabilities`는 넘기지 않는다(기존 선언 유지). `icon`도 넘기지 않는다. `label`은 `W48` 또는 `fuel 2026-12`처럼 이번 변경을 짧게.
3. 발행이 성공하면 `python -I scripts/artifact_state.py --mark`로 기록한다. 실패하면 기록하지 않는다(다음 실행에서 다시 시도된다).

## 4. 기록
- 워크스페이스 `PROJECTS.md`의 「한국 주간 트래블 브리프 V2」 줄 최종 업데이트 날짜를 오늘로.
- 워크스페이스 `ARTIFACTS.md`의 V2 아티팩트 최종 수정 날짜를 오늘로.
- 저장소 안의 파일(`README.md` 등)은 고치지 않는다 — 로컬에 수정이 남으면 다음 `git pull`이 막힐 수 있다. 발행 시각은 `.artifact-state.json`(저장소 제외)에 남는다.

## 5. 결과 보고 (마지막 메시지, 한국어, 짧게)
- 재발행 여부와 아티팩트 링크
- 이번에 반영된 것: 판본(라벨·건수) / 유류할증료(월) / 화면 수정
- 실패했다면 단계와 오류

## 하지 말 것
- `data/brief-data.json`을 직접 고치거나, 주간 작성·유류할증료 반영을 이 실행에서 하지 않는다(그건 GitHub Actions 몫).
- 다른 아티팩트(V1 `9qyt3S…` 등)를 고치거나 새 아티팩트를 만들지 않는다. `url` 없이 발행하지 않는다.
- GitHub Pages를 다시 켜지 않는다.
- `git push --force`, 히스토리 수정 금지.
