#!/bin/bash
# Push feature branch and provide PR creation instructions

cd /Users/naisha/nashor-workspace/portfolio-quant

echo "════════════════════════════════════════════════════════════════"
echo "📝 Creating Pull Request for Indian Stock Support"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "📍 Current branch: $CURRENT_BRANCH"
echo ""

# Switch to feature branch if not already there
if [ "$CURRENT_BRANCH" != "feature/indian-stock-support-and-currency" ]; then
    echo "🔄 Switching to feature branch..."
    git checkout feature/indian-stock-support-and-currency
    if [ $? -ne 0 ]; then
        echo "❌ Failed to checkout feature branch"
        exit 1
    fi
    echo "✅ Switched to feature/indian-stock-support-and-currency"
    echo ""
fi

# Push feature branch
echo "📤 Pushing feature branch to remote..."
git push -u origin feature/indian-stock-support-and-currency

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Feature branch pushed successfully!"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "🎯 CREATE PULL REQUEST"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "Option 1: GitHub Web Interface"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Visit this URL:"
    echo "👉 https://github.com/tommybond/portfolio-quant/compare/main...feature/indian-stock-support-and-currency"
    echo ""
    echo "Then:"
    echo "  1. Click 'Create Pull Request'"
    echo "  2. Title: 'feat: Indian stock support with INR currency'"
    echo "  3. Copy description from: PR_DESCRIPTION.md"
    echo "  4. Click 'Create Pull Request' button"
    echo ""
    echo "Option 2: GitHub CLI (if installed)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "gh pr create \\"
    echo "  --base main \\"
    echo "  --head feature/indian-stock-support-and-currency \\"
    echo "  --title 'feat: Indian stock support with INR currency' \\"
    echo "  --body-file PR_DESCRIPTION.md"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
else
    echo ""
    echo "❌ Failed to push feature branch"
    echo ""
    echo "This might be because:"
    echo "  1. Remote already has this branch"
    echo "  2. Authentication required"
    echo "  3. Network issues"
    echo ""
    echo "Try manually:"
    echo "  git push -u origin feature/indian-stock-support-and-currency --force"
    exit 1
fi
