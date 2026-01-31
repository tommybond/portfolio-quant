#!/bin/bash
# Complete the merge and push changes

echo "📝 Completing merge and push..."
echo ""

# Accept the merge commit message
git commit --no-edit 2>/dev/null || echo "Already committed"

# Push to remote
echo "📤 Pushing to remote..."
git push origin main

echo ""
echo "✅ Changes pushed to main branch!"
