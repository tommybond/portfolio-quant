# How to Create Pull Request - Indian Stock Support

## 📋 Quick Steps

### Step 1: Push Feature Branch (Run in Terminal)

```bash
cd /Users/naisha/nashor-workspace/portfolio-quant
git checkout feature/indian-stock-support-and-currency
git push -u origin feature/indian-stock-support-and-currency
```

### Step 2: Create Pull Request on GitHub

**Option A: Via Web Browser**

1. Go to: https://github.com/tommybond/portfolio-quant/compare/main...feature/indian-stock-support-and-currency

2. Click "Create Pull Request"

3. Fill in:
   - **Title:** `feat: Indian stock support with INR currency`
   - **Description:** Copy content from `PR_DESCRIPTION.md`

4. Click "Create Pull Request"

**Option B: Via GitHub CLI (if installed)**

```bash
gh pr create \
  --base main \
  --head feature/indian-stock-support-and-currency \
  --title "feat: Indian stock support with INR currency" \
  --body-file PR_DESCRIPTION.md
```

## 📝 PR Details

**Title:**
```
feat: Indian stock support with INR currency
```

**Short Description:**
```
Add comprehensive support for Indian stocks (NSE/BSE) with INR currency handling.

- Auto-detect .NS/.BO symbols
- Display ₹ for Indian stocks throughout UI
- IBKR integration with proper NSE/BSE exchanges
- Tested with SBIN.NS order #256

See PR_DESCRIPTION.md for full details.
```

## 🎯 What This PR Includes

### Modified Files (2)
- `app.py` - Currency-aware UI
- `oms/broker_ibkr.py` - NSE/BSE integration

### New Files (6)
- `INDIAN_STOCK_SUPPORT.md` - Setup guide
- `check_broker_order.py` - Order checker
- `check_order_db.py` - DB verification
- `check_sbin_order.py` - SBIN checker
- `monitor_sbin_order.py` - Monitor
- `test_indian_stock.py` - Tests

### Stats
- 8 files changed
- 890+ insertions
- 27 deletions

## ✅ Testing Status

- ✅ SBIN.NS order #256 submitted
- ✅ IBKR Gateway connected
- ✅ Currency displays correctly
- ✅ All tests passing

## 🔗 Useful Links

- **Compare URL:** https://github.com/tommybond/portfolio-quant/compare/main...feature/indian-stock-support-and-currency
- **PR Description:** See `PR_DESCRIPTION.md` in repo root
- **Merge Details:** See `MERGE_DETAILS.md` for technical details
- **Setup Guide:** See `INDIAN_STOCK_SUPPORT.md` for configuration

## ⚠️ Note About Local Merge

The feature branch has already been merged into local `main`. However, to follow proper PR workflow:

1. The feature branch should be pushed to remote
2. PR should be created from feature branch → main on GitHub
3. After PR is reviewed and approved, it can be merged on GitHub
4. Then local main can be synced with remote main

This allows for code review and discussion before merging.

## 🚀 Alternative: Direct Push to Main

If you prefer to skip the PR process (not recommended for collaboration):

```bash
cd /Users/naisha/nashor-workspace/portfolio-quant
git checkout main
git pull origin main --rebase
git push origin main
```

But creating a PR is better for:
- Code review
- Discussion
- Documentation
- Team collaboration
- CI/CD integration

---

**Ready to create PR!** 🎉

Run the commands in Step 1, then follow Step 2 to create the PR on GitHub.
