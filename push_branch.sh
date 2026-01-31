#!/bin/bash
# Push feature branch and show PR URL

cd /Users/naisha/nashor-workspace/portfolio-quant

echo "Current branch:"
git branch --show-current

echo ""
echo "Checking out feature branch..."
git checkout feature/indian-stock-support-and-currency 2>&1

echo ""
echo "Pushing to remote..."
git push -u origin feature/indian-stock-support-and-currency 2>&1

echo ""
echo "Done! Now visit:"
echo "https://github.com/tommybond/portfolio-quant/compare/main...feature/indian-stock-support-and-currency"
