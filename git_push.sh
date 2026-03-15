#!/bin/bash
# ─────────────────────────────────────────────
# git_push.sh — GitHub 푸시 + Notion 자동 동기화
# 사용법: ./git_push.sh "커밋 메시지" ["노션 메모"]
# ─────────────────────────────────────────────

set -e

COMMIT_MSG="${1:-작업 업데이트}"
NOTION_MEMO="${2:-}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$HOME/.openclaw/workspace/.env.notion"

# 환경변수 로드
if [ -f "$ENV_FILE" ]; then
  export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

echo "📦 GitHub 푸시 시작: $COMMIT_MSG"

cd "$SCRIPT_DIR"
git add -A
git commit -m "$COMMIT_MSG" || { echo "변경사항 없음, 스킵"; }

# 토큰 포함 URL로 푸시
GITHUB_TOKEN=$(grep GITHUB_TOKEN "$ENV_FILE" 2>/dev/null | cut -d= -f2)
if [ -n "$GITHUB_TOKEN" ]; then
  git remote set-url origin "https://$GITHUB_TOKEN@github.com/videoschoolkorea/phd-demonetization-ai-creator.git"
fi

git push origin main
git remote set-url origin "https://github.com/videoschoolkorea/phd-demonetization-ai-creator.git"

echo "✅ GitHub 푸시 완료"

# Notion 동기화
echo "📝 Notion 동기화 중..."
python3 "$SCRIPT_DIR/sync_notion.py" "$NOTION_MEMO"

echo "🎉 모든 작업 완료!"
