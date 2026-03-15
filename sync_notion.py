#!/usr/bin/env python3
"""
GitHub → Notion 자동 동기화 스크립트
=====================================
GitHub 푸시 후 실행하면 Notion 프로젝트 페이지에
작업 기록(커밋 로그)을 자동으로 업데이트합니다.

사용법:
  python3 sync_notion.py                    # 최신 커밋 자동 감지
  python3 sync_notion.py "작업 내용 메모"   # 메모 직접 지정
"""

import subprocess, requests, json, sys, os
from datetime import datetime

# ── 설정 (환경변수로 관리, 코드에 토큰 하드코딩 금지)
NOTION_TOKEN    = os.environ.get("NOTION_TOKEN", "")
NOTION_LOG_PAGE = os.environ.get("NOTION_LOG_PAGE", "324e61bc-9ec3-8120-9ff0-de9bb1c42a12")  # 메인 프로젝트 페이지
GITHUB_REPO_URL = "https://github.com/videoschoolkorea/phd-demonetization-ai-creator"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def get_latest_commits(n: int = 5) -> list:
    """최근 n개 git 커밋 정보 가져오기"""
    try:
        result = subprocess.run(
            ["git", "log", f"-{n}", "--pretty=format:%H|%s|%an|%ai"],
            capture_output=True, text=True, cwd=os.path.dirname(__file__)
        )
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line: continue
            parts = line.split("|", 3)
            if len(parts) >= 4:
                commits.append({
                    "hash":    parts[0][:7],
                    "message": parts[1],
                    "author":  parts[2],
                    "date":    parts[3][:19],
                })
        return commits
    except Exception as e:
        return [{"hash": "?", "message": str(e), "author": "system", "date": datetime.now().isoformat()[:19]}]


def get_changed_files() -> list:
    """마지막 커밋에서 변경된 파일 목록"""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True, text=True, cwd=os.path.dirname(__file__)
        )
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except:
        return []


def append_commit_log_to_notion(commits: list, changed_files: list, memo: str = ""):
    """Notion 프로젝트 페이지에 커밋 로그 블록 추가"""
    if not NOTION_TOKEN:
        print("❌ NOTION_TOKEN 환경변수가 설정되지 않았습니다.")
        return False

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    latest = commits[0] if commits else {}
    commit_msg = latest.get("message", "")
    commit_hash = latest.get("hash", "")
    commit_date = latest.get("date", now)

    # 변경 파일 요약
    file_summary = ", ".join(changed_files[:5])
    if len(changed_files) > 5:
        file_summary += f" 외 {len(changed_files)-5}개"

    blocks = [
        # 구분선
        {"type": "divider", "divider": {}},
        # 커밋 헤더 callout
        {
            "type": "callout",
            "callout": {
                "rich_text": [
                    {"type": "text", "text": {"content": f"📦 GitHub 커밋 — {now}"},"annotations": {"bold": True}},
                ],
                "icon": {"type": "emoji", "emoji": "🔄"},
                "color": "blue_background",
            }
        },
        # 커밋 메시지
        {
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [
                {"type": "text", "text": {"content": "커밋: "}, "annotations": {"bold": True}},
                {"type": "text", "text": {
                    "content": f"[{commit_hash}] {commit_msg}",
                    "link": {"url": f"{GITHUB_REPO_URL}/commit/{latest.get('hash','')}"}
                }},
            ]}
        },
        # 날짜
        {
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [
                {"type": "text", "text": {"content": "날짜: "}, "annotations": {"bold": True}},
                {"type": "text", "text": {"content": commit_date}},
            ]}
        },
    ]

    # 변경 파일
    if changed_files:
        blocks.append({
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [
                {"type": "text", "text": {"content": "변경 파일: "}, "annotations": {"bold": True}},
                {"type": "text", "text": {"content": file_summary}},
            ]}
        })

    # 메모
    if memo:
        blocks.append({
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [
                {"type": "text", "text": {"content": "메모: "}, "annotations": {"bold": True}},
                {"type": "text", "text": {"content": memo}},
            ]}
        })

    # GitHub 링크
    blocks.append({
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [
            {"type": "text", "text": {"content": "저장소: "},"annotations": {"bold": True}},
            {"type": "text", "text": {
                "content": "GitHub에서 보기",
                "link": {"url": GITHUB_REPO_URL}
            }},
        ]}
    })

    # 최근 커밋 5개 목록
    if len(commits) > 1:
        blocks.append({
            "type": "heading_3",
            "heading_3": {"rich_text": [{"type": "text", "text": {"content": "최근 커밋 이력"}}]}
        })
        for c in commits:
            blocks.append({
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": [
                    {"type": "text", "text": {"content": f"[{c['hash']}] {c['date'][:10]} — {c['message'][:60]}"}},
                ]}
            })

    # Notion API 호출
    resp = requests.patch(
        f"https://api.notion.com/v1/blocks/{NOTION_LOG_PAGE}/children",
        headers=HEADERS,
        json={"children": blocks}
    )

    if resp.status_code == 200:
        print(f"✅ Notion 업데이트 완료: [{commit_hash}] {commit_msg}")
        return True
    else:
        print(f"❌ Notion 업데이트 실패: {resp.status_code} — {resp.text[:200]}")
        return False


def main():
    memo = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""

    print("🔄 GitHub → Notion 동기화 시작...")
    commits = get_latest_commits(5)
    changed = get_changed_files()

    print(f"  최신 커밋: [{commits[0]['hash']}] {commits[0]['message'][:60]}")
    print(f"  변경 파일: {len(changed)}개")
    if memo:
        print(f"  메모: {memo}")

    # 연구계획서 변경 감지 → 자동 버전 스냅샷 저장
    proposal_changed = any("연구계획서" in f for f in changed)
    if proposal_changed:
        _save_version_snapshot(commits[0])

    success = append_commit_log_to_notion(commits, changed, memo)
    if success:
        print("✅ 완료!")
    else:
        print("❌ 실패. NOTION_TOKEN 환경변수를 확인하세요.")


def _save_version_snapshot(commit: dict):
    """연구계획서 변경 감지 시 자동 버전 스냅샷 저장 + CHANGELOG 업데이트"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(script_dir, "연구계획서_김재환.html")
    versions_dir = os.path.join(script_dir, "versions")
    os.makedirs(versions_dir, exist_ok=True)

    # 기존 버전 번호 파악
    import glob, re
    existing = glob.glob(os.path.join(versions_dir, "연구계획서_v*.html"))
    versions = []
    for f in existing:
        m = re.search(r'v(\d+)\.(\d+)_', os.path.basename(f))
        if m:
            versions.append((int(m.group(1)), int(m.group(2))))

    # 다음 버전 번호
    if versions:
        latest_major, latest_minor = max(versions)
        next_ver = f"v{latest_major}.{latest_minor + 1}"
    else:
        next_ver = "v1.0"

    # 스냅샷 저장
    snap_name = f"연구계획서_{next_ver}_{commit['hash']}.html"
    snap_path = os.path.join(versions_dir, snap_name)
    if os.path.exists(src):
        import shutil
        shutil.copy2(src, snap_path)
        size = os.path.getsize(snap_path)
        print(f"  📸 버전 스냅샷 저장: {snap_name} ({size:,} bytes)")

        # CHANGELOG.md 자동 업데이트
        changelog_path = os.path.join(versions_dir, "CHANGELOG.md")
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_entry = f"""
---

## {next_ver} — {now} (커밋: {commit['hash']})
**변경 유형**: 업데이트

### 커밋 메시지
{commit['message']}

### 파일
- 스냅샷: `versions/{snap_name}` ({size:,} bytes)

"""
        if os.path.exists(changelog_path):
            with open(changelog_path, "r", encoding="utf-8") as f:
                content = f.read()
            # 첫 번째 ---  앞에 새 항목 삽입
            insert_pos = content.find("\n---\n")
            if insert_pos != -1:
                content = content[:insert_pos] + new_entry + content[insert_pos:]
            else:
                content = content + new_entry
            with open(changelog_path, "w", encoding="utf-8") as f:
                f.write(content)
        print(f"  📝 CHANGELOG.md 업데이트 완료")
    else:
        print(f"  ⚠ 연구계획서 파일 없음: {src}")


if __name__ == "__main__":
    main()
