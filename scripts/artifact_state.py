"""아티팩트 재발행 필요 여부 확인·기록 (로컬 전용, Orca 자동화의 사전 점검용).

  python -I scripts/artifact_state.py --check   # git pull 후, 마지막 발행 이후 화면에 들어가는 파일이 바뀌었으면 0, 아니면 1
  python -I scripts/artifact_state.py --mark    # 지금 커밋을 '발행함'으로 기록
  python -I scripts/artifact_state.py --status  # 마지막 발행 커밋과 그 뒤 바뀐 커밋 목록

기록 파일: .artifact-state.json (저장소에 올리지 않음)
"""
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / ".artifact-state.json"
# 빌드 결과(dist/index.html)에 들어가는 파일
WATCH = ["data/brief-data.json", "src/template.html", "scripts/build.py"]
KST = timezone(timedelta(hours=9))


def git(*args):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} 실패: {r.stderr.strip()}")
    return r.stdout.strip()


def last_change():
    return git("log", "-1", "--format=%H", "--", *WATCH)


def load():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    mode = sys.argv[1] if len(sys.argv) > 1 else "--status"
    if mode == "--check":
        git("pull", "-q", "--ff-only")
        cur, prev = last_change(), load().get("commit")
        if cur and cur != prev:
            print(f"재발행 필요: {prev and prev[:7]} → {cur[:7]}")
            return 0
        print("변경 없음")
        return 1
    if mode == "--mark":
        cur = last_change()
        STATE.write_text(json.dumps({"commit": cur, "publishedAt": datetime.now(KST).isoformat(timespec="seconds")},
                                    ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"기록: {cur[:7]}")
        return 0
    st = load()
    prev = st.get("commit")
    print(f"마지막 발행: {prev and prev[:7]} ({st.get('publishedAt')})")
    if prev:
        print(git("log", "--oneline", f"{prev}..HEAD", "--", *WATCH) or "(이후 변경 없음)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
