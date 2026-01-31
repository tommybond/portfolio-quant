# Order Submission & NaN Issue Fixes

## Issues Fixed

### 1. Orders Not Appearing in IBKR ✅

**Problem:**
- Orders placed in UI were showing as submitted but not appearing in IBKR
- Orders were incorrectly being marked as REJECTED
- Root cause: IBKR's `'Inactive'` status was being mapped to `'REJECTED'`

**Solution:**
- Fixed status mapping: `'Inactive'` → `'PENDING'` (not `'REJECTED'`)
- Removed `'Inactive'` from rejection check (only `'Cancelled'` and `'ApiCancelled'` are rejections)
- Increased wait time after `placeOrder()` from 0.1s to 1.0s for status update
- Improved OMS status handling to treat `'PENDING'` as valid submission

**Files Modified:**
- [oms/broker_ibkr.py](oms/broker_ibkr.py) - Lines 305, 210-228
- [oms/oms.py](oms/oms.py) - Lines 103-119

### 2. NaN Price Values ✅

**Problem:**
- IBKR Paper Trading accounts return NaN for bid/ask/last prices
- NaN values were not being checked before conversion to float
- NaN values could propagate to UI and calculations

**Solution:**
- Added comprehensive NaN checking in `get_positions()` method
- Improved `get_current_price()` with helper function to validate prices
- Added fallback to yfinance when IBKR returns NaN
- Added NaN checking in UI price fetching code

**Files Modified:**
- [oms/broker_ibkr.py](oms/broker_ibkr.py) - Lines 337-357, 389-425
- [app.py](app.py) - Lines 2375-2387, 2485-2515, 7645-7690

## Changes Summary

### broker_ibkr.py

1. **Status Mapping (Line 305)**
   ```python
   'Inactive': 'PENDING',  # Was: 'REJECTED'
   ```

2. **Order Submission (Lines 210-228)**
   - Increased sleep time: `self.ib.sleep(1.0)` (was 0.1)
   - Removed 'Inactive' from rejection check
   - Only treats 'Cancelled' and 'ApiCancelled' as rejections

3. **Position Price Handling (Lines 337-357)**
   - Added NaN checking for `marketPrice()`
   - Falls back to `last`, `close` prices if market price is NaN
   - Properly cleans up market data subscriptions

4. **Price Fetching (Lines 389-425)**
   - Created `is_valid_price()` helper function
   - Checks for None, NaN, and negative values
   - More defensive price validation

### oms.py

1. **Status Checking (Lines 103-119)**
   - Normalized status to uppercase for consistent comparison
   - Treats 'PENDING' as successfully submitted
   - Only marks as REJECTED when status is explicitly 'REJECTED'

### app.py

1. **Price Fetching (Lines 7645-7690)**
   - Added NaN checks using `pd.notna()` and `np.isnan()`
   - Validates price before converting to float
   - Prevents NaN propagation to session state

2. **Position Summary (Lines 2375-2387)**
   - Added NaN validation when fetching position prices
   - Safe float conversion only for valid prices

3. **Position Detail (Lines 2485-2515)**
   - Comprehensive NaN checking for current price
   - Safe fallback to average price if current price is NaN

## Testing

### Test Order Submission
```bash
python test_order_fix.py
```

This test will:
1. Connect to IBKR (port 4002)
2. Submit a test order (AAPL BUY 1)
3. Verify order appears in IBKR
4. Cancel the test order

### Expected Results
- ✅ Order status should be 'SUBMITTED' or 'PENDING' (not 'REJECTED')
- ✅ Broker order ID should be assigned
- ✅ Order should appear in IBKR's trade list
- ✅ No NaN values in price data

## Common Issues Resolved

### Issue: Orders show as "SUBMITTED" but don't appear in TWS
**Fixed:** Orders now properly wait for IBKR to process and update status

### Issue: "Current Price: NaN" in UI
**Fixed:** All price fetching now validates for NaN before display

### Issue: Position prices showing as "$0.00"
**Fixed:** Fallback chain: market price → last → close → yfinance

### Issue: Order immediately rejected with "Inactive" status
**Fixed:** "Inactive" is now treated as pending, not rejected

## How It Works Now

### Order Flow
1. User clicks "EXECUTE BUY" in UI
2. OMS creates order and calls `broker.submit_order()`
3. IBKR places order (status initially 'Inactive')
4. System waits 1.0 seconds for status update
5. Status converts: 'Inactive' → 'PENDING' → marks as SUBMITTED
6. Order appears in IBKR with broker order ID

### Price Fetching Flow
1. Try IBKR market data (with NaN validation)
2. If NaN, try fallback prices (last, close)
3. If still NaN, return None (UI falls back to yfinance)
4. yfinance data also validated for NaN before use

## Notes

- **Paper Trading accounts** typically don't have real-time market data subscriptions
- yfinance provides reliable fallback (15-20 min delay)
- All NaN checks use both `pd.notna()` and `np.isnan()` for safety
- Market data subscriptions are properly cleaned up to avoid leaks

## Verification

After these fixes:
- ✅ Orders placed in UI → visible in IBKR TWS/Gateway
- ✅ No NaN values in price displays
- ✅ Positions show valid current prices
- ✅ Order status accurately reflects IBKR state
- ✅ Proper error messages when prices unavailable
