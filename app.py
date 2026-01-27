import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import yaml
from datetime import datetime, timedelta
import os

# Set matplotlib backend before importing pyplot to avoid segfault
import matplotlib
matplotlib.use('Agg')

from core.risk import RiskManager
from core.approval import TradeApproval
from monitoring.audit import log_event
from monitoring.reconciliation import reconcile

# Page configuration
st.set_page_config(
    page_title="Portfolio Quant Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Portfolio Quant Trading System - Institutional-grade trading platform"
    }
)

# Custom CSS for modern UI/UX design
st.markdown("""
<style>
    /* Global Styles - Light Institutional Theme */
    .main {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background-color: #f0f9ff;
    }
    
    /* Page background - Light blue */
    .stApp {
        background-color: #f0f9ff;
        background-image: linear-gradient(to bottom, #f0f9ff 0%, #e0f2fe 100%);
    }
    
    /* Main container background */
    .block-container {
        background-color: transparent;
    }
    
    /* Remove all black colors */
    * {
        border-color: #cbd5e1 !important;
    }
    
    /* Ensure all text is visible */
    * {
        color: inherit;
    }
    
    /* Header Styling - Light Institutional Colors */
    h1 {
        color: #0c4a6e !important;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        border-bottom: 3px solid #60a5fa;
        padding-bottom: 0.5rem;
    }
    
    h2 {
        color: #075985 !important;
        font-weight: 600;
        font-size: 1.75rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    h3 {
        color: #0369a1 !important;
        font-weight: 600;
        font-size: 1.25rem;
        margin-top: 1.5rem;
    }
    
    h4 {
        color: #075985 !important;
        font-weight: 600;
    }
    
    /* Ensure Streamlit text is visible - Light colors */
    .stMarkdown {
        color: #0c4a6e;
    }
    
    p {
        color: #075985 !important;
    }
    
    strong {
        color: #0369a1 !important;
    }
    
    /* Tab content visibility */
    .element-container {
        color: #075985;
    }
    
    /* Card-based Design */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.15);
        color: white;
        margin-bottom: 1rem;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background-color: #dbeafe;
        border-right: 2px solid #93c5fd;
    }
    
    [data-testid="stSidebar"] {
        background-color: #dbeafe !important;
    }
    
    /* Sidebar Text Visibility - Light Colors */
    [data-testid="stSidebar"] {
        color: #075985;
    }
    
    [data-testid="stSidebar"] h1 {
        color: #075985 !important;
        font-weight: 700;
    }
    
    [data-testid="stSidebar"] h2 {
        color: #075985 !important;
        font-weight: 600;
    }
    
    [data-testid="stSidebar"] h3 {
        color: #075985 !important;
        font-weight: 600;
    }
    
    [data-testid="stSidebar"] p {
        color: #075985 !important;
    }
    
    [data-testid="stSidebar"] label {
        color: #075985 !important;
        font-weight: 500;
    }
    
    [data-testid="stSidebar"] .stSelectbox label {
        color: #075985 !important;
        font-weight: 600;
        font-size: 0.95rem;
    }
    
    [data-testid="stSidebar"] .stSlider label {
        color: #075985 !important;
        font-weight: 600;
        font-size: 0.95rem;
    }
    
    [data-testid="stSidebar"] .stCheckbox label {
        color: #075985 !important;
        font-weight: 500;
        font-size: 0.95rem;
    }
    
    [data-testid="stSidebar"] .stTextInput label {
        color: #075985 !important;
        font-weight: 600;
    }
    
    [data-testid="stSidebar"] .stTextArea label {
        color: #075985 !important;
        font-weight: 600;
    }
    
    
    /* Input labels visibility - Light Colors */
    .stTextInput label,
    .stSelectbox label,
    .stSlider label,
    .stNumberInput label {
        color: #075985 !important;
        font-weight: 600;
        font-size: 0.95rem;
    }
    
    /* Slider value visibility */
    .stSlider [data-testid="stMarkdownContainer"] {
        color: #075985 !important;
    }
    
    /* Number input styling */
    .stNumberInput > div > div > input {
        background-color: #ffffff !important;
        color: #075985 !important;
        border-color: #93c5fd !important;
    }
    
    /* Textarea styling */
    textarea {
        background-color: #ffffff !important;
        color: #075985 !important;
        border-color: #93c5fd !important;
    }
    
    /* Button Styling - Light Blue Theme */
    .stButton > button {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    }
    
    /* Metric Cards - Light Colors */
    [data-testid="stMetricValue"] {
        font-size: 1.75rem;
        font-weight: 700;
        color: #075985;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        font-weight: 500;
        color: #0369a1;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Tabs Styling - Enhanced Visibility */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #bfdbfe;
        padding: 0.5rem;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        background-color: #ffffff;
        border: 1px solid #93c5fd;
    }
    
    /* Inactive tabs - Light blue text on white background */
    .stTabs [aria-selected="false"] {
        background-color: #ffffff !important;
        color: #075985 !important;
        border: 1px solid #93c5fd !important;
    }
    
    .stTabs [aria-selected="false"]:hover {
        background-color: #dbeafe !important;
        border-color: #60a5fa !important;
        color: #0369a1 !important;
    }
    
    /* Active tab - White text on light blue gradient */
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%) !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
    }
    
    /* Force ALL tab text to be visible */
    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] div,
    .stTabs [data-baseweb="tab"] span,
    .stTabs [data-baseweb="tab"] * {
        color: inherit !important;
        font-weight: 600 !important;
    }
    
    /* Inactive tab text - light blue */
    .stTabs [aria-selected="false"] p,
    .stTabs [aria-selected="false"] div,
    .stTabs [aria-selected="false"] span,
    .stTabs [aria-selected="false"] * {
        color: #075985 !important;
    }
    
    /* Active tab text - white */
    .stTabs [aria-selected="true"] p,
    .stTabs [aria-selected="true"] div,
    .stTabs [aria-selected="true"] span,
    .stTabs [aria-selected="true"] * {
        color: #ffffff !important;
    }
    
    /* Input Fields - Light Institutional Theme */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #93c5fd;
        padding: 0.75rem;
        transition: all 0.3s ease;
        background-color: #ffffff !important;
        color: #075985 !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #60a5fa;
        box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2);
        background-color: #ffffff !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #94a3b8 !important;
    }
    
    /* Remove black from all inputs */
    input, textarea, select {
        background-color: #ffffff !important;
        color: #075985 !important;
        border-color: #93c5fd !important;
    }
    
    /* Selectbox Styling - Light Theme */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 2px solid #93c5fd;
        background-color: #ffffff !important;
        color: #075985 !important;
    }
    
    .stSelectbox > div > div:hover {
        border-color: #60a5fa;
    }
    
    /* Slider Styling */
    .stSlider {
        margin: 1rem 0;
    }
    
    /* Success/Error Messages */
    .stSuccess {
        background-color: #d1fae5;
        border-left: 4px solid #10b981;
        border-radius: 6px;
        padding: 1rem;
    }
    
    .stError {
        background-color: #fee2e2;
        border-left: 4px solid #ef4444;
        border-radius: 6px;
        padding: 1rem;
    }
    
    .stWarning {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
        border-radius: 6px;
        padding: 1rem;
    }
    
    .stInfo {
        background-color: #dbeafe;
        border-left: 4px solid #3b82f6;
        border-radius: 6px;
        padding: 1rem;
    }
    
    /* Divider */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 2px solid #e2e8f0;
    }
    
    /* Code Blocks */
    .stCodeBlock {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    
    /* Text Area */
    textarea {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
    }
    
    /* Custom Container Styles */
    .custom-container {
        background: #ffffff;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
        margin-bottom: 2rem;
    }
    
    /* Light blue background for content areas */
    .element-container {
        background-color: transparent;
    }
    
    /* Ensure cards stand out on light blue background */
    [data-testid="stMetricContainer"] {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 0.5rem;
    }
    
    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.875rem;
    }
    
    .status-active {
        background-color: #fee2e2;
        color: #991b1b;
    }
    
    .status-inactive {
        background-color: #d1fae5;
        color: #065f46;
    }
    
    /* Chart Container */
    .chart-container {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
        margin: 1rem 0;
    }
    
    /* Footer */
    footer {
        visibility: hidden;
    }
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)

# Load configuration
@st.cache_data
def load_config():
    try:
        with open("config/settings.yaml", "r") as f:
            return yaml.safe_load(f)
    except:
        return {
            "market": "US",
            "kill_switch": False,
            "approval_mode": "SEMI",
            "max_daily_dd": 0.03,
            "max_total_dd": 0.12
        }

def save_config(config):
    with open("config/settings.yaml", "w") as f:
        yaml.dump(config, f)
    # Clear the cache so config reloads on next access
    if hasattr(load_config, 'clear'):
        load_config.clear()

# Initialize session state
if "risk_manager" not in st.session_state:
    try:
        config = load_config()
        st.session_state.risk_manager = RiskManager(
            max_daily_dd=config.get("max_daily_dd", 0.03),
            max_total_dd=config.get("max_total_dd", 0.12)
        )
        st.session_state.approval = TradeApproval(mode=config.get("approval_mode", "SEMI"))
        st.session_state.config = config
        st.session_state.pending_trades = []
        st.session_state.equity_history = []
        st.session_state.equity_data = None
    except Exception as e:
        st.error(f"Error initializing system: {str(e)}")
        st.stop()

# Sidebar - Enhanced UI
with st.sidebar:
    # Logo/Brand Section - Light Colors
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem 0; border-bottom: 2px solid #93c5fd; margin-bottom: 2rem;">
        <h1 style="font-size: 1.75rem; margin: 0; color: #075985; font-weight: 700;">📈 Portfolio Quant</h1>
        <p style="color: #0369a1; font-size: 0.875rem; margin: 0.5rem 0 0 0; font-weight: 500;">Trading System</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### ⚙️ System Configuration")
    st.markdown("---")
    
    config = st.session_state.config.copy()
    
    # Approval Mode Card - Light Colors
    st.markdown("""
    <div style="color: #075985; font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem;">
        Approval Mode
    </div>
    """, unsafe_allow_html=True)
    approval_mode = st.selectbox(
        "Select approval mode",
        ["AUTO", "SEMI"],
        index=0 if config.get("approval_mode") == "AUTO" else 1,
        label_visibility="collapsed"
    )
    config["approval_mode"] = approval_mode
    
    # Risk Parameters Card - Light Colors
    st.markdown("""
    <div style="color: #075985; font-weight: 600; font-size: 0.95rem; margin-top: 1.5rem; margin-bottom: 0.5rem;">
        Risk Parameters
    </div>
    """, unsafe_allow_html=True)
    
    max_daily_dd = st.slider(
        "Max Daily Drawdown",
        0.01, 0.10, float(config.get("max_daily_dd", 0.03)),
        step=0.01,
        format="%.2f",
        help="Maximum allowed daily drawdown percentage"
    )
    config["max_daily_dd"] = max_daily_dd
    
    max_total_dd = st.slider(
        "Max Total Drawdown",
        0.05, 0.30, float(config.get("max_total_dd", 0.12)),
        step=0.01,
        format="%.2f",
        help="Maximum allowed total drawdown percentage"
    )
    config["max_total_dd"] = max_total_dd
    
    # Kill Switch Card - Light Colors
    st.markdown("""
    <div style="color: #075985; font-weight: 600; font-size: 0.95rem; margin-top: 1.5rem; margin-bottom: 0.5rem;">
        System Controls
    </div>
    """, unsafe_allow_html=True)
    kill_switch = st.checkbox(
        "🛑 Kill Switch Active",
        value=config.get("kill_switch", False),
        help="Emergency stop for all trading activities"
    )
    config["kill_switch"] = kill_switch
    
    # Save Button
    col_save1, col_save2 = st.columns([1, 1])
    with col_save1:
        if st.button("💾 Save", use_container_width=True):
            save_config(config)
            st.session_state.risk_manager = RiskManager(
                max_daily_dd=max_daily_dd,
                max_total_dd=max_total_dd
            )
            st.session_state.approval = TradeApproval(mode=approval_mode)
            st.session_state.config = config
            st.success("✅ Configuration saved!")
    
    st.markdown("---")
    
    # System Status
    st.markdown("### 📊 System Status")
    kill_status = st.session_state.config.get("kill_switch", False)
    if kill_status:
        st.error("🔴 **Kill Switch ACTIVE**")
    else:
        st.success("🟢 **System OPERATIONAL**")
    
    st.markdown("---")
    
    # Audit log viewer
    st.markdown("### 📋 Audit Log")
    if os.path.exists("audit.log"):
        with open("audit.log", "r") as f:
            log_lines = f.readlines()
            if log_lines:
                st.text_area(
                    "Recent Activity",
                    "".join(log_lines[-15:]),
                    height=180,
                    disabled=True,
                    label_visibility="collapsed"
                )
            else:
                st.info("No log entries yet")
    else:
        st.info("No log file found")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; color: #94a3b8; font-size: 0.75rem;">
        <p>Version 1.0.0</p>
        <p>© 2026 Portfolio Quant</p>
    </div>
    """, unsafe_allow_html=True)

# Main content - Enhanced Header - Light Blue Theme
st.markdown("""
<div style="background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%); padding: 2rem; border-radius: 12px; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(59, 130, 246, 0.2);">
    <h1 style="color: white; margin: 0; font-size: 2.5rem; font-weight: 700;">📈 Portfolio Quant Trading System</h1>
    <p style="color: rgba(255, 255, 255, 0.95); margin: 0.5rem 0 0 0; font-size: 1.1rem;">Institutional-grade trading platform with advanced risk management and analytics</p>
</div>
""", unsafe_allow_html=True)

# Tabs with enhanced styling - ensure all text is visible
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard", 
    "💰 Trade Management", 
    "⚠️ Risk Monitor", 
    "🔄 Reconciliation", 
    "📋 Trading Rules"
])

with tab1:
    # System Overview Section
    st.markdown("## 📊 System Overview")
    st.markdown("---")
    
    # Key Metrics Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        approval_mode_val = st.session_state.config.get("approval_mode", "SEMI")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 12px; color: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">⚙️</div>
            <div style="font-size: 0.875rem; opacity: 0.9; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px;">Approval Mode</div>
            <div style="font-size: 1.75rem; font-weight: 700;">{}</div>
        </div>
        """.format(approval_mode_val), unsafe_allow_html=True)
    
    with col2:
        kill_status_text = "ACTIVE" if st.session_state.config.get("kill_switch") else "INACTIVE"
        kill_color = "#ef4444" if st.session_state.config.get("kill_switch") else "#10b981"
        kill_icon = "🛑" if st.session_state.config.get("kill_switch") else "✅"
        st.markdown("""
        <div style="background: linear-gradient(135deg, {} 0%, {} 100%); padding: 1.5rem; border-radius: 12px; color: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{}</div>
            <div style="font-size: 0.875rem; opacity: 0.9; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px;">Kill Switch</div>
            <div style="font-size: 1.75rem; font-weight: 700;">{}</div>
        </div>
        """.format(kill_color, kill_color, kill_icon, kill_status_text), unsafe_allow_html=True)
    
    with col3:
        max_daily_dd_val = f"{st.session_state.config.get('max_daily_dd', 0.03):.1%}"
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 1.5rem; border-radius: 12px; color: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📉</div>
            <div style="font-size: 0.875rem; opacity: 0.9; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px;">Max Daily DD</div>
            <div style="font-size: 1.75rem; font-weight: 700;">{}</div>
        </div>
        """.format(max_daily_dd_val), unsafe_allow_html=True)
    
    with col4:
        max_total_dd_val = f"{st.session_state.config.get('max_total_dd', 0.12):.1%}"
        st.markdown("""
        <div style="background: linear-gradient(135deg, #ec4899 0%, #be185d 100%); padding: 1.5rem; border-radius: 12px; color: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">⚠️</div>
            <div style="font-size: 0.875rem; opacity: 0.9; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px;">Max Total DD</div>
            <div style="font-size: 1.75rem; font-weight: 700;">{}</div>
        </div>
        """.format(max_total_dd_val), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Equity Curve Analysis Section
    st.markdown("## 📈 Equity Curve Analysis")
    st.markdown("---")
    
    # Analysis Input Card
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("""
            <div style="color: #075985; font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem;">
                Ticker Symbol
            </div>
            """, unsafe_allow_html=True)
            ticker = st.text_input(
                "Ticker Symbol",
                value="SPY",
                placeholder="Enter stock ticker (e.g., AAPL, MSFT, SPY)",
                help="Enter the stock symbol to analyze",
                label_visibility="collapsed"
            )
        
        with col2:
            st.markdown("""
            <div style="color: #075985; font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem;">
                Analysis Period
            </div>
            """, unsafe_allow_html=True)
            days = st.slider(
                "Analysis Period",
                30, 365, 90,
                help="Number of days to analyze",
                label_visibility="collapsed"
            )
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            analyze_btn = st.button("📊 Analyze Equity", use_container_width=True, type="primary")
        
        if analyze_btn:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period=f"{days}d")
                
                if not hist.empty:
                    equity = hist["Close"]
                    risk_status = st.session_state.risk_manager.evaluate(equity)
                    
                    # Calculate returns
                    returns = equity.pct_change().dropna()
                    daily_returns = returns
                    
                    # Calculate drawdown
                    peak = equity.cummax()
                    drawdown = (peak - equity) / peak
                    
                    # Calculate key metrics
                    total_return = (equity.iloc[-1] / equity.iloc[0] - 1)
                    annualized_return = ((equity.iloc[-1] / equity.iloc[0]) ** (252 / len(equity)) - 1) if len(equity) > 0 else 0
                    volatility = returns.std() * np.sqrt(252)  # Annualized volatility
                    sharpe_ratio = (annualized_return / volatility) if volatility > 0 else 0
                    
                    # Sortino ratio (downside deviation)
                    downside_returns = returns[returns < 0]
                    downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
                    sortino_ratio = (annualized_return / downside_std) if downside_std > 0 else 0
                    
                    # Calmar ratio (annualized return / max drawdown)
                    max_dd = drawdown.max()
                    calmar_ratio = (annualized_return / max_dd) if max_dd > 0 else 0
                    
                    # Beta calculation (vs SPY)
                    try:
                        spy = yf.Ticker("SPY")
                        spy_hist = spy.history(period=f"{days}d")
                        if not spy_hist.empty and len(spy_hist) == len(equity):
                            spy_returns = spy_hist["Close"].pct_change().dropna()
                            if len(spy_returns) == len(returns):
                                covariance = np.cov(returns, spy_returns)[0][1]
                                spy_variance = np.var(spy_returns)
                                beta = covariance / spy_variance if spy_variance > 0 else 0
                                
                                # Alpha (excess return over risk-free rate, simplified)
                                risk_free_rate = 0.05  # Assume 5% risk-free rate
                                alpha = annualized_return - (risk_free_rate + beta * (annualized_return - risk_free_rate))
                            else:
                                beta = None
                                alpha = None
                        else:
                            beta = None
                            alpha = None
                    except:
                        beta = None
                        alpha = None
                    
                    # Win rate (positive days)
                    win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0
                    
                    # Profit factor (sum of wins / abs(sum of losses))
                    wins = returns[returns > 0].sum()
                    losses = abs(returns[returns < 0].sum())
                    profit_factor = wins / losses if losses > 0 else float('inf')
                    
                    # Store in session state
                    st.session_state.equity_history = equity.tolist()
                    st.session_state.equity_data = {
                        'ticker': ticker,
                        'equity': equity,
                        'returns': returns,
                        'drawdown': drawdown
                    }
                    
                    # Plot
                    import matplotlib.pyplot as plt
                    fig, axes = plt.subplots(3, 1, figsize=(12, 12))
                    
                    # Equity curve
                    axes[0].plot(equity.index, equity.values, label="Equity", linewidth=2, color='blue')
                    axes[0].set_title(f"{ticker} Equity Curve")
                    axes[0].set_ylabel("Price")
                    axes[0].legend()
                    axes[0].grid(True, alpha=0.3)
                    
                    # Returns distribution
                    axes[1].hist(returns, bins=50, alpha=0.7, color='green', edgecolor='#94a3b8')
                    axes[1].axvline(x=0, color='red', linestyle='--', linewidth=2)
                    axes[1].set_title("Daily Returns Distribution")
                    axes[1].set_ylabel("Frequency")
                    axes[1].set_xlabel("Return %")
                    axes[1].grid(True, alpha=0.3)
                    
                    # Drawdown
                    axes[2].fill_between(drawdown.index, 0, drawdown.values, alpha=0.3, color="red")
                    axes[2].plot(drawdown.index, drawdown.values, label="Drawdown", color="red", linewidth=2)
                    axes[2].axhline(y=st.session_state.config.get("max_total_dd", 0.12), 
                                   color="orange", linestyle="--", label="Max DD Limit")
                    axes[2].set_title("Drawdown Analysis")
                    axes[2].set_ylabel("Drawdown %")
                    axes[2].set_xlabel("Date")
                    axes[2].legend()
                    axes[2].grid(True, alpha=0.3)
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                    # Risk status
                    if risk_status == "KILL":
                        st.error("🚨 KILL SWITCH TRIGGERED - Maximum drawdown exceeded!")
                    else:
                        st.success("✅ Risk check passed")
                    
                    # Display comprehensive metrics in cards
                    st.markdown("## 📊 Performance Metrics")
                    st.markdown("---")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown("""
                        <div style="background: #ffffff; padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; border-left: 4px solid #60a5fa;">
                            <strong style="color: #075985; font-size: 0.95rem;">📈 Returns</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        st.metric("Total Return", f"{total_return:.2%}")
                        st.metric("Annualized Return", f"{annualized_return:.2%}")
                        st.metric("Volatility (Annualized)", f"{volatility:.2%}")
                    
                    with col2:
                        st.markdown("""
                        <div style="background: #ffffff; padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; border-left: 4px solid #34d399;">
                            <strong style="color: #075985; font-size: 0.95rem;">📊 Risk-Adjusted Ratios</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
                        st.metric("Sortino Ratio", f"{sortino_ratio:.2f}")
                        st.metric("Calmar Ratio", f"{calmar_ratio:.2f}")
                    
                    with col3:
                        st.markdown("""
                        <div style="background: #ffffff; padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; border-left: 4px solid #fbbf24;">
                            <strong style="color: #075985; font-size: 0.95rem;">⚠️ Drawdown Metrics</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        st.metric("Current Drawdown", f"{drawdown.iloc[-1]:.2%}")
                        st.metric("Max Drawdown", f"{drawdown.max():.2%}")
                        st.metric("Win Rate", f"{win_rate:.2%}")
                    
                    with col4:
                        st.markdown("""
                        <div style="background: #ffffff; padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; border-left: 4px solid #a78bfa;">
                            <strong style="color: #075985; font-size: 0.95rem;">🔍 Market Metrics</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        if beta is not None:
                            st.metric("Beta (vs SPY)", f"{beta:.2f}")
                        else:
                            st.metric("Beta (vs SPY)", "N/A")
                        if alpha is not None:
                            st.metric("Alpha", f"{alpha:.2%}")
                        else:
                            st.metric("Alpha", "N/A")
                        profit_factor_display = f"{profit_factor:.2f}" if profit_factor != float('inf') else "∞"
                        st.metric("Profit Factor", profit_factor_display)
                    
                    # Additional statistics
                    st.markdown("## 📈 Additional Statistics")
                    st.markdown("---")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("""
                        <div style="background: #f8fafc; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #667eea;">
                            <h4 style="color: #075985; margin-top: 0; margin-bottom: 1rem;">📊 Return Statistics</h4>
                            <p style="margin: 0.5rem 0;"><strong>Best Day:</strong> {}</p>
                            <p style="margin: 0.5rem 0;"><strong>Worst Day:</strong> {}</p>
                            <p style="margin: 0.5rem 0;"><strong>Avg Daily Return:</strong> {}</p>
                            <p style="margin: 0.5rem 0;"><strong>Median Daily Return:</strong> {}</p>
                        </div>
                        """.format(
                            f"{returns.max():.2%}",
                            f"{returns.min():.2%}",
                            f"{returns.mean():.2%}",
                            f"{returns.median():.2%}"
                        ), unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("""
                        <div style="background: #f8fafc; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #10b981;">
                            <h4 style="color: #075985; margin-top: 0; margin-bottom: 1rem;">💰 Price Statistics</h4>
                            <p style="margin: 0.5rem 0;"><strong>Starting Price:</strong> ${}</p>
                            <p style="margin: 0.5rem 0;"><strong>Ending Price:</strong> ${}</p>
                            <p style="margin: 0.5rem 0;"><strong>Highest Price:</strong> ${}</p>
                            <p style="margin: 0.5rem 0;"><strong>Lowest Price:</strong> ${}</p>
                        </div>
                        """.format(
                            f"{equity.iloc[0]:.2f}",
                            f"{equity.iloc[-1]:.2f}",
                            f"{equity.max():.2f}",
                            f"{equity.min():.2f}"
                        ), unsafe_allow_html=True)
                    
                    with col3:
                        avg_win = f"{returns[returns > 0].mean():.2%}" if (returns > 0).sum() > 0 else "N/A"
                        avg_loss = f"{returns[returns < 0].mean():.2%}" if (returns < 0).sum() > 0 else "N/A"
                        st.markdown("""
                        <div style="background: #f8fafc; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #f59e0b;">
                            <h4 style="color: #075985; margin-top: 0; margin-bottom: 1rem;">⚠️ Risk Statistics</h4>
                            <p style="margin: 0.5rem 0;"><strong>Days Analyzed:</strong> {}</p>
                            <p style="margin: 0.5rem 0;"><strong>Positive Days:</strong> {}</p>
                            <p style="margin: 0.5rem 0;"><strong>Negative Days:</strong> {}</p>
                            <p style="margin: 0.5rem 0;"><strong>Average Win:</strong> {}</p>
                            <p style="margin: 0.5rem 0;"><strong>Average Loss:</strong> {}</p>
                        </div>
                        """.format(
                            len(equity),
                            (returns > 0).sum(),
                            (returns < 0).sum(),
                            avg_win,
                            avg_loss
                        ), unsafe_allow_html=True)
                else:
                    st.error("No data available for this ticker")
            except Exception as e:
                st.error(f"Error fetching data: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

with tab2:
    st.markdown("## 💰 Trade Management")
    st.markdown("---")
    
    # Mode indicator
    approval_mode_display = st.session_state.config.get('approval_mode', 'SEMI')
    mode_color = "#10b981" if approval_mode_display == "AUTO" else "#f59e0b"
    mode_text = "Automatic approval" if approval_mode_display == "AUTO" else "Manual approval required"
    st.markdown(f"""
    <div style="background: {mode_color}; padding: 1rem 1.5rem; border-radius: 8px; color: white; margin-bottom: 2rem; box-shadow: 0 2px 4px rgba(59, 130, 246, 0.15);">
        <div style="font-size: 0.875rem; opacity: 0.9; margin-bottom: 0.25rem;">CURRENT MODE</div>
        <div style="font-size: 1.25rem; font-weight: 700;">{approval_mode_display}</div>
        <div style="font-size: 0.875rem; opacity: 0.9; margin-top: 0.25rem;">{mode_text}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📋 Trade Approval Workflow")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 📤 Submit New Trade")
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("""
            <div style="color: #075985; font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem;">
                Symbol
            </div>
            """, unsafe_allow_html=True)
            symbol = st.text_input(
                "Symbol", 
                value="AAPL", 
                placeholder="e.g., AAPL, MSFT",
                help="Enter the stock symbol",
                label_visibility="collapsed"
            )
            col_side, col_qty = st.columns(2)
            with col_side:
                st.markdown("""
                <div style="color: #075985; font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem;">
                    Side
                </div>
                """, unsafe_allow_html=True)
                side = st.selectbox(
                    "Side", 
                    ["BUY", "SELL"],
                    help="Buy or Sell",
                    label_visibility="collapsed"
                )
            with col_qty:
                st.markdown("""
                <div style="color: #075985; font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem;">
                    Quantity
                </div>
                """, unsafe_allow_html=True)
                quantity = st.number_input(
                    "Quantity", 
                    min_value=1, 
                    value=100,
                    help="Number of shares",
                    label_visibility="collapsed"
                )
            st.markdown("""
            <div style="color: #075985; font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem;">
                Price
            </div>
            """, unsafe_allow_html=True)
            price = st.number_input(
                "Price", 
                min_value=0.0, 
                value=150.0, 
                step=0.01, 
                format="%.2f",
                help="Price per share",
                label_visibility="collapsed"
            )
            
            if st.button("📤 Submit Trade", use_container_width=True, type="primary"):
                trade = {
                    "symbol": symbol,
                    "side": side,
                    "quantity": int(quantity),
                    "price": float(price),
                    "timestamp": datetime.now().isoformat()
                }
                
                if st.session_state.config.get("approval_mode") == "AUTO":
                    approved = st.session_state.approval.approve(trade)
                    if approved:
                        st.success("✅ Trade auto-approved and executed")
                        log_event("TRADE_EXECUTED", trade)
                else:
                    st.session_state.pending_trades.append(trade)
                    st.success("📋 Trade submitted for approval")
                    log_event("TRADE_SUBMITTED", trade)
    
    with col2:
        st.markdown("#### ⏳ Pending Approvals")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.session_state.pending_trades:
            for i, trade in enumerate(st.session_state.pending_trades):
                with st.container():
                    st.markdown(f"""
                    <div style="background: #ffffff; padding: 1rem; border-radius: 8px; border-left: 4px solid #60a5fa; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(59, 130, 246, 0.1);">
                        <div style="font-weight: 600; font-size: 1.1rem; color: #075985;">{trade['symbol']}</div>
                        <div style="color: #0369a1; font-size: 0.875rem;">{trade['side']} {trade['quantity']} shares @ ${trade['price']:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_approve, col_reject = st.columns(2)
                    
                    with col_approve:
                        if st.button("✅ Approve", key=f"approve_{i}", use_container_width=True):
                            trade["approved"] = True
                            log_event("TRADE_EXECUTED", trade)
                            st.session_state.pending_trades.pop(i)
                            st.rerun()
                    
                    with col_reject:
                        if st.button("❌ Reject", key=f"reject_{i}", use_container_width=True):
                            trade["approved"] = False
                            log_event("TRADE_REJECTED", trade)
                            st.session_state.pending_trades.pop(i)
                            st.rerun()
        else:
            st.markdown("""
            <div style="background: #ffffff; padding: 2rem; border-radius: 8px; text-align: center; border: 2px dashed #93c5fd;">
                <p style="color: #0369a1; margin: 0; font-size: 1rem;">📭 No pending trades</p>
                <p style="color: #60a5fa; margin: 0.5rem 0 0 0; font-size: 0.875rem;">Submit a trade to see it here</p>
            </div>
            """, unsafe_allow_html=True)

with tab3:
    st.markdown("## ⚠️ Risk Management Monitor")
    st.markdown("---")
    
    st.markdown("### ⚙️ Risk Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 1.5rem; border-radius: 12px; color: white; margin-bottom: 1rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="font-size: 0.875rem; opacity: 0.9; margin-bottom: 0.5rem;">MAX DAILY DRAWDOWN</div>
            <div style="font-size: 2rem; font-weight: 700;">{}</div>
        </div>
        """.format(f"{st.session_state.config.get('max_daily_dd', 0.03):.2%}"), unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #ec4899 0%, #be185d 100%); padding: 1.5rem; border-radius: 12px; color: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="font-size: 0.875rem; opacity: 0.9; margin-bottom: 0.5rem;">MAX TOTAL DRAWDOWN</div>
            <div style="font-size: 2rem; font-weight: 700;">{}</div>
        </div>
        """.format(f"{st.session_state.config.get('max_total_dd', 0.12):.2%}"), unsafe_allow_html=True)
    
    with col2:
        kill_status = st.session_state.risk_manager.kill
        if kill_status:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 2rem; border-radius: 12px; color: white; text-align: center; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🚨</div>
                <div style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">KILL SWITCH ACTIVE</div>
                <div style="font-size: 0.875rem; opacity: 0.9;">Trading is disabled due to risk limits</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 2rem; border-radius: 12px; color: white; text-align: center; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">✅</div>
                <div style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">SYSTEM OPERATIONAL</div>
                <div style="font-size: 0.875rem; opacity: 0.9;">Trading is enabled</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📊 Risk Evaluation")
    st.markdown("---")
    
    if st.session_state.equity_history:
        equity_series = pd.Series(st.session_state.equity_history)
        risk_status = st.session_state.risk_manager.evaluate(equity_series)
        
        peak = equity_series.cummax()
        drawdown = (peak - equity_series) / peak
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Current Equity", f"${equity_series.iloc[-1]:.2f}")
        
        with col2:
            st.metric("Peak Equity", f"${peak.iloc[-1]:.2f}")
        
        with col3:
            st.metric("Current Drawdown", f"{drawdown.iloc[-1]:.2%}")
        
        if risk_status == "KILL":
            st.error("⚠️ **Risk limit exceeded** - Kill switch activated")
        else:
            st.success("✅ **Risk within acceptable limits**")
    else:
        st.markdown("""
        <div style="background: #ffffff; padding: 2rem; border-radius: 8px; text-align: center; border: 2px dashed #93c5fd;">
            <p style="color: #0369a1; margin: 0; font-size: 1rem;">📊 No risk data available</p>
            <p style="color: #60a5fa; margin: 0.5rem 0 0 0; font-size: 0.875rem;">Run equity analysis in Dashboard tab to see risk evaluation</p>
        </div>
        """, unsafe_allow_html=True)

with tab4:
    st.markdown("## 🔄 Broker Reconciliation")
    st.markdown("---")
    
    st.markdown("### 📊 Strategy vs Broker Positions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Strategy Positions")
        strategy_trades = st.text_area(
            "Enter strategy trades (one per line, format: SYMBOL QTY)",
            value="AAPL 100\nMSFT 50\nGOOGL 25",
            height=150,
            label_visibility="collapsed",
            help="Format: SYMBOL QTY (one per line)"
        )
    
    with col2:
        st.markdown("#### 🏦 Broker Positions")
        broker_trades = st.text_area(
            "Enter broker trades (one per line, format: SYMBOL QTY)",
            value="AAPL 100\nMSFT 50\nGOOGL 25",
            height=150,
            label_visibility="collapsed",
            help="Format: SYMBOL QTY (one per line)"
        )
    
    if st.button("🔄 Reconcile Positions", use_container_width=True, type="primary"):
        strategy_list = [t.strip() for t in strategy_trades.split("\n") if t.strip()]
        broker_list = [t.strip() for t in broker_trades.split("\n") if t.strip()]
        
        mismatches = reconcile(strategy_list, broker_list)
        
        if mismatches:
            st.error(f"❌ **Found {len(mismatches)} mismatches:**")
            for mismatch in mismatches:
                st.markdown(f"<p style='color: #dc2626; margin: 0.5rem 0; font-weight: 500;'>• {mismatch}</p>", unsafe_allow_html=True)
        else:
            st.success("✅ **All positions reconciled** - No mismatches found")

with tab5:
    st.markdown("## 📋 Trading Rules Analysis")
    st.markdown("---")
    st.markdown("<p style='color: #64748b; font-size: 1rem; margin-bottom: 2rem;'>Analyze stocks based on fundamental, trend, and structure rules</p>", unsafe_allow_html=True)
    
    col_ticker, col_btn = st.columns([3, 1])
    with col_ticker:
        st.markdown("""
        <div style="color: #075985; font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem;">
            Enter Ticker Symbol
        </div>
        """, unsafe_allow_html=True)
        ticker_input = st.text_input(
            "Enter ticker symbol", 
            value="AAPL", 
            key="rules_ticker",
            placeholder="e.g., AAPL, MSFT, GOOGL",
            help="Enter the stock symbol to analyze",
            label_visibility="collapsed"
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_button = st.button("🔍 Analyze Trading Rules", key="analyze_rules", use_container_width=True, type="primary")
    
    if analyze_button:
        try:
            stock = yf.Ticker(ticker_input)
            hist = stock.history(period="1y")
            
            if hist.empty:
                st.error("No data available for this ticker")
            else:
                # Get current price
                current_price = hist["Close"].iloc[-1]
                
                # ========== RULE 1: FUNDAMENTALS ==========
                st.markdown("## 📊 Rule 1: Fundamentals - Profit Growth")
                st.markdown("**Select quality stocks with profit growth**")
                
                # Detect market (Indian vs US) for appropriate thresholds
                is_indian_ticker = ticker_input.endswith('.NS') or ticker_input.endswith('.BO')
                market_label = "🇮🇳 Indian Market" if is_indian_ticker else "🇺🇸 US Market"
                
                # Market-specific thresholds
                if is_indian_ticker:
                    # Indian market thresholds (typically lower than US)
                    PROFIT_MARGIN_THRESHOLD = 5.0  # 5% is good for Indian markets
                    ROE_THRESHOLD = 12.0  # 12% is good for Indian markets
                    REVENUE_GROWTH_THRESHOLD = 10.0  # 10% YoY growth
                    INCOME_GROWTH_THRESHOLD = 5.0  # 5% YoY growth
                else:
                    # US market thresholds
                    PROFIT_MARGIN_THRESHOLD = 10.0  # 10% margin
                    ROE_THRESHOLD = 15.0  # 15% ROE
                    REVENUE_GROWTH_THRESHOLD = 10.0  # 10% YoY growth
                    INCOME_GROWTH_THRESHOLD = 10.0  # 10% YoY growth
                
                st.markdown(f"<p style='color: #0369a1; font-size: 0.9rem; margin-bottom: 1rem;'><strong>Market:</strong> {market_label} | Thresholds: Profit Margin >{PROFIT_MARGIN_THRESHOLD}%, ROE >{ROE_THRESHOLD}%</p>", unsafe_allow_html=True)
                st.markdown("---")
                
                try:
                    info = stock.info
                    financials = None
                    quarterly_financials = None
                    
                    try:
                        financials = stock.financials
                    except:
                        pass
                    
                    try:
                        quarterly_financials = stock.quarterly_financials
                    except:
                        pass
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    # Revenue Growth
                    revenue_growth = None
                    try:
                        if financials is not None and not financials.empty:
                            # Try different possible column names (including Indian variations)
                            revenue_row = None
                            for row_name in ['Total Revenue', 'Revenue', 'totalRevenue', 'Total Income', 
                                           'Operating Revenue', 'Net Sales', 'Sales']:
                                if row_name in financials.index:
                                    revenue_row = financials.loc[row_name]
                                    break
                            
                            if revenue_row is not None and len(revenue_row) >= 2:
                                # Get consecutive years (most recent first in yfinance)
                                # Use original order, but skip NaN values
                                valid_indices = []
                                for i in range(len(revenue_row)):
                                    if not pd.isna(revenue_row.iloc[i]) and revenue_row.iloc[i] != 0:
                                        valid_indices.append(i)
                                
                                if len(valid_indices) >= 2:
                                    # Compare first two valid consecutive periods
                                    latest_idx = valid_indices[0]
                                    previous_idx = valid_indices[1] if len(valid_indices) > 1 else valid_indices[0]
                                    
                                    latest = revenue_row.iloc[latest_idx]
                                    previous = revenue_row.iloc[previous_idx]
                                    
                                    if previous != 0 and abs(previous) > 0.0001:  # Avoid division by very small numbers
                                        revenue_growth = ((latest - previous) / abs(previous)) * 100
                                        # Display the value (even if extreme, user should see it)
                                        with col1:
                                            if abs(revenue_growth) > 10000:
                                                st.metric("Revenue Growth (YoY)", f"{revenue_growth:.1f}%", 
                                                         delta="⚠️ Extreme - check data", delta_color="off")
                                            else:
                                                st.metric("Revenue Growth (YoY)", f"{revenue_growth:.1f}%")
                    except Exception as e:
                        pass
                    
                    if revenue_growth is None or pd.isna(revenue_growth):
                        with col1:
                            st.metric("Revenue Growth (YoY)", "N/A")
                    
                    # Net Income Growth
                    income_growth = None
                    try:
                        if financials is not None and not financials.empty:
                            income_row = None
                            # Try more column name variations (including Indian variations)
                            for row_name in ['Net Income', 'Net Income Common Stockholders', 'netIncomeToCommon',
                                           'Profit After Tax', 'PAT', 'Net Profit', 'Net Profit After Tax']:
                                if row_name in financials.index:
                                    income_row = financials.loc[row_name]
                                    break
                            
                            if income_row is not None and len(income_row) >= 2:
                                # Get consecutive years (most recent first in yfinance)
                                # Use original order, but skip NaN values
                                valid_indices = []
                                for i in range(len(income_row)):
                                    if not pd.isna(income_row.iloc[i]) and income_row.iloc[i] != 0:
                                        valid_indices.append(i)
                                
                                if len(valid_indices) >= 2:
                                    # Compare first two valid consecutive periods
                                    latest_idx = valid_indices[0]
                                    previous_idx = valid_indices[1] if len(valid_indices) > 1 else valid_indices[0]
                                    
                                    latest = income_row.iloc[latest_idx]
                                    previous = income_row.iloc[previous_idx]
                                    
                                    if previous != 0 and abs(previous) > 0.0001:  # Avoid division by very small numbers
                                        income_growth = ((latest - previous) / abs(previous)) * 100
                                        # Display the value (even if extreme, user should see it)
                                        with col2:
                                            if abs(income_growth) > 10000:
                                                st.metric("Net Income Growth (YoY)", f"{income_growth:.1f}%",
                                                         delta="⚠️ Extreme - check data", delta_color="off")
                                            else:
                                                st.metric("Net Income Growth (YoY)", f"{income_growth:.1f}%")
                    except Exception as e:
                        pass
                    
                    if income_growth is None or pd.isna(income_growth):
                        with col2:
                            st.metric("Net Income Growth (YoY)", "N/A")
                    
                    # Profit Margin
                    profit_margin = None
                    try:
                        if 'profitMargins' in info and info['profitMargins'] is not None:
                            profit_margin = info['profitMargins'] * 100
                            with col3:
                                st.metric("Profit Margin", f"{profit_margin:.2f}%")
                    except:
                        pass
                    
                    if profit_margin is None:
                        with col3:
                            st.metric("Profit Margin", "N/A")
                    
                    # ROE
                    roe = None
                    try:
                        if 'returnOnEquity' in info and info['returnOnEquity'] is not None:
                            roe = info['returnOnEquity'] * 100
                            with col4:
                                st.metric("Return on Equity (ROE)", f"{roe:.2f}%")
                    except:
                        pass
                    
                    if roe is None:
                        with col4:
                            st.metric("Return on Equity (ROE)", "N/A")
                    
                    # Quarterly earnings growth
                    q_growth = None
                    try:
                        if quarterly_financials is not None and not quarterly_financials.empty:
                            q_income_row = None
                            # Try more column name variations
                            for row_name in ['Net Income', 'Net Income Common Stockholders', 
                                           'Profit After Tax', 'PAT', 'Net Profit']:
                                if row_name in quarterly_financials.index:
                                    q_income_row = quarterly_financials.loc[row_name]
                                    break
                            
                            if q_income_row is not None and len(q_income_row) >= 2:
                                # Remove NaN values and get valid data
                                q_income_row_clean = q_income_row.dropna()
                                if len(q_income_row_clean) >= 2:
                                    latest_q = q_income_row_clean.iloc[0]
                                    previous_q = q_income_row_clean.iloc[1]
                                    if previous_q != 0 and not pd.isna(latest_q) and not pd.isna(previous_q):
                                        q_growth = ((latest_q - previous_q) / abs(previous_q)) * 100
                                        st.metric("Quarterly Earnings Growth (QoQ)", f"{q_growth:.1f}%")
                    except Exception as e:
                        pass
                    
                    if q_growth is None or pd.isna(q_growth):
                        st.metric("Quarterly Earnings Growth (QoQ)", "N/A")
                    
                    # Rule 1 Assessment - Enhanced scoring with 5 criteria
                    rule1_score = 0
                    max_score = 5  # Now scoring 5 criteria
                    rule1_reasons = []
                    
                    # 1. Profit Margin (with negative handling)
                    try:
                        if profit_margin is not None:
                            if profit_margin < 0:
                                rule1_reasons.append("❌ **Negative profit margin** - Company is losing money")
                            elif profit_margin >= PROFIT_MARGIN_THRESHOLD:
                                rule1_score += 1
                                rule1_reasons.append(f"✅ Strong profit margin ({profit_margin:.2f}% > {PROFIT_MARGIN_THRESHOLD}%)")
                            else:
                                rule1_reasons.append(f"⚠️ Low profit margin ({profit_margin:.2f}% < {PROFIT_MARGIN_THRESHOLD}%)")
                        else:
                            rule1_reasons.append("⚠️ Profit margin data unavailable")
                    except:
                        rule1_reasons.append("⚠️ Profit margin data unavailable")
                    
                    # 2. ROE (with negative handling)
                    try:
                        if roe is not None:
                            if roe < 0:
                                rule1_reasons.append("❌ **Negative ROE** - Poor return on equity")
                            elif roe >= ROE_THRESHOLD:
                                rule1_score += 1
                                rule1_reasons.append(f"✅ Strong ROE ({roe:.2f}% > {ROE_THRESHOLD}%)")
                            else:
                                rule1_reasons.append(f"⚠️ Moderate ROE ({roe:.2f}% < {ROE_THRESHOLD}%)")
                        else:
                            rule1_reasons.append("⚠️ ROE data unavailable")
                    except:
                        rule1_reasons.append("⚠️ ROE data unavailable")
                    
                    # 3. Revenue Growth (now included in scoring)
                    try:
                        if revenue_growth is not None:
                            # Check for unrealistic growth (likely data quality issue - don't count in score)
                            if abs(revenue_growth) > 1000:
                                rule1_reasons.append(f"⚠️ Extreme revenue growth ({revenue_growth:.1f}% YoY) - likely data quality issue or very small base (not counted in score)")
                            elif revenue_growth >= REVENUE_GROWTH_THRESHOLD:
                                rule1_score += 1
                                rule1_reasons.append(f"✅ Strong revenue growth ({revenue_growth:.1f}% YoY)")
                            elif revenue_growth > 0:
                                rule1_reasons.append(f"⚠️ Moderate revenue growth ({revenue_growth:.1f}% YoY)")
                            else:
                                rule1_reasons.append(f"❌ Declining revenue ({revenue_growth:.1f}% YoY)")
                        else:
                            rule1_reasons.append("⚠️ Revenue growth data unavailable")
                    except:
                        rule1_reasons.append("⚠️ Revenue growth data unavailable")
                    
                    # 4. Net Income Growth (now included in scoring)
                    try:
                        if income_growth is not None:
                            # Check for unrealistic growth (likely data quality issue - don't count in score)
                            if abs(income_growth) > 1000:
                                rule1_reasons.append(f"⚠️ Extreme net income growth ({income_growth:.1f}% YoY) - likely data quality issue or very small base (not counted in score)")
                            elif income_growth >= INCOME_GROWTH_THRESHOLD:
                                rule1_score += 1
                                rule1_reasons.append(f"✅ Strong net income growth ({income_growth:.1f}% YoY)")
                            elif income_growth > 0:
                                rule1_reasons.append(f"⚠️ Moderate net income growth ({income_growth:.1f}% YoY)")
                            else:
                                rule1_reasons.append(f"❌ Declining net income ({income_growth:.1f}% YoY)")
                        else:
                            rule1_reasons.append("⚠️ Net income growth data unavailable")
                    except:
                        rule1_reasons.append("⚠️ Net income growth data unavailable")
                    
                    # 5. Quarterly Earnings Growth
                    try:
                        if q_growth is not None:
                            if q_growth > 0:
                                rule1_score += 1
                                rule1_reasons.append(f"✅ Positive quarterly earnings growth ({q_growth:.1f}% QoQ)")
                            else:
                                rule1_reasons.append(f"⚠️ Negative or flat quarterly earnings ({q_growth:.1f}% QoQ)")
                        else:
                            rule1_reasons.append("⚠️ Quarterly earnings data unavailable")
                    except:
                        rule1_reasons.append("⚠️ Quarterly earnings data unavailable")
                    
                    # Assessment result
                    if rule1_score >= 4:
                        st.success(f"✅ **Rule 1 PASSED** ({rule1_score}/{max_score} criteria met)")
                    elif rule1_score >= 2:
                        st.warning(f"⚠️ **Rule 1 PARTIAL** ({rule1_score}/{max_score} criteria met)")
                    else:
                        st.error(f"❌ **Rule 1 FAILED** ({rule1_score}/{max_score} criteria met)")
                    
                    for reason in rule1_reasons:
                        st.markdown(f"<p style='color: #075985; margin: 0.5rem 0;'>{reason}</p>", unsafe_allow_html=True)
                        
                except Exception as e:
                    st.warning(f"Fundamental data not fully available: {str(e)}")
                    st.info("Some fundamental metrics may not be available for this ticker")
                
                st.divider()
                
                # ========== HEIKIN ASHI CHART ==========
                st.markdown("## 🕯️ Heikin Ashi Chart")
                st.markdown("**Smoothed candlestick chart for trend identification**")
                st.markdown("---")
                
                # Calculate Heikin Ashi
                ha_close = (hist['Open'] + hist['High'] + hist['Low'] + hist['Close']) / 4
                ha_open = pd.Series(index=hist.index, dtype=float)
                ha_open.iloc[0] = (hist['Open'].iloc[0] + hist['Close'].iloc[0]) / 2
                for i in range(1, len(hist)):
                    ha_open.iloc[i] = (ha_open.iloc[i-1] + ha_close.iloc[i-1]) / 2
                
                ha_high = pd.concat([hist['High'], ha_open, ha_close], axis=1).max(axis=1)
                ha_low = pd.concat([hist['Low'], ha_open, ha_close], axis=1).min(axis=1)
                
                # Create Heikin Ashi DataFrame
                ha_data = pd.DataFrame({
                    'Open': ha_open,
                    'High': ha_high,
                    'Low': ha_low,
                    'Close': ha_close
                })
                
                # Calculate SMA 50 and SMA 100 for Heikin Ashi
                ha_sma50 = ha_close.rolling(window=50).mean()
                ha_sma100 = ha_close.rolling(window=100).mean()
                
                # Plot Heikin Ashi with SMAs
                import matplotlib.pyplot as plt_ha
                fig_ha, ax_ha = plt_ha.subplots(figsize=(16, 8))
                
                # Set background color (dark theme like TradingView)
                fig_ha.patch.set_facecolor('#131722')
                ax_ha.set_facecolor('#131722')
                
                # Plot SMA 50 (green) and SMA 100 (red) first so they appear behind candles
                ha_sma50_valid = ha_sma50.dropna()
                ha_sma100_valid = ha_sma100.dropna()
                
                if len(ha_sma50_valid) > 0:
                    ax_ha.plot(ha_sma50_valid.index, ha_sma50_valid.values, 
                              label='SMA 50', linewidth=2.5, color='#26a69a', alpha=0.9, zorder=1)
                
                if len(ha_sma100_valid) > 0:
                    ax_ha.plot(ha_sma100_valid.index, ha_sma100_valid.values, 
                              label='SMA 100', linewidth=2.5, color='#ef5350', alpha=0.9, zorder=1)
                
                # Plot Heikin Ashi candles with improved visibility
                for i in range(len(ha_data)):
                    open_price = ha_data['Open'].iloc[i]
                    close_price = ha_data['Close'].iloc[i]
                    high_price = ha_data['High'].iloc[i]
                    low_price = ha_data['Low'].iloc[i]
                    
                    # Use TradingView-like colors: bright green for bullish, bright red for bearish
                    if close_price >= open_price:
                        body_color = '#26a69a'  # Green (bullish)
                        wick_color = '#26a69a'
                    else:
                        body_color = '#ef5350'  # Red (bearish)
                        wick_color = '#ef5350'
                    
                    # Draw wick (thicker and more visible)
                    ax_ha.plot([hist.index[i], hist.index[i]], [low_price, high_price], 
                              color=wick_color, linewidth=1.2, alpha=0.9, zorder=2)
                    
                    # Draw body (thicker bars for better visibility)
                    body_height = abs(close_price - open_price)
                    if body_height > 0:
                        ax_ha.bar(hist.index[i], body_height, bottom=min(open_price, close_price),
                                 color=body_color, alpha=0.85, width=0.6, edgecolor=body_color, 
                                 linewidth=0.5, zorder=2)
                    else:
                        # Doji candle
                        ax_ha.plot([hist.index[i]], [close_price], marker='_', 
                                  color=body_color, markersize=15, alpha=0.85, zorder=2)
                
                # Styling improvements
                ax_ha.set_title(f"{ticker_input} - Heikin Ashi Chart with SMA 50 & SMA 100", 
                              fontsize=16, fontweight='bold', color='#d1d4dc', pad=20)
                ax_ha.set_ylabel("Price ($)", fontsize=13, color='#d1d4dc')
                ax_ha.set_xlabel("Date", fontsize=13, color='#d1d4dc')
                
                # Grid styling (subtle like TradingView)
                ax_ha.grid(True, alpha=0.15, linestyle='-', linewidth=0.5, color='#2a2e39')
                ax_ha.set_axisbelow(True)
                
                # Axis colors
                ax_ha.tick_params(colors='#868993', labelsize=11)
                ax_ha.spines['bottom'].set_color('#2a2e39')
                ax_ha.spines['top'].set_color('#2a2e39')
                ax_ha.spines['right'].set_color('#2a2e39')
                ax_ha.spines['left'].set_color('#2a2e39')
                
                # Legend with better styling
                legend = ax_ha.legend(loc='upper left', fontsize=11, framealpha=0.9, 
                                     facecolor='#1e222d', edgecolor='#2a2e39', labelcolor='#d1d4dc')
                legend.get_frame().set_linewidth(1)
                
                # Date formatting
                from matplotlib.dates import DateFormatter, MonthLocator
                ax_ha.xaxis.set_major_locator(MonthLocator(interval=1))
                ax_ha.xaxis.set_major_formatter(DateFormatter('%Y-%m'))
                plt_ha.xticks(rotation=45, ha='right', color='#868993')
                
                plt_ha.tight_layout()
                st.pyplot(fig_ha)
                
                # Display SMA values
                col_sma1, col_sma2, col_sma3, col_sma4 = st.columns(4)
                with col_sma1:
                    current_ha_price = ha_close.iloc[-1]
                    st.metric("Current HA Price", f"${current_ha_price:.2f}")
                with col_sma2:
                    if len(ha_sma50_valid) > 0:
                        sma50_val = ha_sma50_valid.iloc[-1]
                        sma50_diff = ((current_ha_price - sma50_val) / sma50_val) * 100
                        st.metric("SMA 50", f"${sma50_val:.2f}", 
                                delta=f"{sma50_diff:+.2f}%", delta_color="normal")
                    else:
                        st.metric("SMA 50", "N/A")
                with col_sma3:
                    if len(ha_sma100_valid) > 0:
                        sma100_val = ha_sma100_valid.iloc[-1]
                        sma100_diff = ((current_ha_price - sma100_val) / sma100_val) * 100
                        st.metric("SMA 100", f"${sma100_val:.2f}", 
                                delta=f"{sma100_diff:+.2f}%", delta_color="normal")
                    else:
                        st.metric("SMA 100", "N/A")
                with col_sma4:
                    if len(ha_sma50_valid) > 0 and len(ha_sma100_valid) > 0:
                        sma50_val = ha_sma50_valid.iloc[-1]
                        sma100_val = ha_sma100_valid.iloc[-1]
                        if sma50_val > sma100_val:
                            st.success("🟢 SMA 50 > SMA 100")
                        else:
                            st.error("🔴 SMA 50 < SMA 100")
                    else:
                        st.info("SMA data unavailable")
                
                # Heikin Ashi trend analysis
                recent_ha = ha_data.tail(10)
                bullish_candles = (recent_ha['Close'] >= recent_ha['Open']).sum()
                bearish_candles = (recent_ha['Close'] < recent_ha['Open']).sum()
                
                col_ha1, col_ha2, col_ha3 = st.columns(3)
                with col_ha1:
                    st.metric("Recent Bullish Candles", f"{bullish_candles}/10")
                with col_ha2:
                    st.metric("Recent Bearish Candles", f"{bearish_candles}/10")
                with col_ha3:
                    if bullish_candles >= 7:
                        st.success("🟢 Strong Uptrend")
                    elif bearish_candles >= 7:
                        st.error("🔴 Strong Downtrend")
                    else:
                        st.warning("⚠️ Mixed Signals")
                
                st.divider()
                
                # ========== ICHIMOKU CHART ==========
                st.markdown("## ☁️ Ichimoku Cloud Chart")
                st.markdown("**Complete Ichimoku Kinko Hyo system for trend and support/resistance**")
                st.markdown("---")
                
                # Calculate Ichimoku components
                # Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
                period1 = 9
                period2 = 26
                period3 = 52
                
                tenkan_sen = (hist['High'].rolling(window=period1).max() + 
                             hist['Low'].rolling(window=period1).min()) / 2
                
                # Kijun-sen (Base Line): (26-period high + 26-period low) / 2
                kijun_sen = (hist['High'].rolling(window=period2).max() + 
                           hist['Low'].rolling(window=period2).min()) / 2
                
                # Senkou Span A (Leading Span A): (Tenkan-sen + Kijun-sen) / 2, shifted 26 periods forward
                senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(period2)
                
                # Senkou Span B (Leading Span B): (52-period high + 52-period low) / 2, shifted 26 periods forward
                senkou_span_b = ((hist['High'].rolling(window=period3).max() + 
                                hist['Low'].rolling(window=period3).min()) / 2).shift(period2)
                
                # Chikou Span (Lagging Span): Close price shifted 26 periods backward
                chikou_span = hist['Close'].shift(-period2)
                
                # Current Ichimoku values
                current_tenkan = tenkan_sen.iloc[-1] if not pd.isna(tenkan_sen.iloc[-1]) else None
                current_kijun = kijun_sen.iloc[-1] if not pd.isna(kijun_sen.iloc[-1]) else None
                current_senkou_a = senkou_span_a.iloc[-1] if not pd.isna(senkou_span_a.iloc[-1]) else None
                current_senkou_b = senkou_span_b.iloc[-1] if not pd.isna(senkou_span_b.iloc[-1]) else None
                
                # Plot Ichimoku
                import matplotlib.pyplot as plt_ich
                fig_ich, ax_ich = plt_ich.subplots(figsize=(14, 8))
                
                # Plot price
                ax_ich.plot(hist.index, hist['Close'], label='Price', linewidth=2, color='#3b82f6')
                
                # Plot Tenkan-sen and Kijun-sen
                tenkan_valid = tenkan_sen.dropna()
                kijun_valid = kijun_sen.dropna()
                if len(tenkan_valid) > 0:
                    ax_ich.plot(tenkan_valid.index, tenkan_valid.values, 
                              label='Tenkan-sen (9)', linewidth=1.5, color='blue', alpha=0.8)
                if len(kijun_valid) > 0:
                    ax_ich.plot(kijun_valid.index, kijun_valid.values, 
                              label='Kijun-sen (26)', linewidth=1.5, color='red', alpha=0.8)
                
                # Plot Ichimoku Cloud (Kumo)
                senkou_a_valid = senkou_span_a.dropna()
                senkou_b_valid = senkou_span_b.dropna()
                
                if len(senkou_a_valid) > 0 and len(senkou_b_valid) > 0:
                    # Find common index
                    common_idx = senkou_a_valid.index.intersection(senkou_b_valid.index)
                    if len(common_idx) > 0:
                        cloud_a = senkou_a_valid.loc[common_idx]
                        cloud_b = senkou_b_valid.loc[common_idx]
                        
                        # Fill cloud area
                        ax_ich.fill_between(common_idx, cloud_a, cloud_b, 
                                          where=(cloud_a >= cloud_b), 
                                          alpha=0.3, color='green', label='Bullish Cloud')
                        ax_ich.fill_between(common_idx, cloud_a, cloud_b, 
                                          where=(cloud_a < cloud_b), 
                                          alpha=0.3, color='red', label='Bearish Cloud')
                        
                        # Plot cloud lines
                        ax_ich.plot(common_idx, cloud_a, linewidth=1, color='green', alpha=0.5, linestyle='--')
                        ax_ich.plot(common_idx, cloud_b, linewidth=1, color='red', alpha=0.5, linestyle='--')
                
                # Plot Chikou Span
                chikou_valid = chikou_span.dropna()
                if len(chikou_valid) > 0:
                    ax_ich.plot(chikou_valid.index, chikou_valid.values, 
                              label='Chikou Span (26)', linewidth=1, color='purple', alpha=0.6)
                
                ax_ich.set_title(f"{ticker_input} - Ichimoku Cloud Chart", fontsize=14, fontweight='bold')
                ax_ich.set_ylabel("Price ($)", fontsize=12)
                ax_ich.set_xlabel("Date", fontsize=12)
                ax_ich.legend(loc='best', fontsize=9)
                ax_ich.grid(True, alpha=0.3, linestyle='--')
                
                ax_ich.xaxis.set_major_locator(MonthLocator(interval=2))
                ax_ich.xaxis.set_major_formatter(DateFormatter('%Y-%m'))
                plt_ich.xticks(rotation=45, ha='right')
                plt_ich.tight_layout()
                st.pyplot(fig_ich)
                
                # Ichimoku signals analysis
                col_ich1, col_ich2, col_ich3, col_ich4 = st.columns(4)
                
                with col_ich1:
                    if current_tenkan:
                        tenkan_signal = "✅ Above" if current_price > current_tenkan else "❌ Below"
                        st.metric("Tenkan-sen", f"${current_tenkan:.2f}", delta=tenkan_signal)
                    else:
                        st.metric("Tenkan-sen", "N/A")
                
                with col_ich2:
                    if current_kijun:
                        kijun_signal = "✅ Above" if current_price > current_kijun else "❌ Below"
                        st.metric("Kijun-sen", f"${current_kijun:.2f}", delta=kijun_signal)
                    else:
                        st.metric("Kijun-sen", "N/A")
                
                with col_ich3:
                    if current_senkou_a and current_senkou_b:
                        cloud_color = "🟢 Bullish" if current_senkou_a > current_senkou_b else "🔴 Bearish"
                        price_above_cloud = current_price > max(current_senkou_a, current_senkou_b)
                        cloud_signal = "✅ Above" if price_above_cloud else "❌ Below"
                        st.metric("Cloud", cloud_color, delta=cloud_signal)
                    else:
                        st.metric("Cloud", "N/A")
                
                with col_ich4:
                    if current_tenkan and current_kijun:
                        tk_cross = "🟢 Bullish" if current_tenkan > current_kijun else "🔴 Bearish"
                        st.metric("TK Cross", tk_cross)
                    else:
                        st.metric("TK Cross", "N/A")
                
                # Ichimoku trading signals
                ichimoku_signals = []
                
                if current_price and current_tenkan and current_kijun:
                    # Signal 1: Price above/below cloud
                    if current_senkou_a and current_senkou_b:
                        cloud_top = max(current_senkou_a, current_senkou_b)
                        cloud_bottom = min(current_senkou_a, current_senkou_b)
                        if current_price > cloud_top:
                            ichimoku_signals.append("✅ Price above cloud - Bullish")
                        elif current_price < cloud_bottom:
                            ichimoku_signals.append("❌ Price below cloud - Bearish")
                        else:
                            ichimoku_signals.append("⚠️ Price in cloud - Neutral")
                    
                    # Signal 2: Tenkan/Kijun cross
                    if current_tenkan > current_kijun:
                        ichimoku_signals.append("✅ Tenkan > Kijun - Bullish cross")
                    else:
                        ichimoku_signals.append("❌ Tenkan < Kijun - Bearish cross")
                    
                    # Signal 3: Cloud color
                    if current_senkou_a and current_senkou_b:
                        if current_senkou_a > current_senkou_b:
                            ichimoku_signals.append("✅ Bullish cloud (green)")
                        else:
                            ichimoku_signals.append("❌ Bearish cloud (red)")
                
                if ichimoku_signals:
                    st.markdown("### 📊 Ichimoku Signals")
                    for signal in ichimoku_signals:
                        st.markdown(f"<p style='color: #075985; margin: 0.75rem 0;'>{signal}</p>", unsafe_allow_html=True)
                
                st.divider()
                
                # ========== RULE 2: TREND CONFIRMATION ==========
                st.markdown("## 📈 Rule 2: Simple Moving Averages (SMA Order)")
                st.markdown("**Correct SMA Order Interpretation for Buy/Sell Signals**")
                st.markdown("---")
                
                # Calculate moving averages
                ma20 = hist["Close"].rolling(window=20).mean()
                ma50 = hist["Close"].rolling(window=50).mean()
                ma200 = hist["Close"].rolling(window=200).mean()
                
                # Current values
                current_ma20 = ma20.iloc[-1]
                current_ma50 = ma50.iloc[-1]
                current_ma200 = ma200.iloc[-1] if len(ma200.dropna()) > 0 else None
                
                # Check SMA Order for Buy/Sell signal
                bullish_structure = False
                bearish_structure = False
                
                if current_ma200:
                    # Bullish: Price > 20 DMA > 50 DMA > 200 DMA
                    bullish_structure = (current_price > current_ma20 > current_ma50 > current_ma200)
                    # Bearish: Price < 20 DMA < 50 DMA < 200 DMA
                    bearish_structure = (current_price < current_ma20 < current_ma50 < current_ma200)
                else:
                    # If 200 MA not available, check with available MAs
                    bullish_structure = (current_price > current_ma20 > current_ma50)
                    bearish_structure = (current_price < current_ma20 < current_ma50)
                
                # Display Buy/Sell Indicator
                col_signal = st.columns(1)[0]
                with col_signal:
                    if bullish_structure:
                        st.success("🟢 **BUY SIGNAL** - Bullish Structure: Price > 20 DMA > 50 DMA > 200 DMA")
                        st.info("✅ Strong uptrend | Institutions accumulating | Pullbacks to 20 or 50 DMA = buy-the-dip")
                    elif bearish_structure:
                        st.error("🔴 **SELL / AVOID SIGNAL** - Bearish Structure: Price < 20 DMA < 50 DMA < 200 DMA")
                        st.warning("❌ Downtrend | Capital preservation zone | Avoid buying")
                    else:
                        st.warning("⚠️ **MIXED SIGNAL** - SMA order not aligned | Wait for clearer structure")
                
                st.divider()
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Current Price", f"${current_price:.2f}")
                
                with col2:
                    ma20_status = "✅ Above" if current_price > current_ma20 else "❌ Below"
                    ma20_order = "✅" if (current_ma200 and current_ma20 > current_ma50 > current_ma200) or (not current_ma200 and current_ma20 > current_ma50) else "❌"
                    st.metric("20-Day MA", f"${current_ma20:.2f}", delta=f"{ma20_status} | Order: {ma20_order}")
                
                with col3:
                    ma50_status = "✅ Above" if current_price > current_ma50 else "❌ Below"
                    ma50_order = "✅" if (current_ma200 and current_ma50 > current_ma200) else ("✅" if not current_ma200 else "❌")
                    st.metric("50-Day MA", f"${current_ma50:.2f}", delta=f"{ma50_status} | Order: {ma50_order}")
                
                with col4:
                    if current_ma200:
                        ma200_status = "✅ Above" if current_price > current_ma200 else "❌ Below"
                        st.metric("200-Day MA", f"${current_ma200:.2f}", delta=ma200_status)
                    else:
                        st.metric("200-Day MA", "N/A (Need 200+ days)")
                
                # Plot with moving averages
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots(figsize=(14, 6))
                
                # Plot price
                ax.plot(hist.index, hist["Close"], label="Price", linewidth=2.5, color='#3b82f6', zorder=3)
                
                # Plot MAs only where they have valid data (not NaN)
                # Plot 200-Day MA first (behind others) so it's more visible
                ma200_valid = ma200.dropna()
                if len(ma200_valid) > 0:
                    ax.plot(ma200_valid.index, ma200_valid.values, label="200-Day MA", 
                           linewidth=3.5, color='#ff0000', alpha=0.95, linestyle='-', zorder=1)
                
                # 20-Day MA - starts after 20 days
                ma20_valid = ma20.dropna()
                if len(ma20_valid) > 0:
                    ax.plot(ma20_valid.index, ma20_valid.values, label="20-Day MA", linewidth=2.0, color='blue', alpha=0.8, zorder=2)
                
                # 50-Day MA - starts after 50 days
                ma50_valid = ma50.dropna()
                if len(ma50_valid) > 0:
                    ax.plot(ma50_valid.index, ma50_valid.values, label="50-Day MA", linewidth=2.0, color='orange', alpha=0.8, zorder=2)
                
                
                # Highlight current price
                ax.axhline(y=current_price, color='green', linestyle='--', linewidth=2, label='Current Price', alpha=0.8)
                
                ax.set_title(f"{ticker_input} - Price vs Moving Averages", fontsize=14, fontweight='bold')
                ax.set_ylabel("Price ($)", fontsize=12)
                ax.set_xlabel("Date", fontsize=12)
                
                # Enhanced legend with better visibility for 200-Day MA
                legend = ax.legend(loc='best', fontsize=11, framealpha=0.95)
                # Make 200-Day MA label bold in legend
                for text in legend.get_texts():
                    if '200-Day MA' in text.get_text():
                        text.set_fontweight('bold')
                        text.set_fontsize(12)
                
                ax.grid(True, alpha=0.3, linestyle='--')
                
                # Add informational note about 200-Day MA if data is limited
                if len(ma200_valid) > 0 and len(ma200_valid) < len(hist) * 0.6:
                    ax.text(0.02, 0.02, f"ℹ️ 200-Day MA shown for last {len(ma200_valid)} days (requires 200+ days of data)",
                           transform=ax.transAxes, fontsize=9, verticalalignment='bottom',
                           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8, edgecolor='orange'))
                
                # Format x-axis dates better
                from matplotlib.dates import DateFormatter, MonthLocator
                ax.xaxis.set_major_locator(MonthLocator(interval=2))
                ax.xaxis.set_major_formatter(DateFormatter('%Y-%m'))
                plt.xticks(rotation=45, ha='right')
                
                plt.tight_layout()
                st.pyplot(fig)
                
                # Rule 2 Assessment - Correct SMA Order Logic
                rule2_score = 0
                rule2_reasons = []
                
                # Check 1: Price > 20 DMA
                if current_price > current_ma20:
                    rule2_score += 1
                    rule2_reasons.append("✅ Price > 20 DMA")
                else:
                    rule2_reasons.append("❌ Price < 20 DMA")
                
                # Check 2: 20 DMA > 50 DMA
                if current_ma20 > current_ma50:
                    rule2_score += 1
                    rule2_reasons.append("✅ 20 DMA > 50 DMA")
                else:
                    rule2_reasons.append("❌ 20 DMA < 50 DMA")
                
                # Check 3: 50 DMA > 200 DMA (if available)
                if current_ma200:
                    if current_ma50 > current_ma200:
                        rule2_score += 1
                        rule2_reasons.append("✅ 50 DMA > 200 DMA")
                    else:
                        rule2_reasons.append("❌ 50 DMA < 200 DMA")
                else:
                    rule2_reasons.append("⚠️ 200 DMA not available (need 200+ days)")
                
                # Check 4: Complete Bullish Structure (Price > 20 > 50 > 200)
                if current_ma200:
                    if bullish_structure:
                        rule2_score += 1
                        rule2_reasons.append("✅ Complete Bullish Structure: Price > 20 > 50 > 200")
                    else:
                        rule2_reasons.append("❌ Not in complete bullish structure")
                else:
                    if current_price > current_ma20 > current_ma50:
                        rule2_score += 1
                        rule2_reasons.append("✅ Partial Bullish Structure: Price > 20 > 50")
                    else:
                        rule2_reasons.append("❌ Not in bullish structure")
                
                # Final Assessment
                if bullish_structure:
                    st.success(f"✅ **Rule 2 PASSED** ({rule2_score}/4 criteria met) - 🟢 BUY SIGNAL")
                    st.info("**Best Entry:** Buy near 20 or 50 DMA on pullbacks, not when price is extended. "
                           "Combine with rising volume, tight price action, and market trend confirmation.")
                elif bearish_structure:
                    st.error(f"❌ **Rule 2 FAILED** ({rule2_score}/4 criteria met) - 🔴 SELL/AVOID SIGNAL")
                    st.warning("**Action:** Avoid buying. This is a downtrend - capital preservation zone.")
                elif rule2_score >= 3:
                    st.warning(f"⚠️ **Rule 2 PARTIAL** ({rule2_score}/4 criteria met) - Mixed signals")
                    st.info("**Action:** Wait for clearer structure. Some MAs aligned but not complete.")
                else:
                    st.error(f"❌ **Rule 2 FAILED** ({rule2_score}/4 criteria met) - No clear uptrend")
                    st.info("**Action:** Wait for proper SMA order alignment before considering entry.")
                
                for reason in rule2_reasons:
                    st.markdown(f"<p style='color: #075985; margin: 0.5rem 0;'>{reason}</p>", unsafe_allow_html=True)
                
                st.divider()
                
                # ========== RULE 3: STRUCTURE ==========
                st.markdown("## 🏗️ Rule 3: Structure Analysis")
                st.markdown("**Wait for base / range / U-shape**")
                st.markdown("---")
                
                # Configurable lookback period for structure analysis
                st.markdown("**Structure Analysis Period Filter:**")
                structure_options = {
                    30: "30 days: Quick bases, swing trading, very active stocks",
                    60: "60 days: Recommended default for most stocks",
                    90: "90 days: Slower-moving stocks, longer consolidations",
                    120: "120 days: Very long-term structures, major bases",
                    180: "180 days: Very long-term structures, major bases"
                }
                
                selected_days = st.selectbox(
                    "Select analysis period:",
                    options=list(structure_options.keys()),
                    format_func=lambda x: structure_options[x],
                    index=1,  # Default to 60 days (index 1 in the list)
                    help="Choose the lookback period for structure analysis. "
                         "60 days is recommended as the default for most stocks."
                )
                
                structure_days = selected_days
                
                # Show selected option info
                st.info(f"📊 **Selected:** {structure_options[structure_days]} - Analyzing last {structure_days} days")
                
                # Calculate support and resistance levels
                recent_data = hist["Close"].tail(structure_days)  # Configurable lookback period
                support_level = recent_data.min()
                resistance_level = recent_data.max()
                price_range = resistance_level - support_level
                range_percent = (price_range / support_level) * 100
                
                # Detect consolidation/base pattern
                # A base is typically: price consolidates in a range for extended period
                volatility = recent_data.pct_change().std()
                avg_volatility = hist["Close"].pct_change().std()
                
                # U-shape detection: look for V-shaped recovery pattern
                # Check if price dropped then recovered
                mid_point = len(recent_data) // 2
                first_half_low = recent_data.iloc[:mid_point].min()
                second_half_high = recent_data.iloc[mid_point:].max()
                ushape_score = 0
                
                if first_half_low < recent_data.iloc[0] * 0.95:  # Price dropped
                    if second_half_high > first_half_low * 1.05:  # Then recovered
                        ushape_score = 1
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Support Level", f"${support_level:.2f}")
                
                with col2:
                    st.metric("Resistance Level", f"${resistance_level:.2f}")
                
                with col3:
                    st.metric("Price Range", f"{range_percent:.1f}%")
                
                with col4:
                    st.metric("Current Volatility", f"{volatility*100:.2f}%")
                
                # Plot structure analysis
                import matplotlib.pyplot as plt_struct
                fig2, ax2 = plt_struct.subplots(figsize=(14, 6))
                
                ax2.plot(recent_data.index, recent_data.values, label="Price", linewidth=2, color='#3b82f6')
                ax2.axhline(y=support_level, color='green', linestyle='--', linewidth=2, label='Support', alpha=0.7)
                ax2.axhline(y=resistance_level, color='red', linestyle='--', linewidth=2, label='Resistance', alpha=0.7)
                ax2.fill_between(recent_data.index, support_level, resistance_level, alpha=0.1, color='gray', label='Range')
                
                ax2.set_title(f"{ticker_input} - Structure Analysis (Last {structure_days} Days)")
                ax2.set_ylabel("Price ($)")
                ax2.set_xlabel("Date")
                ax2.legend()
                ax2.grid(True, alpha=0.3)
                plt_struct.xticks(rotation=45)
                plt_struct.tight_layout()
                st.pyplot(fig2)
                
                # Rule 3 Assessment
                rule3_score = 0
                rule3_reasons = []
                
                # Base/Range detection - adjust threshold based on lookback period
                # Longer periods naturally have wider ranges, so adjust threshold
                if structure_days <= 60:
                    range_threshold = 15  # 15% for short/medium term
                elif structure_days <= 90:
                    range_threshold = 20  # 20% for medium-long term
                else:
                    range_threshold = 25  # 25% for long term
                
                if range_percent < range_threshold:  # Tight range suggests consolidation
                    rule3_score += 1
                    rule3_reasons.append(f"✅ Tight range ({range_percent:.1f}%) - Possible base formation")
                else:
                    rule3_reasons.append(f"⚠️ Wide range ({range_percent:.1f}%) - Less consolidation (threshold: {range_threshold}%)")
                
                # Volatility contraction (base formation)
                if volatility < avg_volatility * 0.8:
                    rule3_score += 1
                    rule3_reasons.append("✅ Volatility contraction - Base forming")
                else:
                    rule3_reasons.append("⚠️ High volatility - No clear base")
                
                # U-shape detection
                if ushape_score > 0:
                    rule3_score += 1
                    rule3_reasons.append("✅ U-shape pattern detected - Recovery from low")
                else:
                    rule3_reasons.append("⚠️ No clear U-shape pattern")
                
                # Price near support (good entry point)
                price_from_support = ((current_price - support_level) / support_level) * 100
                if 0 < price_from_support < 5:
                    rule3_score += 1
                    rule3_reasons.append(f"✅ Price near support ({price_from_support:.1f}%) - Good entry zone")
                else:
                    rule3_reasons.append(f"⚠️ Price {price_from_support:.1f}% from support")
                
                if rule3_score >= 3:
                    st.success(f"✅ **Rule 3 PASSED** ({rule3_score}/4 criteria met) - Good structure")
                elif rule3_score >= 2:
                    st.warning(f"⚠️ **Rule 3 PARTIAL** ({rule3_score}/4 criteria met) - Developing structure")
                else:
                    st.error(f"❌ **Rule 3 FAILED** ({rule3_score}/4 criteria met) - Poor structure")
                
                for reason in rule3_reasons:
                    st.markdown(f"<p style='color: #075985; margin: 0.5rem 0;'>{reason}</p>", unsafe_allow_html=True)
                
                st.divider()
                
                # ========== VOLATILITY CONTRACTION PATTERN ==========
                st.markdown("## 📉 Volatility Contraction Pattern")
                st.markdown("**Detect volatility squeeze patterns - low volatility often precedes big moves**")
                st.markdown("---")
                
                # Calculate volatility over different periods
                volatility_20 = hist["Close"].pct_change().rolling(window=20).std() * np.sqrt(252)
                volatility_50 = hist["Close"].pct_change().rolling(window=50).std() * np.sqrt(252)
                volatility_100 = hist["Close"].pct_change().rolling(window=100).std() * np.sqrt(252)
                
                # Current volatility values
                current_vol_20 = volatility_20.iloc[-1] if not pd.isna(volatility_20.iloc[-1]) else None
                current_vol_50 = volatility_50.iloc[-1] if not pd.isna(volatility_50.iloc[-1]) else None
                current_vol_100 = volatility_100.iloc[-1] if not pd.isna(volatility_100.iloc[-1]) else None
                
                # Detect volatility contraction
                vol_contraction_detected = False
                vol_expansion_detected = False
                
                if current_vol_20 and current_vol_50 and current_vol_100:
                    # Contraction: shorter-term volatility < longer-term volatility
                    if current_vol_20 < current_vol_50 < current_vol_100:
                        vol_contraction_detected = True
                    # Expansion: shorter-term volatility > longer-term volatility
                    elif current_vol_20 > current_vol_50 > current_vol_100:
                        vol_expansion_detected = True
                
                # Plot volatility contraction chart
                import matplotlib.pyplot as plt_vol
                fig_vol, ax_vol = plt_vol.subplots(figsize=(14, 6))
                
                # Plot price on top subplot
                ax_vol_price = ax_vol.twinx()
                ax_vol_price.plot(hist.index, hist["Close"], label="Price", linewidth=1.5, color='#3b82f6', alpha=0.6)
                ax_vol_price.set_ylabel("Price ($)", color='#3b82f6', fontsize=11)
                ax_vol_price.tick_params(axis='y', labelcolor='#3b82f6')
                
                # Plot volatility bands
                vol_20_valid = volatility_20.dropna()
                vol_50_valid = volatility_50.dropna()
                vol_100_valid = volatility_100.dropna()
                
                if len(vol_20_valid) > 0:
                    ax_vol.plot(vol_20_valid.index, vol_20_valid.values * 100, 
                               label='20-Day Volatility', linewidth=2, color='blue', alpha=0.8)
                if len(vol_50_valid) > 0:
                    ax_vol.plot(vol_50_valid.index, vol_50_valid.values * 100, 
                               label='50-Day Volatility', linewidth=2, color='orange', alpha=0.8)
                if len(vol_100_valid) > 0:
                    ax_vol.plot(vol_100_valid.index, vol_100_valid.values * 100, 
                               label='100-Day Volatility', linewidth=2, color='red', alpha=0.8)
                
                # Highlight contraction zones
                if len(vol_20_valid) > 0 and len(vol_50_valid) > 0:
                    common_idx = vol_20_valid.index.intersection(vol_50_valid.index)
                    if len(common_idx) > 0:
                        vol_20_common = vol_20_valid.loc[common_idx]
                        vol_50_common = vol_50_valid.loc[common_idx]
                        contraction_zones = vol_20_common < vol_50_common
                        if contraction_zones.sum() > 0:
                            ax_vol.fill_between(common_idx, 0, 
                                              np.maximum(vol_20_common, vol_50_common) * 100,
                                              where=contraction_zones, alpha=0.2, color='green', 
                                              label='Contraction Zone')
                
                ax_vol.set_title(f"{ticker_input} - Volatility Contraction Pattern Analysis", 
                               fontsize=14, fontweight='bold')
                ax_vol.set_ylabel("Volatility (%)", fontsize=12)
                ax_vol.set_xlabel("Date", fontsize=12)
                ax_vol.legend(loc='upper left', fontsize=10)
                ax_vol.grid(True, alpha=0.3)
                
                from matplotlib.dates import DateFormatter, MonthLocator
                ax_vol.xaxis.set_major_locator(MonthLocator(interval=2))
                ax_vol.xaxis.set_major_formatter(DateFormatter('%Y-%m'))
                plt_vol.xticks(rotation=45, ha='right')
                plt_vol.tight_layout()
                st.pyplot(fig_vol)
                
                # Volatility contraction analysis
                col_vol1, col_vol2, col_vol3, col_vol4 = st.columns(4)
                
                with col_vol1:
                    if current_vol_20:
                        st.metric("20-Day Volatility", f"{current_vol_20*100:.2f}%")
                    else:
                        st.metric("20-Day Volatility", "N/A")
                
                with col_vol2:
                    if current_vol_50:
                        st.metric("50-Day Volatility", f"{current_vol_50*100:.2f}%")
                    else:
                        st.metric("50-Day Volatility", "N/A")
                
                with col_vol3:
                    if current_vol_100:
                        st.metric("100-Day Volatility", f"{current_vol_100*100:.2f}%")
                    else:
                        st.metric("100-Day Volatility", "N/A")
                
                with col_vol4:
                    if vol_contraction_detected:
                        st.success("🟢 Volatility Contraction")
                        st.info("Low volatility - potential breakout coming")
                    elif vol_expansion_detected:
                        st.warning("🔴 Volatility Expansion")
                        st.info("High volatility - increased price movement")
                    else:
                        st.info("⚠️ Mixed Volatility")
                
                # Volatility contraction signals
                vol_signals = []
                if current_vol_20 and current_vol_50 and current_vol_100:
                    if vol_contraction_detected:
                        vol_signals.append("✅ **VOLATILITY CONTRACTION DETECTED** - 20-Day < 50-Day < 100-Day")
                        vol_signals.append("📊 **Signal:** Low volatility squeeze - watch for breakout")
                        vol_signals.append("💡 **Action:** Prepare for potential big move (up or down)")
                    elif vol_expansion_detected:
                        vol_signals.append("⚠️ **VOLATILITY EXPANSION** - 20-Day > 50-Day > 100-Day")
                        vol_signals.append("📊 **Signal:** High volatility - active price movement")
                    else:
                        vol_signals.append("⚠️ **MIXED VOLATILITY** - No clear contraction pattern")
                
                if vol_signals:
                    st.markdown("### 📊 Volatility Pattern Signals")
                    for signal in vol_signals:
                        st.markdown(f"<p style='color: #075985; margin: 0.75rem 0;'>{signal}</p>", unsafe_allow_html=True)
                
                st.divider()
                
                # ========== NICOLAS DARVAS BOX PATTERN ==========
                st.markdown("## 📦 Nicolas Darvas Box Pattern")
                st.markdown("**Detect box patterns - price consolidates in a box, then breaks out**")
                st.markdown("---")
                
                # Nicolas Darvas Box Pattern Detection
                # A box is defined as: price trades within a tight range (support/resistance)
                # Then breaks out above resistance (buy signal) or below support (sell signal)
                
                # Calculate box parameters
                box_period = min(structure_days, 60)  # Use shorter period for box detection
                box_data = hist["Close"].tail(box_period)
                
                # Find box boundaries (support and resistance)
                box_high = box_data.max()
                box_low = box_data.min()
                box_range = box_high - box_low
                box_range_pct = (box_range / box_low) * 100
                
                # Box quality: tighter range = better box
                box_quality = "Excellent" if box_range_pct < 10 else ("Good" if box_range_pct < 15 else "Fair")
                
                # Detect if price is in box or has broken out
                current_price_box = hist["Close"].iloc[-1]
                price_in_box = box_low <= current_price_box <= box_high
                
                # Breakout detection
                breakout_up = current_price_box > box_high * 1.01  # 1% above resistance
                breakout_down = current_price_box < box_low * 0.99  # 1% below support
                
                # Volume confirmation (if available)
                try:
                    volume_data = hist["Volume"].tail(box_period)
                    avg_volume = volume_data.mean()
                    recent_volume = volume_data.tail(5).mean()
                    volume_confirmation = recent_volume > avg_volume * 1.2  # 20% above average
                except:
                    volume_confirmation = None
                
                # Plot Darvas Box Pattern
                import matplotlib.pyplot as plt_darvas
                fig_darvas, ax_darvas = plt_darvas.subplots(figsize=(14, 7))
                
                # Plot price
                ax_darvas.plot(box_data.index, box_data.values, label="Price", linewidth=2, color='#3b82f6')
                
                # Draw box boundaries
                ax_darvas.axhline(y=box_high, color='red', linestyle='--', linewidth=2.5, 
                                 label=f'Box Top (Resistance): ${box_high:.2f}', alpha=0.8)
                ax_darvas.axhline(y=box_low, color='green', linestyle='--', linewidth=2.5, 
                                 label=f'Box Bottom (Support): ${box_low:.2f}', alpha=0.8)
                
                # Fill box area
                ax_darvas.fill_between(box_data.index, box_low, box_high, alpha=0.15, 
                                      color='gray', label='Box Range')
                
                # Highlight current price
                ax_darvas.axhline(y=current_price_box, color='blue', linestyle=':', linewidth=2, 
                                 label=f'Current Price: ${current_price_box:.2f}', alpha=0.9)
                
                # Mark breakout zones
                if breakout_up:
                    ax_darvas.fill_between(box_data.index, box_high, box_high * 1.05, 
                                          alpha=0.2, color='green', label='Breakout Zone (Up)')
                    ax_darvas.text(box_data.index[-1], current_price_box, '↑ BREAKOUT UP', 
                                  fontsize=12, color='green', fontweight='bold', 
                                  bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
                elif breakout_down:
                    ax_darvas.fill_between(box_data.index, box_low * 0.95, box_low, 
                                          alpha=0.2, color='red', label='Breakout Zone (Down)')
                    ax_darvas.text(box_data.index[-1], current_price_box, '↓ BREAKOUT DOWN', 
                                  fontsize=12, color='red', fontweight='bold',
                                  bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.7))
                elif price_in_box:
                    ax_darvas.text(box_data.index[len(box_data)//2], (box_high + box_low) / 2, 
                                  'IN BOX', fontsize=14, color='blue', fontweight='bold',
                                  ha='center', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
                
                ax_darvas.set_title(f"{ticker_input} - Nicolas Darvas Box Pattern Analysis", 
                                   fontsize=14, fontweight='bold')
                ax_darvas.set_ylabel("Price ($)", fontsize=12)
                ax_darvas.set_xlabel("Date", fontsize=12)
                ax_darvas.legend(loc='best', fontsize=10)
                ax_darvas.grid(True, alpha=0.3)
                
                ax_darvas.xaxis.set_major_locator(MonthLocator(interval=1))
                ax_darvas.xaxis.set_major_formatter(DateFormatter('%Y-%m'))
                plt_darvas.xticks(rotation=45, ha='right')
                plt_darvas.tight_layout()
                st.pyplot(fig_darvas)
                
                # Darvas Box Analysis
                col_darvas1, col_darvas2, col_darvas3, col_darvas4 = st.columns(4)
                
                with col_darvas1:
                    st.metric("Box Top (Resistance)", f"${box_high:.2f}")
                
                with col_darvas2:
                    st.metric("Box Bottom (Support)", f"${box_low:.2f}")
                
                with col_darvas3:
                    st.metric("Box Range", f"{box_range_pct:.1f}%")
                
                with col_darvas4:
                    st.metric("Box Quality", box_quality)
                
                # Darvas Box Signals
                darvas_signals = []
                
                if price_in_box:
                    darvas_signals.append("📦 **PRICE IN BOX** - Consolidation phase")
                    darvas_signals.append(f"✅ Box Quality: **{box_quality}** ({box_range_pct:.1f}% range)")
                    darvas_signals.append("💡 **Action:** Wait for breakout above ${:.2f} (buy) or below ${:.2f} (avoid)".format(box_high, box_low))
                elif breakout_up:
                    darvas_signals.append("🟢 **BREAKOUT UP DETECTED** - Price broke above box top")
                    darvas_signals.append(f"✅ Breakout level: ${box_high:.2f}")
                    if volume_confirmation:
                        darvas_signals.append("✅ **Volume Confirmation:** High volume supports breakout")
                    darvas_signals.append("💡 **Action:** BUY SIGNAL - Enter on breakout with stop below box")
                elif breakout_down:
                    darvas_signals.append("🔴 **BREAKOUT DOWN DETECTED** - Price broke below box bottom")
                    darvas_signals.append(f"❌ Breakdown level: ${box_low:.2f}")
                    darvas_signals.append("💡 **Action:** SELL/AVOID SIGNAL - Price breaking down")
                else:
                    darvas_signals.append("⚠️ **UNCLEAR BOX PATTERN** - Price near box boundaries")
                
                # Darvas Box Rules
                darvas_signals.append("")
                darvas_signals.append("**Nicolas Darvas Box Rules:**")
                darvas_signals.append("1. ✅ Buy when price breaks above box top with volume")
                darvas_signals.append("2. ✅ Set stop loss below box bottom")
                darvas_signals.append("3. ✅ Target: Box height added to breakout point")
                darvas_signals.append("4. ❌ Avoid buying inside the box")
                darvas_signals.append("5. ❌ Avoid if box range > 20% (too wide)")
                
                st.markdown("### 📊 Darvas Box Pattern Signals")
                for signal in darvas_signals:
                    st.markdown(f"<p style='color: #075985; margin: 0.75rem 0;'>{signal}</p>", unsafe_allow_html=True)
                
                st.divider()
                
                # ========== OVERALL ASSESSMENT ==========
                st.markdown("## 🎯 Overall Trading Rules Assessment")
                st.markdown("---")
                
                total_score = rule1_score + rule2_score + rule3_score
                max_score = 13  # 5 + 4 + 4 (Rule 1 now has 5 criteria)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Rule 1 (Fundamentals)", f"{rule1_score}/5", 
                             delta="✅" if rule1_score >= 4 else "⚠️" if rule1_score >= 2 else "❌")
                
                with col2:
                    st.metric("Rule 2 (Trend)", f"{rule2_score}/4",
                             delta="✅" if rule2_score >= 3 else "⚠️")
                
                with col3:
                    st.metric("Rule 3 (Structure)", f"{rule3_score}/4",
                             delta="✅" if rule3_score >= 3 else "⚠️")
                
                overall_percentage = (total_score / max_score) * 100
                
                if overall_percentage >= 75:
                    st.success(f"🎯 **STRONG BUY SIGNAL** - {total_score}/{max_score} criteria met ({overall_percentage:.0f}%)")
                    st.info("All three rules show positive signals. Consider this a high-quality setup.")
                elif overall_percentage >= 60:
                    st.warning(f"⚠️ **MODERATE SIGNAL** - {total_score}/{max_score} criteria met ({overall_percentage:.0f}%)")
                    st.info("Some rules are met but not all. Proceed with caution.")
                else:
                    st.error(f"❌ **WEAK SIGNAL** - {total_score}/{max_score} criteria met ({overall_percentage:.0f}%)")
                    st.info("Most rules are not met. Wait for better setup.")
                
        except Exception as e:
            st.error(f"Error analyzing trading rules: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# Enhanced Footer
st.markdown("---")
st.markdown("""
<div style="background: #f8fafc; padding: 2rem; border-radius: 12px; text-align: center; margin-top: 3rem;">
    <p style="color: #64748b; margin: 0; font-size: 0.875rem;">
        ⚠️ <strong>Educational / Research Use Only</strong> - Not for actual trading
    </p>
    <p style="color: #94a3b8; margin: 0.5rem 0 0 0; font-size: 0.75rem;">
        Portfolio Quant Trading System v1.0.0 | © 2026
    </p>
</div>
""", unsafe_allow_html=True)
