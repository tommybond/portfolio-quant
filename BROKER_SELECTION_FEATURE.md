# Broker Selection Feature

## Overview

Added broker selection capability to the dashboard, allowing users to choose between Alpaca and IBKR brokers.

---

## Features Added

### 1. Broker Selection UI
- **Location**: Sidebar → "🏦 Broker Selection"
- **Options**: 
  - Alpaca (default)
  - IBKR (if available)
- **Status Display**: Shows connection status for selected broker

### 2. Broker Helper Function
- **Function**: `get_broker_instance(broker_name=None)`
- **Purpose**: Returns broker instance based on selection
- **Location**: Top of `app.py` (after imports)

### 3. Updated Broker Usage
All broker instances now use the selected broker:
- ✅ Institutional Deployment tab
- ✅ Institutional Strategy tab
- ✅ Order submission
- ✅ Position loading
- ✅ Price fetching
- ✅ Account information

---

## How It Works

### Broker Selection Flow

1. **User selects broker** in sidebar dropdown
2. **Selection stored** in `st.session_state.selected_broker`
3. **All broker calls** use `get_broker_instance()` helper
4. **Broker-specific logic** handles differences between Alpaca and IBKR

### Broker Helper Function

```python
def get_broker_instance(broker_name: str = None):
    """
    Get broker instance based on selection
    
    Args:
        broker_name: Broker name ('Alpaca' or 'IBKR'). If None, uses session state.
    
    Returns:
        Broker instance or None if unavailable
    """
    if not INTEGRATIONS_AVAILABLE:
        return None
    
    # Get broker name from parameter or session state
    if broker_name is None:
        broker_name = st.session_state.get('selected_broker', 'Alpaca')
    
    try:
        if broker_name == 'Alpaca':
            return AlpacaBroker()
        elif broker_name == 'IBKR' and IBKR_AVAILABLE and IBKRBroker:
            return IBKRBroker()
        else:
            # Fallback to Alpaca if IBKR not available
            return AlpacaBroker()
    except Exception as e:
        # Return None if broker initialization fails
        print(f"Failed to initialize {broker_name} broker: {e}")
        return None
```

---

## UI Changes

### Sidebar Addition

```python
# Broker Selection
st.markdown("### 🏦 Broker Selection")
st.markdown("---")

# Broker selection dropdown
selected_broker = st.selectbox(
    "Select Broker",
    available_brokers,  # ['Alpaca', 'IBKR']
    ...
)

# Show broker status
# ✅ Connected / ⚠️ Not Connected / ❌ Unavailable
```

---

## Broker-Specific Handling

### Alpaca Broker
- Uses `broker_instance.api.list_positions()`
- Uses `broker_instance.api.get_account()`
- Uses `broker_instance.api.get_bars()` for price data

### IBKR Broker
- Uses `broker_instance.get_positions()`
- Uses `broker_instance.get_account_info()`
- Uses `broker_instance.ib.reqMktData()` for price data
- Requires TWS/IB Gateway to be running

---

## Updated Sections

### 1. Institutional Deployment Tab
- ✅ Broker selection respected
- ✅ Connection status shows selected broker
- ✅ Price fetching works for both brokers
- ✅ Order submission uses selected broker
- ✅ Position loading uses selected broker

### 2. Institutional Strategy Tab
- ✅ Position loading uses selected broker
- ✅ Price synchronization uses selected broker
- ✅ Broker-specific position format handling

### 3. Order Management
- ✅ All order submissions use selected broker
- ✅ Order status checking uses selected broker

---

## Configuration

### Environment Variables

**Alpaca:**
```bash
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

**IBKR:**
```bash
IBKR_HOST=127.0.0.1
IBKR_PORT=7497  # Paper Trading
IBKR_CLIENT_ID=1
```

---

## Usage

### Select Broker
1. Open sidebar
2. Find "🏦 Broker Selection" section
3. Choose broker from dropdown:
   - **Alpaca** - Cloud-based, no local software needed
   - **IBKR** - Requires TWS/IB Gateway running

### Check Status
- ✅ Green = Connected and ready
- ⚠️ Yellow = Not connected (check configuration)
- ❌ Red = Unavailable (module not installed)

### Use Selected Broker
- All trading operations automatically use selected broker
- No need to change code or restart app
- Selection persists across page refreshes

---

## Testing

### Test Alpaca
1. Select "Alpaca" in dropdown
2. Verify status shows "✅ Alpaca Connected"
3. Check positions load correctly
4. Submit a test order

### Test IBKR
1. Start TWS/IB Gateway
2. Enable API connections
3. Select "IBKR" in dropdown
4. Verify status shows "✅ IBKR Connected"
5. Check positions load correctly
6. Submit a test order

---

## Troubleshooting

### Issue: IBKR not showing in dropdown

**Solution:**
```bash
# Install ib_insync
pip install ib-insync

# Restart app
streamlit run app.py
```

### Issue: Broker status shows "Not Connected"

**Alpaca:**
- Check API keys in `.env`
- Verify keys are correct
- Check internet connection

**IBKR:**
- Ensure TWS/IB Gateway is running
- Check API connections enabled
- Verify port matches configuration (7497 for paper)

### Issue: Orders fail with selected broker

**Solution:**
- Check broker connection status
- Verify broker-specific requirements:
  - Alpaca: API keys configured
  - IBKR: TWS/Gateway running

---

## Code Changes Summary

### Files Modified:
1. **app.py**:
   - Added broker imports (IBKR)
   - Added `get_broker_instance()` helper function
   - Added broker selection UI in sidebar
   - Updated all broker instantiations to use helper
   - Updated position loading for both brokers
   - Updated price fetching for both brokers
   - Updated connection status display

### Key Functions:
- `get_broker_instance()` - Returns broker based on selection
- Broker-specific position format conversion
- Broker-specific price fetching logic

---

## Benefits

1. **Flexibility**: Switch between brokers without code changes
2. **User-Friendly**: Simple dropdown selection
3. **Status Visibility**: See connection status at a glance
4. **Unified Interface**: Same UI works with both brokers
5. **Extensible**: Easy to add more brokers in future

---

## Future Enhancements

- [ ] Add broker-specific settings panel
- [ ] Show broker-specific account details
- [ ] Add broker comparison metrics
- [ ] Support multiple brokers simultaneously
- [ ] Add broker-specific order types

---

**Status**: ✅ Complete and Ready to Use
