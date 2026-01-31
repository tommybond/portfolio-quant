#!/bin/bash
# Create PR branch with Indian stock support changes

cd /Users/naisha/nashor-workspace/portfolio-quant

echo "🔍 Finding the Indian stock feature commit..."
echo ""

# Show recent commits
git log --oneline -10

echo ""
echo "---"
echo ""

# Find the specific commit (should be 32c6efe or similar)
FEATURE_COMMIT=$(git log --oneline --grep="Indian" --grep="currency" --grep="INR" -1 | cut -d' ' -f1)

if [ -z "$FEATURE_COMMIT" ]; then
    echo "❌ Could not find feature commit. Looking for recent commits with changes..."
    # Try to find by looking at commits with app.py changes
    FEATURE_COMMIT=$(git log --oneline --all -10 | grep -i "feat:" | head -1 | cut -d' ' -f1)
fi

echo "📍 Feature commit found: $FEATURE_COMMIT"
echo ""

# Check if branch already exists and delete it
git branch -D feature/indian-stock-pr 2>/dev/null

echo "🌿 Creating new branch from commit $FEATURE_COMMIT..."
git checkout -b feature/indian-stock-pr $FEATURE_COMMIT

if [ $? -eq 0 ]; then
    echo "✅ Branch created successfully"
    echo ""
    echo "📤 Pushing to GitHub..."
    git push -u origin feature/indian-stock-pr --force
    
    echo ""
    echo "✅ Done! Now visit:"
    echo "👉 https://github.com/tommybond/portfolio-quant/compare/main...feature/indian-stock-pr"
    echo ""
    echo "Then click 'Create pull request' and use the description from PR_DESCRIPTION.md"
else
    echo "❌ Failed to create branch"
fi
