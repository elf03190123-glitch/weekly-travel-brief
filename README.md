# 한국 주간 트래블 브리프 V2

6개 관광청 계정(하와이·뉴욕·샌프란시스코·라스베가스·스페인·타히티) 관점의 한국 아웃바운드 주간 브리프.
V1 기능(10개 섹션, 한·영 병기, 지표, 계정 스코어보드, 유류할증료 탭, 문서 만들기)을 유지하고 관광청별 필터와 계정별 보고서 내보내기를 더했다.

- **게재**: GitHub Pages — https://elf03190123-glitch.github.io/weekly-travel-brief/
- **저장소**: https://github.com/elf03190123-glitch/weekly-travel-brief (공개)
- **작업 규칙**: [CLAUDE.md](CLAUDE.md)

## 자동화

| 워크플로 | 일정 | 하는 일 |
|---|---|---|
| `collect` | 6시간마다 | RSS 15개 소스 수집 → `data/inbox/` 커밋 |
| `weekly` | 월 10:00 KST | 기간 후보 목록 → Claude가 선별·작성 → 커밋 → Pages 배포 (Secret `ANTHROPIC_API_KEY` 필요) |
| `pages` | 데이터·화면 변경 시 | 검사·빌드 후 Pages 배포 |

## 현재 상태 (2026-11-15)

- V2 화면 완성, V1 판본 10개(manual, W35–W42, 기사 267건) 이관. 개인 메일은 모두 "AVIAREPS Korea"로 바꿨다.
- 수집 0건 원인(클라우드 예약 실행의 RSS 주소 차단)을 확인했고, GitHub Actions(미국 서버)에서 15개 소스 수집이 되는 것을 시험으로 확인했다.
- W43–W46 공백은 건너뛴다. 첫 자동 발행은 W46(11/9–11/16)이다.

## 다음 할 일

- [ ] 저장소 Secret `ANTHROPIC_API_KEY` 입력 (입력 화면을 Chrome에 열어 둠)
- [ ] `weekly`를 수동 실행해 첫 호(W46) 확인
- [ ] 유류할증료 월간 갱신 방식 정하기(Pages에는 업로드 기능 없음)
- [ ] 구독 신청 받을 주소 정하기(`subscribeTo`, 개인 메일 제외)
- [ ] 시험용 저장소 `weekly-brief-collect-test` 정리
