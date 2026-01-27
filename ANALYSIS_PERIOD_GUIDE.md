# Analysis Period Guide: Optimal Settings for Trading Analysis

## Overview
Your system has **two main analysis periods** that affect different aspects of trading analysis:

1. **Equity Curve Analysis Period** (Dashboard Tab)
2. **Structure Analysis Period** (Trading Rules Tab)

---

## 1. Equity Curve Analysis Period

### **Location**: Dashboard Tab → Equity Curve Analysis

### **Current Settings**:
- **Range**: 30 to 365 days
- **Default**: 90 days
- **Purpose**: Analyzes equity curve, returns, drawdown, risk metrics

### **Recommendations by Use Case**:

| Period | Use Case | Best For |
|--------|----------|----------|
| **30-60 days** | Short-term analysis | Day trading, swing trading, recent performance |
| **90 days** (Default) ✅ | Balanced analysis | **Most users** - Good balance of recent vs historical |
| **180-252 days** | Medium-term analysis | Position trading, quarterly reviews |
| **365 days** | Long-term analysis | Annual reviews, trend analysis, institutional reporting |

### **Institutional Standard**: 
- **Daily Monitoring**: 30-60 days
- **Weekly Reviews**: 90-180 days
- **Monthly Reports**: 180-365 days
- **Quarterly Reviews**: 252-365 days (1 year)

### **Recommendation**: 
✅ **Keep 90 days as default** - Provides good balance between:
- Recent market conditions
- Statistical significance
- Performance trends

---

## 2. Structure Analysis Period (Rule 3)

### **Location**: Trading Rules Analysis Tab → Rule 3: Structure Analysis

### **Current Options**:
```python
30 days:  "Quick bases, swing trading, very active stocks"
60 days:  "Recommended default for most stocks" ✅ DEFAULT
90 days:  "Slower-moving stocks, longer consolidations"
120 days: "Very long-term structures, major bases"
180 days: "Very long-term structures, major bases"
```

### **How It Works**:
- Analyzes **support/resistance levels**
- Detects **consolidation patterns** (bases)
- Identifies **U-shape patterns**
- Calculates **volatility contraction**

### **Thresholds Adjust Automatically**:
- **≤60 days**: Range threshold = 15% (tight consolidation)
- **≤90 days**: Range threshold = 20% (medium consolidation)
- **>90 days**: Range threshold = 25% (wide consolidation)

---

## 📊 **Detailed Recommendations by Trading Style**

### **1. Day Trading / Scalping**
```yaml
Equity Analysis: 30-60 days
Structure Analysis: 30 days
```
**Why**: Focus on recent, short-term patterns and quick bases

### **2. Swing Trading** ✅ **RECOMMENDED**
```yaml
Equity Analysis: 90 days (default)
Structure Analysis: 60 days (default)
```
**Why**: Balanced view of recent performance and medium-term structures

### **3. Position Trading**
```yaml
Equity Analysis: 180-252 days
Structure Analysis: 90-120 days
```
**Why**: Longer-term trends and major base formations

### **4. Long-Term Investing**
```yaml
Equity Analysis: 365 days
Structure Analysis: 120-180 days
```
**Why**: Annual trends and major consolidation patterns

---

## 🎯 **Institutional-Grade Analysis Periods**

### **Multi-Timeframe Analysis** (Best Practice):

| Timeframe | Purpose | Period |
|-----------|---------|--------|
| **Short-term** | Daily monitoring | 30 days |
| **Medium-term** | Weekly reviews | 90 days |
| **Long-term** | Monthly reports | 180 days |
| **Strategic** | Quarterly/annual | 365 days |

### **Recommended Approach**:
✅ **Use multiple timeframes** for comprehensive analysis:
1. **Quick Check**: 30-day view for recent trends
2. **Standard Analysis**: 90-day view (default)
3. **Deep Dive**: 180-day view for major patterns

---

## ⚙️ **Current System Settings**

### **Equity Curve Analysis**:
- **Current**: 90 days (slider: 30-365)
- **Assessment**: ✅ **Good** - Standard institutional practice
- **Recommendation**: Keep as-is

### **Structure Analysis**:
- **Current**: 60 days (selectbox: 30/60/90/120/180)
- **Assessment**: ✅ **Good** - Recommended default
- **Recommendation**: Keep as-is

---

## 📈 **Best Practices**

### **1. Match Period to Strategy**:
- **Fast-moving stocks**: Use shorter periods (30-60 days)
- **Slow-moving stocks**: Use longer periods (90-180 days)
- **Volatile markets**: Use shorter periods to capture recent volatility
- **Stable markets**: Use longer periods for trend confirmation

### **2. Consider Market Regime**:
- **Bull markets**: Longer periods show uptrends better
- **Bear markets**: Shorter periods capture recent support levels
- **Sideways markets**: Medium periods (60-90 days) for range analysis

### **3. Combine Multiple Periods**:
- **Primary**: Use default (90 days equity, 60 days structure)
- **Confirmation**: Check shorter period (30 days) for recent changes
- **Context**: Check longer period (180 days) for major trends

---

## 🔍 **Real-World Examples**

### **Example 1: Active Swing Trader**
```
Equity Analysis: 60 days
Structure Analysis: 30 days
Reason: Focus on recent performance and quick bases
```

### **Example 2: Balanced Professional Trader** ✅
```
Equity Analysis: 90 days
Structure Analysis: 60 days
Reason: Standard institutional practice, good balance
```

### **Example 3: Position Trader**
```
Equity Analysis: 180 days
Structure Analysis: 90 days
Reason: Longer-term trends and major consolidations
```

### **Example 4: Institutional Fund Manager**
```
Equity Analysis: 365 days (annual)
Structure Analysis: 120 days (quarterly)
Reason: Strategic analysis and major base formations
```

---

## ✅ **Recommendations**

### **For Most Users** (Current Defaults):
```yaml
Equity Analysis Period: 90 days ✅
Structure Analysis Period: 60 days ✅
```
**Assessment**: ✅ **EXCELLENT** - Well-chosen defaults

### **For Conservative/Institutional**:
```yaml
Equity Analysis Period: 180 days
Structure Analysis Period: 90 days
```
**Why**: More conservative, longer-term view

### **For Aggressive/Day Trading**:
```yaml
Equity Analysis Period: 30-60 days
Structure Analysis Period: 30 days
```
**Why**: Focus on recent, short-term patterns

---

## 💡 **Key Insights**

1. **90 days equity analysis** is the **industry standard** for balanced analysis
2. **60 days structure analysis** is optimal for detecting **most base patterns**
3. **Shorter periods** = More sensitive to recent changes
4. **Longer periods** = More stable, less noise, but slower to react

---

## 🎯 **Bottom Line**

### **Are Current Analysis Periods Good Enough?**

**Equity Analysis (90 days)**: ✅ **YES**
- Standard institutional practice
- Good balance of recent vs historical
- Sufficient for statistical significance

**Structure Analysis (60 days)**: ✅ **YES**
- Recommended default
- Captures most base formations
- Good for swing/position trading

### **Recommendation**: 
✅ **Keep current defaults** - They align with institutional best practices and work well for most trading styles.

**Optional Enhancement**: Consider adding ability to analyze multiple timeframes simultaneously for comprehensive view.

---

*Last Updated: 2026-01-27*
