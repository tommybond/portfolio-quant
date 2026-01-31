#!/bin/bash
# Show merge details

cd /Users/naisha/nashor-workspace/portfolio-quant

echo "════════════════════════════════════════════════════════════════"
echo "📊 MERGE DETAILS - Indian Stock Support Feature"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "🌿 Current Branch:"
git branch --show-current
echo ""

echo "📝 Recent Commits:"
git log -5 --pretty=format:"  %h - %s (%ar)" --abbrev-commit
echo ""
echo ""

echo "📦 Last Merge Commit:"
git log -1 --pretty=format:"  Commit: %H%n  Author: %an <%ae>%n  Date: %ad%n  Message: %s%n" --date=format:"%Y-%m-%d %H:%M:%S"
echo ""

echo "📊 Files Changed in Last Merge:"
git diff-tree --no-commit-id --name-status -r HEAD | head -20
echo ""

echo "📈 Statistics:"
git diff --shortstat HEAD~1 HEAD
echo ""

echo "🔍 Merge Commit Details:"
git show --stat --oneline HEAD | head -30
echo ""

echo "════════════════════════════════════════════════════════════════"
