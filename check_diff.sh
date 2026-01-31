#!/bin/bash
cd /Users/naisha/nashor-workspace/portfolio-quant

echo "════════════════════════════════════════════════════════════════"
echo "📊 Workspace vs Remote Main - Diff Summary"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "🔄 Fetching latest from remote..."
git fetch origin 2>&1 | head -5
echo ""

echo "📍 Current branch:"
git branch --show-current
echo ""

echo "📝 Commits in local that are NOT in origin/main:"
git log origin/main..HEAD --oneline --graph
echo ""

echo "📊 File changes summary (local vs origin/main):"
git diff origin/main HEAD --stat | head -30
echo ""

echo "📁 Modified files:"
git diff origin/main HEAD --name-status | head -20
echo ""

echo "════════════════════════════════════════════════════════════════"
