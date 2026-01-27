import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import yaml
import json
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
    page_title="Nashor Portfolio Quant Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Nashor Portfolio Quant Trading System - Institutional-grade trading platform"
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

def get_currency_symbol(ticker):
    """Get currency symbol based on ticker market"""
    if ticker.endswith('.NS') or ticker.endswith('.BO'):
        return '₹'  # Indian Rupee
    else:
        return '$'  # US Dollar

def format_currency(amount, ticker, decimals=2):
    """Format amount with appropriate currency symbol"""
    symbol = get_currency_symbol(ticker)
    if decimals == 0:
        return f"{symbol}{amount:,.0f}"
    else:
        return f"{symbol}{amount:,.2f}"

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
            max_total_dd=config.get("max_total_dd", 0.12),
            max_var=config.get("max_var", -0.05)
        )
        st.session_state.approval = TradeApproval(
            mode=config.get("approval_mode", "SEMI"),
            enable_compliance=config.get("enable_compliance_logging", True)
        )
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
        <h1 style="font-size: 1.75rem; margin: 0; color: #075985; font-weight: 700;">📈 Nashor Portfolio Quant</h1>
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
                max_total_dd=max_total_dd,
                max_var=config.get("max_var", -0.05)
            )
            st.session_state.approval = TradeApproval(
                mode=approval_mode,
                enable_compliance=config.get("enable_compliance_logging", True)
            )
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
        <p>© 2026 Nashor Portfolio Quant</p>
    </div>
    """, unsafe_allow_html=True)

# Main content - Enhanced Header - Light Blue Theme
st.markdown("""
<div style="background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%); padding: 2rem; border-radius: 12px; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(59, 130, 246, 0.2);">
    <h1 style="color: white; margin: 0; font-size: 2.5rem; font-weight: 700;">📈 Nashor Portfolio Quant Trading System</h1>
    <p style="color: rgba(255, 255, 255, 0.95); margin: 0.5rem 0 0 0; font-size: 1.1rem;">Institutional-grade trading platform with advanced risk management and analytics</p>
</div>
""", unsafe_allow_html=True)

# Tabs with enhanced styling - ensure all text is visible
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Dashboard", 
    "💰 Trade Management", 
    "⚠️ Risk Monitor", 
    "🔄 Reconciliation", 
    "📋 Trading Rules",
    "🏛️ Institutional Strategy"
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
            
            # Analysis Period Guidelines
            with st.expander("📚 Analysis Period Guidelines", expanded=False):
                st.markdown("""
                <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; border-left: 4px solid #3b82f6;">
                    <h5 style="color: #075985; margin-top: 0; margin-bottom: 0.75rem;">Recommended Periods by Trading Style</h5>
                    <table style="width: 100%; font-size: 0.875rem; color: #0369a1;">
                        <tr style="border-bottom: 1px solid #e2e8f0;">
                            <td style="padding: 0.5rem 0;"><strong>Day Trading</strong></td>
                            <td style="text-align: right;">30 - 60 days</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e2e8f0;">
                            <td style="padding: 0.5rem 0;"><strong>Swing Trading</strong> ✅</td>
                            <td style="text-align: right;">90 days (default)</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e2e8f0;">
                            <td style="padding: 0.5rem 0;"><strong>Position Trading</strong></td>
                            <td style="text-align: right;">180 - 252 days</td>
                        </tr>
                        <tr>
                            <td style="padding: 0.5rem 0;"><strong>Long-Term Investing</strong></td>
                            <td style="text-align: right;">365 days</td>
                        </tr>
                    </table>
                    <p style="font-size: 0.8rem; color: #64748b; margin: 0.75rem 0 0 0;">
                        <strong>Institutional Standard:</strong> 90 days for weekly/monthly reviews<br>
                        <strong>Your Setting:</strong> {} days - {} for most trading scenarios
                    </p>
                </div>
                """.format(
                    days,
                    "✅ Optimal" if days == 90 else "Good" if 60 <= days <= 180 else "Consider adjusting"
                ), unsafe_allow_html=True)
        
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
                            <p style="margin: 0.5rem 0;"><strong>Starting Price:</strong> {}</p>
                            <p style="margin: 0.5rem 0;"><strong>Ending Price:</strong> {}</p>
                            <p style="margin: 0.5rem 0;"><strong>Highest Price:</strong> {}</p>
                            <p style="margin: 0.5rem 0;"><strong>Lowest Price:</strong> {}</p>
                        </div>
                        """.format(
                            f"{get_currency_symbol(ticker)}{equity.iloc[0]:,.2f}",
                            f"{get_currency_symbol(ticker)}{equity.iloc[-1]:,.2f}",
                            f"{get_currency_symbol(ticker)}{equity.max():,.2f}",
                            f"{get_currency_symbol(ticker)}{equity.min():,.2f}"
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
    
    # ========== POSITIONS / HOLDINGS VIEW ==========
    st.markdown("### 📊 Current Positions & Holdings")
    st.markdown("**View average price and quantity for your positions**")
    st.markdown("---")
    
    # Load executed trades from compliance log
    positions = {}
    compliance_log_file = "compliance_log.json"
    
    if os.path.exists(compliance_log_file):
        try:
            with open(compliance_log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            if entry.get('symbol') and entry.get('side') and entry.get('quantity') and entry.get('price'):
                                symbol = entry['symbol']
                                side = entry['side']
                                qty = entry['quantity']
                                price = entry['price']
                                timestamp = entry.get('timestamp', '')
                                
                                if symbol not in positions:
                                    positions[symbol] = {
                                        'buys': [],
                                        'sells': [],
                                        'total_bought': 0,
                                        'total_sold': 0,
                                        'total_cost': 0.0,
                                        'total_proceeds': 0.0
                                    }
                                
                                if side.upper() == 'BUY':
                                    positions[symbol]['buys'].append({
                                        'qty': qty,
                                        'price': price,
                                        'timestamp': timestamp
                                    })
                                    positions[symbol]['total_bought'] += qty
                                    positions[symbol]['total_cost'] += qty * price
                                elif side.upper() == 'SELL':
                                    positions[symbol]['sells'].append({
                                        'qty': qty,
                                        'price': price,
                                        'timestamp': timestamp
                                    })
                                    positions[symbol]['total_sold'] += qty
                                    positions[symbol]['total_proceeds'] += qty * price
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            st.warning(f"⚠️ Could not read compliance log: {str(e)}")
    
    # Calculate net positions
    net_positions = {}
    for symbol, data in positions.items():
        net_qty = data['total_bought'] - data['total_sold']
        if net_qty > 0:  # Only show positions with net long
            avg_price = data['total_cost'] / data['total_bought'] if data['total_bought'] > 0 else 0
            net_positions[symbol] = {
                'net_quantity': net_qty,
                'average_price': avg_price,
                'total_cost': data['total_cost'],
                'total_proceeds': data['total_proceeds'],
                'num_buys': len(data['buys']),
                'num_sells': len(data['sells']),
                'buys': data['buys'],
                'sells': data['sells']
            }
    
    if net_positions:
        st.success(f"✅ Found {len(net_positions)} active position(s)")
        
        # Display positions summary
        col_pos1, col_pos2 = st.columns([2, 1])
        
        with col_pos1:
            st.markdown("#### 📈 Position Summary")
            positions_data = []
            for symbol, pos in net_positions.items():
                # Get current price if available
                current_price = None
                try:
                    stock = yf.Ticker(symbol)
                    hist = stock.history(period="1d")
                    if not hist.empty:
                        current_price = hist["Close"].iloc[-1]
                except:
                    pass
                
                unrealized_pnl = (current_price - pos['average_price']) * pos['net_quantity'] if current_price else None
                unrealized_pnl_pct = ((current_price / pos['average_price']) - 1) * 100 if current_price and pos['average_price'] > 0 else None
                
                currency_symbol = get_currency_symbol(symbol)
                positions_data.append({
                    'Symbol': symbol,
                    'Quantity': pos['net_quantity'],
                    'Avg Price': f"{currency_symbol}{pos['average_price']:.2f}",
                    'Total Cost': f"{currency_symbol}{pos['total_cost']:,.2f}",
                    'Current Price': f"{currency_symbol}{current_price:.2f}" if current_price else "N/A",
                    'Unrealized P&L': f"{currency_symbol}{unrealized_pnl:,.2f}" if unrealized_pnl is not None else "N/A",
                    'P&L %': f"{unrealized_pnl_pct:.2f}%" if unrealized_pnl_pct is not None else "N/A",
                    'Buy Count': pos['num_buys']
                })
            
            positions_df = pd.DataFrame(positions_data)
            st.dataframe(positions_df.style.format({
                'Quantity': '{:.0f}',
                'Buy Count': '{:.0f}'
            }), use_container_width=True, height=300)
        
        with col_pos2:
            st.markdown("#### 📊 Quick Stats")
            total_cost = sum(pos['total_cost'] for pos in net_positions.values())
            total_qty = sum(pos['net_quantity'] for pos in net_positions.values())
            overall_avg = total_cost / sum(pos['total_bought'] for pos in net_positions.values()) if sum(pos['total_bought'] for pos in net_positions.values()) > 0 else 0
            
            st.metric("Total Positions", len(net_positions))
            st.metric("Total Quantity", f"{total_qty:.0f}")
            # Use dollar for mixed portfolios, or detect from first position
            first_symbol = list(net_positions.keys())[0] if net_positions else "USD"
            currency_symbol = get_currency_symbol(first_symbol)
            st.metric("Total Cost", f"{currency_symbol}{total_cost:,.2f}")
            st.metric("Overall Avg Price", f"{currency_symbol}{overall_avg:.2f}")
        
        # Detailed view for selected symbol
        st.markdown("---")
        st.markdown("#### 🔍 Detailed Position History")
        
        selected_symbol = st.selectbox(
            "Select Symbol to View Details",
            options=list(net_positions.keys()),
            key="position_detail_symbol"
        )
        
        if selected_symbol:
            pos = net_positions[selected_symbol]
            
            col_det1, col_det2 = st.columns(2)
            
            with col_det1:
                st.markdown(f"**{selected_symbol} - Buy History**")
                if pos['buys']:
                    buys_df = pd.DataFrame(pos['buys'])
                    buys_df.columns = ['Quantity', 'Price', 'Timestamp']
                    buys_df['Cost'] = buys_df['Quantity'] * buys_df['Price']
                    buys_df['Timestamp'] = pd.to_datetime(buys_df['Timestamp']).dt.strftime('%Y-%m-%d %H:%M')
                    currency_symbol = get_currency_symbol(selected_symbol)
                    st.dataframe(buys_df.style.format({
                        'Quantity': '{:.0f}',
                        'Price': f'{currency_symbol}{{:.2f}}',
                        'Cost': f'{currency_symbol}{{:.2f}}'
                    }), use_container_width=True)
                    
                    st.info(f"📊 **Average Buy Price:** {currency_symbol}{pos['average_price']:.2f} | **Total Bought:** {pos['total_bought']:.0f} shares")
                else:
                    st.info("No buy history")
            
            with col_det2:
                st.markdown(f"**{selected_symbol} - Sell History**")
                if pos['sells']:
                    sells_df = pd.DataFrame(pos['sells'])
                    sells_df.columns = ['Quantity', 'Price', 'Timestamp']
                    sells_df['Proceeds'] = sells_df['Quantity'] * sells_df['Price']
                    sells_df['Timestamp'] = pd.to_datetime(sells_df['Timestamp']).dt.strftime('%Y-%m-%d %H:%M')
                    currency_symbol = get_currency_symbol(selected_symbol)
                    st.dataframe(sells_df.style.format({
                        'Quantity': '{:.0f}',
                        'Price': f'{currency_symbol}{{:.2f}}',
                        'Proceeds': f'{currency_symbol}{{:.2f}}'
                    }), use_container_width=True)
                    
                    st.info(f"💰 **Total Sold:** {pos['total_sold']:.0f} shares | **Total Proceeds:** {currency_symbol}{pos['total_proceeds']:,.2f}")
                else:
                    st.info("No sell history")
            
            # Position summary
            st.markdown("---")
            col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
            currency_symbol = get_currency_symbol(selected_symbol)
            with col_sum1:
                st.metric("Net Quantity", f"{pos['net_quantity']:.0f}")
            with col_sum2:
                st.metric("Average Price", f"{currency_symbol}{pos['average_price']:.2f}")
            with col_sum3:
                st.metric("Total Cost", f"{currency_symbol}{pos['total_cost']:,.2f}")
            with col_sum4:
                try:
                    current_price = yf.Ticker(selected_symbol).history(period='1d')['Close'].iloc[-1]
                    current_value = pos['net_quantity'] * current_price
                except:
                    current_value = pos['net_quantity'] * pos['average_price']
                st.metric("Current Value", f"{currency_symbol}{current_value:,.2f}")
    else:
        st.info("ℹ️ No positions found. Execute some BUY trades to see positions here.")
        st.markdown("""
        <div style="background: #f0f9ff; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #60a5fa; margin-top: 1rem;">
            <p style="color: #075985; margin: 0; font-weight: 600;">💡 How to track positions:</p>
            <ul style="color: #0369a1; margin: 0.5rem 0 0 1.5rem;">
                <li>Submit BUY trades through the Trade Management section</li>
                <li>Approved trades are automatically logged to compliance_log.json</li>
                <li>Positions are calculated from executed trades</li>
                <li>Average price is calculated as weighted average of all buys</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
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
                        # Compliance logging is handled in approval.approve() method
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
                            # Log to compliance system
                            from monitoring.compliance import ComplianceLogger
                            compliance_logger = ComplianceLogger()
                            compliance_logger.log_trade(
                                symbol=trade['symbol'],
                                side=trade['side'],
                                qty=trade['quantity'],
                                price=trade['price'],
                                reason=f"Approved via {st.session_state.config.get('approval_mode', 'SEMI')} mode"
                            )
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
    
    # Drawdown Rules & Guidelines
    with st.expander("📚 Drawdown Limits - Rules & Guidelines", expanded=False):
        st.markdown("""
        <div style="background: #f8fafc; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #3b82f6;">
            <h4 style="color: #075985; margin-top: 0;">Industry Standards & Recommendations</h4>
        </div>
        """, unsafe_allow_html=True)
        
        col_rules1, col_rules2 = st.columns(2)
        
        with col_rules1:
            st.markdown("""
            <div style="background: #ffffff; padding: 1rem; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 1rem;">
                <h5 style="color: #075985; margin-top: 0; margin-bottom: 0.75rem;">📊 Daily Drawdown Limits</h5>
                <table style="width: 100%; font-size: 0.875rem; color: #0369a1;">
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 0.5rem 0;"><strong>Conservative</strong></td>
                        <td style="text-align: right;">1.0% - 2.0%</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 0.5rem 0;"><strong>Moderate</strong> ✅</td>
                        <td style="text-align: right;">2.0% - 3.0%</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 0.5rem 0;"><strong>Aggressive</strong></td>
                        <td style="text-align: right;">3.0% - 5.0%</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem 0;"><strong>Your Setting</strong></td>
                        <td style="text-align: right; font-weight: 700; color: #075985;">{}</td>
                    </tr>
                </table>
                <p style="font-size: 0.8rem; color: #64748b; margin: 0.75rem 0 0 0;">
                    <strong>Industry Standard:</strong> 1.5% - 3.0% for prop trading firms
                </p>
            </div>
            """.format(f"{st.session_state.config.get('max_daily_dd', 0.03):.1%}"), unsafe_allow_html=True)
        
        with col_rules2:
            st.markdown("""
            <div style="background: #ffffff; padding: 1rem; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 1rem;">
                <h5 style="color: #075985; margin-top: 0; margin-bottom: 0.75rem;">📈 Total Drawdown Limits</h5>
                <table style="width: 100%; font-size: 0.875rem; color: #0369a1;">
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 0.5rem 0;"><strong>Conservative</strong></td>
                        <td style="text-align: right;">5% - 8%</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 0.5rem 0;"><strong>Moderate</strong> ✅</td>
                        <td style="text-align: right;">8% - 12%</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 0.5rem 0;"><strong>Aggressive</strong></td>
                        <td style="text-align: right;">12% - 20%</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem 0;"><strong>Your Setting</strong></td>
                        <td style="text-align: right; font-weight: 700; color: #075985;">{}</td>
                    </tr>
                </table>
                <p style="font-size: 0.8rem; color: #64748b; margin: 0.75rem 0 0 0;">
                    <strong>Industry Standard:</strong> 8% - 12% for most trading strategies
                </p>
            </div>
            """.format(f"{st.session_state.config.get('max_total_dd', 0.12):.1%}"), unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: #f0f9ff; padding: 1rem; border-radius: 8px; border-left: 4px solid #60a5fa; margin-top: 1rem;">
            <h5 style="color: #075985; margin-top: 0; margin-bottom: 0.75rem;">💡 Recommendations by Trading Style</h5>
            <ul style="color: #0369a1; margin: 0; padding-left: 1.5rem; font-size: 0.875rem;">
                <li><strong>Conservative/Institutional:</strong> 1.5% daily / 8% total</li>
                <li><strong>Moderate/Balanced:</strong> 3.0% daily / 12% total ✅ <em>Your current setting</em></li>
                <li><strong>Aggressive/Day Trading:</strong> 5.0% daily / 20% total</li>
            </ul>
            <p style="color: #64748b; font-size: 0.8rem; margin: 0.75rem 0 0 0;">
                <strong>Note:</strong> Your current settings (3% / 12%) align with prop trading firm standards and are appropriate for most professional trading scenarios.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
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
        
        # Institutional features: VaR/CVaR and Stress Testing
        if config.get("enable_compliance_logging", True):
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 📈 Advanced Risk Metrics")
            st.markdown("---")
            
            returns = equity_series.pct_change().dropna()
            if len(returns) > 0:
                col_var1, col_var2, col_var3 = st.columns(3)
                
                with col_var1:
                    var_95 = st.session_state.risk_manager.get_var(level=0.05)
                    if var_95 is not None:
                        st.metric("VaR (95%)", f"{var_95:.2%}", 
                                 delta=f"Limit: {config.get('max_var', -0.05):.2%}" if var_95 < config.get('max_var', -0.05) else None,
                                 delta_color="inverse")
                    else:
                        st.metric("VaR (95%)", "N/A")
                
                with col_var2:
                    cvar_95 = st.session_state.risk_manager.get_cvar(level=0.05)
                    if cvar_95 is not None:
                        st.metric("CVaR (95%)", f"{cvar_95:.2%}")
                    else:
                        st.metric("CVaR (95%)", "N/A")
                
                with col_var3:
                    max_var_config = config.get("max_var", -0.05)
                    st.metric("Max VaR Limit", f"{max_var_config:.2%}")
                
                # Stress Testing Section
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 🧪 Stress Testing")
                st.markdown("---")
                
                stress_col1, stress_col2 = st.columns(2)
                
                with stress_col1:
                    st.markdown("**Historical Worst Case Scenario**")
                    historical_stress = st.session_state.risk_manager.stress_test()
                    if historical_stress is not None:
                        stress_equity = historical_stress.iloc[-1] if hasattr(historical_stress, 'iloc') else historical_stress[-1]
                        current_equity = equity_series.iloc[-1]
                        stress_loss = (current_equity - stress_equity) / current_equity if current_equity > 0 else 0
                        equity_ticker = st.session_state.equity_data.get('ticker', 'USD') if hasattr(st.session_state, 'equity_data') else 'USD'
                        currency_symbol = get_currency_symbol(equity_ticker)
                        st.metric("Projected Equity", f"{currency_symbol}{stress_equity:,.2f}", 
                                 delta=f"{stress_loss:.2%} loss", delta_color="inverse")
                
                with stress_col2:
                    st.markdown("**Custom Shock Scenario**")
                    shock_pct = st.number_input("Shock Percentage", min_value=-0.50, max_value=0.50, 
                                                value=-0.10, step=0.01, format="%.2f", key="stress_shock")
                    if st.button("Run Stress Test", key="run_stress"):
                        custom_stress = st.session_state.risk_manager.stress_test(shock_pct=shock_pct)
                        if custom_stress is not None:
                            stress_equity = custom_stress.iloc[-1] if hasattr(custom_stress, 'iloc') else custom_stress[-1]
                            current_equity = equity_series.iloc[-1]
                            stress_loss = (current_equity - stress_equity) / current_equity if current_equity > 0 else 0
                            equity_ticker = st.session_state.equity_data.get('ticker', 'USD') if hasattr(st.session_state, 'equity_data') else 'USD'
                            currency_symbol = get_currency_symbol(equity_ticker)
                            st.metric("Projected Equity", f"{currency_symbol}{stress_equity:,.2f}", 
                                     delta=f"{stress_loss:.2%} loss", delta_color="inverse")
        
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
                currency_symbol = get_currency_symbol(ticker_input)
                ax_ha.set_ylabel(f"Price ({currency_symbol})", fontsize=13, color='#d1d4dc')
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
                currency_symbol = get_currency_symbol(ticker_input)
                col_sma1, col_sma2, col_sma3, col_sma4 = st.columns(4)
                with col_sma1:
                    current_ha_price = ha_close.iloc[-1]
                    st.metric("Current HA Price", f"{currency_symbol}{current_ha_price:.2f}")
                with col_sma2:
                    if len(ha_sma50_valid) > 0:
                        sma50_val = ha_sma50_valid.iloc[-1]
                        sma50_diff = ((current_ha_price - sma50_val) / sma50_val) * 100
                        st.metric("SMA 50", f"{currency_symbol}{sma50_val:.2f}", 
                                delta=f"{sma50_diff:+.2f}%", delta_color="normal")
                    else:
                        st.metric("SMA 50", "N/A")
                with col_sma3:
                    if len(ha_sma100_valid) > 0:
                        sma100_val = ha_sma100_valid.iloc[-1]
                        sma100_diff = ((current_ha_price - sma100_val) / sma100_val) * 100
                        st.metric("SMA 100", f"{currency_symbol}{sma100_val:.2f}", 
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
                currency_symbol = get_currency_symbol(ticker_input)
                ax_ich.set_ylabel(f"Price ({currency_symbol})", fontsize=12)
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
                        currency_symbol = get_currency_symbol(ticker_input)
                        st.metric("Tenkan-sen", f"{currency_symbol}{current_tenkan:.2f}", delta=tenkan_signal)
                    else:
                        st.metric("Tenkan-sen", "N/A")
                
                with col_ich2:
                    if current_kijun:
                        kijun_signal = "✅ Above" if current_price > current_kijun else "❌ Below"
                        st.metric("Kijun-sen", f"{currency_symbol}{current_kijun:.2f}", delta=kijun_signal)
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
                
                currency_symbol = get_currency_symbol(ticker_input)
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Current Price", f"{currency_symbol}{current_price:.2f}")
                
                with col2:
                    ma20_status = "✅ Above" if current_price > current_ma20 else "❌ Below"
                    ma20_order = "✅" if (current_ma200 and current_ma20 > current_ma50 > current_ma200) or (not current_ma200 and current_ma20 > current_ma50) else "❌"
                    st.metric("20-Day MA", f"{currency_symbol}{current_ma20:.2f}", delta=f"{ma20_status} | Order: {ma20_order}")
                
                with col3:
                    ma50_status = "✅ Above" if current_price > current_ma50 else "❌ Below"
                    ma50_order = "✅" if (current_ma200 and current_ma50 > current_ma200) else ("✅" if not current_ma200 else "❌")
                    st.metric("50-Day MA", f"{currency_symbol}{current_ma50:.2f}", delta=f"{ma50_status} | Order: {ma50_order}")
                
                with col4:
                    if current_ma200:
                        ma200_status = "✅ Above" if current_price > current_ma200 else "❌ Below"
                        st.metric("200-Day MA", f"{currency_symbol}{current_ma200:.2f}", delta=ma200_status)
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
                currency_symbol = get_currency_symbol(ticker_input)
                ax.set_ylabel(f"Price ({currency_symbol})", fontsize=12)
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
                
                col_struct1, col_struct2 = st.columns([2, 1])
                
                with col_struct1:
                    selected_days = st.selectbox(
                        "Select analysis period:",
                        options=list(structure_options.keys()),
                        format_func=lambda x: structure_options[x],
                        index=1,  # Default to 60 days (index 1 in the list)
                        help="Choose the lookback period for structure analysis. "
                             "60 days is recommended as the default for most stocks."
                    )
                
                with col_struct2:
                    with st.expander("📚 Structure Period Rules", expanded=False):
                        st.markdown("""
                        <div style="background: #f8fafc; padding: 0.75rem; border-radius: 6px; font-size: 0.8rem;">
                            <p style="color: #0369a1; margin: 0.25rem 0;"><strong>30 days:</strong> Day trading</p>
                            <p style="color: #0369a1; margin: 0.25rem 0;"><strong>60 days:</strong> Swing trading ✅</p>
                            <p style="color: #0369a1; margin: 0.25rem 0;"><strong>90-120 days:</strong> Position trading</p>
                            <p style="color: #0369a1; margin: 0.25rem 0;"><strong>180 days:</strong> Long-term</p>
                            <p style="color: #64748b; margin: 0.5rem 0 0 0; font-size: 0.75rem;">
                                <strong>Note:</strong> Thresholds adjust automatically (15% for ≤60 days, 20% for ≤90 days, 25% for >90 days)
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                
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
                    currency_symbol = get_currency_symbol(ticker_input)
                    st.metric("Support Level", f"{currency_symbol}{support_level:.2f}")
                
                with col2:
                    st.metric("Resistance Level", f"{currency_symbol}{resistance_level:.2f}")
                
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
                currency_symbol = get_currency_symbol(ticker_input)
                ax2.set_ylabel(f"Price ({currency_symbol})")
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
                currency_symbol = get_currency_symbol(ticker_input)
                ax_vol_price.set_ylabel(f"Price ({currency_symbol})", color='#3b82f6', fontsize=11)
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
                currency_symbol = get_currency_symbol(ticker_input)
                ax_darvas.axhline(y=current_price_box, color='blue', linestyle=':', linewidth=2, 
                                 label=f'Current Price: {currency_symbol}{current_price_box:.2f}', alpha=0.9)
                
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
                currency_symbol = get_currency_symbol(ticker_input)
                ax_darvas.set_ylabel(f"Price ({currency_symbol})", fontsize=12)
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
                    currency_symbol = get_currency_symbol(ticker_input)
                    st.metric("Box Top (Resistance)", f"{currency_symbol}{box_high:.2f}")
                
                with col_darvas2:
                    st.metric("Box Bottom (Support)", f"{currency_symbol}{box_low:.2f}")
                
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

with tab6:
    st.markdown("## 🏛️ Institutional Strategy Engine")
    st.markdown("**Advanced execution, allocation, and risk management tools**")
    st.markdown("---")
    
    # ========== INSTITUTIONAL STRATEGY ANALYZER ==========
    st.markdown("### 🎯 Strategy Analyzer & Recommendations")
    st.markdown("**Generate buy/sell recommendations based on technical analysis and position P&L**")
    st.markdown("---")
    
    # Load existing positions
    positions = {}
    compliance_log_file = "compliance_log.json"
    if os.path.exists(compliance_log_file):
        try:
            with open(compliance_log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            if entry.get('symbol') and entry.get('side') and entry.get('quantity') and entry.get('price'):
                                symbol = entry['symbol']
                                side = entry['side']
                                qty = entry['quantity']
                                price = entry['price']
                                timestamp = entry.get('timestamp', '')
                                
                                if symbol not in positions:
                                    positions[symbol] = {'buys': [], 'sells': [], 'total_bought': 0, 'total_sold': 0, 'total_cost': 0.0}
                                
                                if side.upper() == 'BUY':
                                    positions[symbol]['buys'].append({'qty': qty, 'price': price, 'timestamp': timestamp})
                                    positions[symbol]['total_bought'] += qty
                                    positions[symbol]['total_cost'] += qty * price
                                elif side.upper() == 'SELL':
                                    positions[symbol]['sells'].append({'qty': qty, 'price': price, 'timestamp': timestamp})
                                    positions[symbol]['total_sold'] += qty
                        except json.JSONDecodeError:
                            continue
        except:
            pass
    
    # Calculate net positions
    net_positions = {}
    for symbol, data in positions.items():
        net_qty = data['total_bought'] - data['total_sold']
        if net_qty > 0:
            avg_price = data['total_cost'] / data['total_bought'] if data['total_bought'] > 0 else 0
            net_positions[symbol] = {
                'net_quantity': net_qty,
                'average_price': avg_price,
                'total_cost': data['total_cost']
            }
    
    # Strategy mode selection
    strategy_mode = st.radio(
        "**Select Analysis Mode:**",
        ["📊 Existing Position (Old Ticker)", "🆕 New Ticker"],
        horizontal=True,
        key="strategy_mode"
    )
    
    ticker_input = None
    position_data = None
    
    if strategy_mode == "📊 Existing Position (Old Ticker)":
        # Option to use existing positions or manual input
        input_method = st.radio(
            "**Input Method:**",
            ["📋 Load from Positions", "✏️ Manual Entry"],
            horizontal=True,
            key="position_input_method"
        )
        
        if input_method == "📋 Load from Positions":
            if net_positions:
                selected_position = st.selectbox(
                    "Select Position to Analyze",
                    options=list(net_positions.keys()),
                    key="selected_position"
                )
                ticker_input = selected_position
                position_data = net_positions[selected_position]
                
                currency_symbol = get_currency_symbol(ticker_input)
                col_pos_info1, col_pos_info2, col_pos_info3, col_pos_info4 = st.columns(4)
                with col_pos_info1:
                    st.metric("Current Quantity", f"{position_data['net_quantity']:.0f}")
                with col_pos_info2:
                    st.metric("Average Price", f"{currency_symbol}{position_data['average_price']:.2f}")
                with col_pos_info3:
                    st.metric("Total Cost", f"{currency_symbol}{position_data['total_cost']:,.2f}")
                with col_pos_info4:
                    try:
                        current_price = yf.Ticker(ticker_input).history(period="1d")["Close"].iloc[-1]
                        unrealized_pnl = (current_price - position_data['average_price']) * position_data['net_quantity']
                        unrealized_pnl_pct = ((current_price / position_data['average_price']) - 1) * 100
                        st.metric("Unrealized P&L", f"{currency_symbol}{unrealized_pnl:,.2f}", 
                                 delta=f"{unrealized_pnl_pct:.2f}%", 
                                 delta_color="normal" if unrealized_pnl >= 0 else "inverse")
                    except:
                        st.metric("Unrealized P&L", "N/A")
            else:
                st.warning("⚠️ No existing positions found. Use 'Manual Entry' option or execute some BUY trades first.")
                ticker_input = None
                position_data = None
        else:
            # Manual Entry Option
            st.markdown("#### ✏️ Manual Position Entry")
            st.info("💡 Enter your position details manually for trench analysis")
            
            col_manual1, col_manual2, col_manual3 = st.columns(3)
            
            with col_manual1:
                ticker_input = st.text_input(
                    "Ticker Symbol",
                    value="AAPL",
                    placeholder="e.g., AAPL, MSFT, JIOFIN.NS",
                    key="manual_ticker"
                )
            
            with col_manual2:
                manual_avg_price = st.number_input(
                    "Average Entry Price",
                    min_value=0.01,
                    value=150.0,
                    step=0.01,
                    format="%.2f",
                    key="manual_avg_price"
                )
            
            with col_manual3:
                manual_quantity = st.number_input(
                    "Total Quantity",
                    min_value=1,
                    value=100,
                    step=10,
                    key="manual_quantity"
                )
            
            if ticker_input:
                try:
                    # Get current price to calculate P&L
                    stock_temp = yf.Ticker(ticker_input)
                    hist_temp = stock_temp.history(period="1d")
                    if not hist_temp.empty:
                        current_price_temp = hist_temp["Close"].iloc[-1]
                        total_cost = manual_avg_price * manual_quantity
                        unrealized_pnl_temp = (current_price_temp - manual_avg_price) * manual_quantity
                        unrealized_pnl_pct_temp = ((current_price_temp / manual_avg_price) - 1) * 100
                        
                        currency_symbol_manual = get_currency_symbol(ticker_input)
                        col_manual_info1, col_manual_info2, col_manual_info3, col_manual_info4 = st.columns(4)
                        with col_manual_info1:
                            st.metric("Quantity", f"{manual_quantity:.0f}")
                        with col_manual_info2:
                            st.metric("Average Price", f"{currency_symbol_manual}{manual_avg_price:.2f}")
                        with col_manual_info3:
                            st.metric("Total Cost", f"{currency_symbol_manual}{total_cost:,.2f}")
                        with col_manual_info4:
                            st.metric("Current Price", f"{currency_symbol_manual}{current_price_temp:.2f}", 
                                     delta=f"{unrealized_pnl_pct_temp:.2f}%",
                                     delta_color="normal" if unrealized_pnl_temp >= 0 else "inverse")
                        
                        # Create position_data structure
                        position_data = {
                            'net_quantity': manual_quantity,
                            'average_price': manual_avg_price,
                            'total_cost': total_cost
                        }
                    else:
                        st.error("Could not fetch current price for this ticker")
                        position_data = None
                except Exception as e:
                    st.error(f"Error fetching data: {str(e)}")
                    position_data = None
            else:
                position_data = None
    else:
        ticker_input = st.text_input(
            "Enter Ticker Symbol",
            value="AAPL",
            placeholder="e.g., AAPL, MSFT, JIOFIN.NS",
            key="new_ticker_strategy"
        )
    
    if ticker_input and st.button("🔍 Analyze & Generate Strategy", type="primary", use_container_width=True):
        try:
            with st.spinner("Analyzing ticker and generating strategy..."):
                stock = yf.Ticker(ticker_input)
                hist = stock.history(period="1y")
                
                if hist.empty:
                    st.error("No data available for this ticker")
                else:
                    current_price = hist["Close"].iloc[-1]
                    
                    # ========== TECHNICAL ANALYSIS ==========
                    st.markdown("---")
                    st.markdown("### 📊 Technical Analysis Summary")
                    
                    # Calculate moving averages
                    ma20 = hist["Close"].rolling(window=20).mean()
                    ma50 = hist["Close"].rolling(window=50).mean()
                    ma200 = hist["Close"].rolling(window=200).mean()
                    
                    current_ma20 = ma20.iloc[-1] if not pd.isna(ma20.iloc[-1]) else None
                    current_ma50 = ma50.iloc[-1] if not pd.isna(ma50.iloc[-1]) else None
                    current_ma200 = ma200.iloc[-1] if not pd.isna(ma200.iloc[-1]) else None
                    
                    # SMA Order Analysis
                    bullish_structure = False
                    bearish_structure = False
                    if current_ma200:
                        bullish_structure = (current_price > current_ma20 > current_ma50 > current_ma200)
                        bearish_structure = (current_price < current_ma20 < current_ma50 < current_ma200)
                    else:
                        bullish_structure = (current_price > current_ma20 > current_ma50) if current_ma20 and current_ma50 else False
                        bearish_structure = (current_price < current_ma20 < current_ma50) if current_ma20 and current_ma50 else False
                    
                    # Calculate ATR for trench spacing
                    high_low = hist['High'] - hist['Low']
                    high_close = np.abs(hist['High'] - hist['Close'].shift())
                    low_close = np.abs(hist['Low'] - hist['Close'].shift())
                    ranges = pd.concat([high_low, high_close, low_close], axis=1)
                    true_range = ranges.max(axis=1)
                    atr = true_range.rolling(window=14).mean().iloc[-1]
                    
                    # Calculate volatility and risk metrics
                    returns = hist["Close"].pct_change().dropna()
                    volatility = returns.std() * np.sqrt(252) * 100
                    
                    # Calculate VaR/CVaR for risk-based sizing
                    from core.portfolio_var_cvar import PortfolioRisk
                    portfolio_risk = PortfolioRisk(returns)
                    var_95 = portfolio_risk.var(level=0.05)
                    cvar_95 = portfolio_risk.cvar(level=0.05)
                    
                    # Calculate portfolio-level metrics
                    total_portfolio_value = sum(pos['total_cost'] for pos in net_positions.values())
                    if position_data:
                        current_position_value = position_data['total_cost']
                        position_weight = current_position_value / total_portfolio_value if total_portfolio_value > 0 else 0
                    else:
                        position_weight = 0
                    
                    # Calculate correlation with existing positions
                    correlations = {}
                    if len(net_positions) > 0 and ticker_input:
                        try:
                            ticker_returns = returns
                            for other_symbol, other_pos in net_positions.items():
                                if other_symbol != ticker_input:
                                    try:
                                        other_stock = yf.Ticker(other_symbol)
                                        other_hist = other_stock.history(period="1y")
                                        if not other_hist.empty:
                                            other_returns = other_hist["Close"].pct_change().dropna()
                                            # Align dates
                                            common_dates = ticker_returns.index.intersection(other_returns.index)
                                            if len(common_dates) > 20:
                                                corr = ticker_returns.loc[common_dates].corr(other_returns.loc[common_dates])
                                                correlations[other_symbol] = corr if not pd.isna(corr) else 0
                                    except:
                                        correlations[other_symbol] = 0
                        except:
                            pass
                    
                    avg_correlation = np.mean(list(correlations.values())) if correlations else 0
                    
                    # Overall signal score
                    signal_score = 0
                    signal_reasons = []
                    
                    if bullish_structure:
                        signal_score += 3
                        signal_reasons.append("✅ Strong bullish SMA structure (Price > 20 > 50 > 200)")
                    elif bearish_structure:
                        signal_score -= 3
                        signal_reasons.append("❌ Bearish SMA structure - downtrend")
                    else:
                        signal_reasons.append("⚠️ Mixed SMA signals")
                    
                    # Price vs MAs
                    if current_price > current_ma20:
                        signal_score += 1
                        signal_reasons.append("✅ Price above 20 DMA")
                    else:
                        signal_score -= 1
                        signal_reasons.append("❌ Price below 20 DMA")
                    
                    # Risk assessment
                    risk_score = 0
                    if volatility > 40:
                        risk_score = 3  # High risk
                        signal_reasons.append("⚠️ High volatility (>40%) - reduce position size")
                    elif volatility > 25:
                        risk_score = 2  # Medium-high risk
                        signal_reasons.append("⚠️ Elevated volatility (25-40%)")
                    elif volatility < 15:
                        risk_score = 0  # Low risk
                        signal_reasons.append("✅ Low volatility (<15%) - favorable for larger positions")
                    
                    # Correlation risk
                    if avg_correlation > 0.7:
                        risk_score += 1
                        signal_reasons.append(f"⚠️ High correlation ({avg_correlation:.2f}) with existing positions - reduce size")
                    elif avg_correlation < 0.3:
                        signal_reasons.append(f"✅ Low correlation ({avg_correlation:.2f}) - good diversification")
                    
                    # ========== INSTITUTIONAL RISK CONSTANTS ==========
                    MAX_POSITION_WEIGHT = 0.15  # Max 15% per position (institutional standard)
                    MAX_CORRELATION = 0.7  # Max correlation threshold
                    MAX_VOLATILITY_FOR_LARGE_POS = 30  # Max volatility for large positions
                    
                    # ========== STRATEGY RECOMMENDATION ==========
                    st.markdown("---")
                    st.markdown("### 🎯 Strategy Recommendation")
                    
                    if position_data:
                        # EXISTING POSITION ANALYSIS
                        avg_price = position_data['average_price']
                        current_qty = position_data['net_quantity']
                        pnl_pct = ((current_price / avg_price) - 1) * 100
                        
                        currency_symbol = get_currency_symbol(ticker_input)
                        st.markdown(f"#### 📍 Position Analysis: {ticker_input}")
                        col_rec1, col_rec2, col_rec3 = st.columns(3)
                        with col_rec1:
                            st.metric("Entry Price", f"{currency_symbol}{avg_price:.2f}")
                        with col_rec2:
                            st.metric("Current Price", f"{currency_symbol}{current_price:.2f}")
                        with col_rec3:
                            pnl_amount = (current_price - avg_price) * current_qty
                            st.metric("P&L", f"{pnl_pct:.2f}%", 
                                     delta=f"{currency_symbol}{pnl_amount:,.2f}",
                                     delta_color="normal" if pnl_pct >= 0 else "inverse")
                        
                        # Recommendation logic based on P&L and signals
                        if signal_score >= 3 and pnl_pct < -5:
                            # Strong buy signal + losing position = average down
                            recommendation = "🟢 BUY MORE (Average Down)"
                            recommendation_reason = f"Strong bullish signals detected. Position is down {abs(pnl_pct):.1f}%. Consider averaging down."
                            action = "BUY"
                            urgency = "HIGH"
                        elif signal_score >= 3 and pnl_pct > 10:
                            # Strong buy signal + profitable = add to winners
                            recommendation = "🟢 BUY MORE (Add to Winners)"
                            recommendation_reason = f"Strong bullish signals + position is profitable ({pnl_pct:.1f}%). Add to winning position."
                            action = "BUY"
                            urgency = "MEDIUM"
                        elif signal_score <= -2 and pnl_pct > 5:
                            # Bearish signal + profitable = take profits
                            recommendation = "🟡 SELL PARTIAL (Take Profits)"
                            recommendation_reason = f"Bearish signals detected. Position is profitable ({pnl_pct:.1f}%). Consider taking profits."
                            action = "SELL"
                            urgency = "MEDIUM"
                        elif signal_score <= -2 and pnl_pct < -10:
                            # Bearish signal + losing = cut losses
                            recommendation = "🔴 SELL (Cut Losses)"
                            recommendation_reason = f"Bearish signals + position down {abs(pnl_pct):.1f}%. Consider cutting losses."
                            action = "SELL"
                            urgency = "HIGH"
                        elif signal_score >= 1:
                            # Mild bullish = hold or small add
                            recommendation = "🟢 HOLD / SMALL ADD"
                            recommendation_reason = "Mild bullish signals. Hold position or add small amount."
                            action = "BUY"
                            urgency = "LOW"
                        else:
                            # Neutral/negative = hold
                            recommendation = "🟡 HOLD"
                            recommendation_reason = "Mixed signals. Hold position and wait for clearer direction."
                            action = "HOLD"
                            urgency = "LOW"
                        
                        # Display recommendation
                        # Display recommendation with risk context
                        if action == "BUY":
                            st.success(f"**{recommendation}**")
                        elif action == "SELL":
                            st.error(f"**{recommendation}**")
                        else:
                            st.warning(f"**{recommendation}**")
                        
                        st.info(f"**Reason:** {recommendation_reason}")
                        
                        # Risk warnings
                        if avg_correlation > MAX_CORRELATION:
                            st.warning(f"⚠️ **High Correlation Risk:** Average correlation ({avg_correlation:.2f}) exceeds threshold ({MAX_CORRELATION}). Consider reducing position size.")
                        if volatility > MAX_VOLATILITY_FOR_LARGE_POS:
                            st.warning(f"⚠️ **High Volatility:** {volatility:.1f}% volatility suggests smaller position size.")
                        if position_weight > MAX_POSITION_WEIGHT * 0.8:
                            st.warning(f"⚠️ **Concentration Risk:** Position weight ({position_weight:.1%}) approaching limit ({MAX_POSITION_WEIGHT:.0%}).")
                        
                        # ========== INSTITUTIONAL RISK ANALYSIS ==========
                        st.markdown("---")
                        st.markdown("### ⚠️ Institutional Risk Analysis")
                        
                        col_risk1, col_risk2, col_risk3, col_risk4 = st.columns(4)
                        with col_risk1:
                            st.metric("VaR (95%)", f"{var_95:.2%}" if var_95 else "N/A")
                        with col_risk2:
                            st.metric("CVaR (95%)", f"{cvar_95:.2%}" if cvar_95 else "N/A")
                        with col_risk3:
                            st.metric("Volatility", f"{volatility:.1f}%")
                        with col_risk4:
                            st.metric("Current Position Weight", f"{position_weight:.1%}" if position_weight > 0 else "N/A")
                        
                        # Risk-based position sizing (constants already defined above)
                        if action == "BUY":
                            # Calculate risk-adjusted position size
                            # Base size on VaR and volatility
                            risk_budget = abs(var_95) if var_95 else volatility / 100
                            
                            # Adjust for volatility
                            if volatility > MAX_VOLATILITY_FOR_LARGE_POS:
                                vol_adjustment = 0.5  # Reduce size by 50% for high vol
                            elif volatility > 25:
                                vol_adjustment = 0.7  # Reduce by 30%
                            else:
                                vol_adjustment = 1.0  # Full size
                            
                            # Adjust for correlation
                            from core.correlation_adjustment import correlation_adjusted_size
                            base_add_pct = 0.20  # Base 20% add
                            corr_adjusted_pct = correlation_adjusted_size(base_add_pct, avg_correlation, MAX_CORRELATION) / base_add_pct
                            
                            # Adjust for portfolio weight limit
                            if position_weight > MAX_POSITION_WEIGHT * 0.8:  # Near limit
                                weight_adjustment = 0.5  # Reduce size
                                st.warning(f"⚠️ Position weight ({position_weight:.1%}) approaching limit ({MAX_POSITION_WEIGHT:.0%})")
                            else:
                                weight_adjustment = 1.0
                            
                            # P&L adjustment (institutional: add to winners, careful with losers)
                            if pnl_pct < -15:
                                pnl_adjustment = 0.3  # Very conservative if down >15%
                            elif pnl_pct < -10:
                                pnl_adjustment = 0.5  # Conservative if down >10%
                            elif pnl_pct > 10:
                                pnl_adjustment = 1.2  # Add more to winners
                            else:
                                pnl_adjustment = 1.0
                            
                            # Final risk-adjusted size
                            suggested_add_pct = base_add_pct * vol_adjustment * corr_adjusted_pct * weight_adjustment * pnl_adjustment
                            suggested_add_pct = min(suggested_add_pct, 0.50)  # Cap at 50%
                            suggested_add_pct = max(suggested_add_pct, 0.05)  # Minimum 5%
                            
                            suggested_qty = int(current_qty * suggested_add_pct)
                            
                            st.markdown("#### 💰 Institutional Position Sizing")
                            
                            sizing_details = pd.DataFrame({
                                'Factor': ['Base Add %', 'Volatility Adjustment', 'Correlation Adjustment', 
                                          'Portfolio Weight Adjustment', 'P&L Adjustment', 'Final Add %'],
                                'Value': [f"{base_add_pct:.0%}", f"{vol_adjustment:.2f}x", f"{corr_adjusted_pct:.2f}x",
                                         f"{weight_adjustment:.2f}x", f"{pnl_adjustment:.2f}x", f"{suggested_add_pct:.1%}"]
                            })
                            st.dataframe(sizing_details, use_container_width=True, hide_index=True)
                            
                            st.metric("Risk-Adjusted Add Quantity", f"{suggested_qty} shares", 
                                     delta=f"{suggested_add_pct*100:.1f}% of current position")
                            
                            # Risk limits check
                            new_position_value = (current_qty + suggested_qty) * current_price
                            new_position_weight = new_position_value / (total_portfolio_value + suggested_qty * current_price) if total_portfolio_value > 0 else 1.0
                            
                            if new_position_weight > MAX_POSITION_WEIGHT:
                                st.error(f"❌ **RISK LIMIT:** Adding {suggested_qty} shares would exceed {MAX_POSITION_WEIGHT:.0%} position limit (would be {new_position_weight:.1%})")
                                max_allowed_qty = int((MAX_POSITION_WEIGHT * (total_portfolio_value + current_qty * current_price) - current_qty * current_price) / current_price)
                                st.warning(f"⚠️ **Maximum allowed add:** {max_allowed_qty} shares to stay within limit")
                                suggested_qty = max(0, max_allowed_qty)
                            
                            # Stop-loss and Trailing Stop recommendations
                            stop_loss_pct = abs(var_95) * 2 if var_95 else 0.05  # 2x VaR or 5% default
                            stop_loss_price = avg_price * (1 - stop_loss_pct)
                            
                            st.markdown("#### 🛑 Risk Management")
                            
                            col_sl1, col_sl2 = st.columns(2)
                            currency_symbol = get_currency_symbol(ticker_input)
                            with col_sl1:
                                st.metric("Fixed Stop-Loss", f"{currency_symbol}{stop_loss_price:.2f}", 
                                         delta=f"{stop_loss_pct:.1%} below entry")
                            with col_sl2:
                                max_loss = current_qty * (avg_price - stop_loss_price)
                                st.metric("Maximum Risk", f"{currency_symbol}{max_loss:,.2f}")
                            
                            # ========== INSTITUTIONAL TRAILING STOP LOSS ==========
                            st.markdown("---")
                            st.markdown("##### 📈 Institutional Trailing Stop Loss Strategy")
                            st.info("💡 **Institutional Methods:** ATR-based, dynamic adjustments, break-even protection, profit target activation")
                            
                            # Calculate ATR-based trailing stops (most common institutional method)
                            atr_multipliers = [1.5, 2.0, 2.5, 3.0]  # Common institutional multipliers
                            atr_labels = ["Tight (1.5x ATR)", "Standard (2x ATR)", "Moderate (2.5x ATR)", "Wide (3x ATR)"]
                            
                            # Calculate recent high for trailing stop reference
                            recent_high_20 = hist["High"].tail(20).max()
                            recent_high_50 = hist["High"].tail(50).max()
                            
                            # Get currency symbol for this ticker
                            currency_symbol = get_currency_symbol(ticker_input)
                            
                            # Institutional trailing stop strategies
                            institutional_stops = []
                            
                            # Strategy 1: ATR-Based (Most Common)
                            for mult, label in zip(atr_multipliers, atr_labels):
                                atr_trailing = current_price - (atr * mult)
                                atr_distance_pct = (atr * mult / current_price) * 100
                                protected_profit = (atr_trailing - avg_price) * current_qty if atr_trailing > avg_price else 0
                                
                                institutional_stops.append({
                                    'Strategy': 'ATR-Based',
                                    'Type': label,
                                    'Multiplier': f"{mult:.1f}x",
                                    'Trailing Stop': f"{currency_symbol}{atr_trailing:.2f}",
                                    'Distance (ATR)': f"{currency_symbol}{atr * mult:.2f}",
                                    'Distance %': f"{atr_distance_pct:.2f}%",
                                    'Protected Profit': f"{currency_symbol}{protected_profit:,.2f}" if protected_profit > 0 else f"{currency_symbol}0.00"
                                })
                            
                            # Strategy 2: Break-Even Stop (after 5% profit)
                            profit_pct = ((current_price - avg_price) / avg_price * 100) if current_price > avg_price else 0
                            if profit_pct >= 5:
                                be_stop = avg_price  # Break-even
                                be_protected = (be_stop - avg_price) * current_qty  # Should be 0, but shows break-even protection
                                institutional_stops.append({
                                    'Strategy': 'Break-Even',
                                    'Type': 'Break-Even Stop',
                                    'Multiplier': 'N/A',
                                    'Trailing Stop': f"{currency_symbol}{be_stop:.2f}",
                                    'Distance (ATR)': f"{currency_symbol}{current_price - be_stop:.2f}",
                                    'Distance %': f"{((current_price - be_stop) / current_price * 100):.2f}%",
                                    'Protected Profit': f"{currency_symbol}{be_protected:,.2f} (Break-Even)"
                                })
                            
                            # Strategy 3: Dynamic Trailing (adjusts based on volatility regime)
                            if volatility > 35:
                                dynamic_mult = 3.0  # Wider for very high vol
                            elif volatility > 25:
                                dynamic_mult = 2.5
                            elif volatility > 15:
                                dynamic_mult = 2.0
                            else:
                                dynamic_mult = 1.5
                            
                            dynamic_trailing = current_price - (atr * dynamic_mult)
                            dynamic_distance_pct = (atr * dynamic_mult / current_price) * 100
                            dynamic_protected = (dynamic_trailing - avg_price) * current_qty if dynamic_trailing > avg_price else 0
                            
                            institutional_stops.append({
                                'Strategy': 'Dynamic (Vol-Adj)',
                                'Type': f'Vol-Adjusted ({volatility:.1f}% vol)',
                                'Multiplier': f"{dynamic_mult:.1f}x",
                                'Trailing Stop': f"{currency_symbol}{dynamic_trailing:.2f}",
                                'Distance (ATR)': f"{currency_symbol}{atr * dynamic_mult:.2f}",
                                'Distance %': f"{dynamic_distance_pct:.2f}%",
                                'Protected Profit': f"{currency_symbol}{dynamic_protected:,.2f}" if dynamic_protected > 0 else f"{currency_symbol}0.00"
                            })
                            
                            # Strategy 4: Support-Based (use recent low as trailing stop)
                            recent_low_20 = hist["Low"].tail(20).min()
                            support_trailing = recent_low_20 * 0.98  # 2% below support
                            support_distance_pct = ((current_price - support_trailing) / current_price) * 100
                            support_protected = (support_trailing - avg_price) * current_qty if support_trailing > avg_price else 0
                            
                            institutional_stops.append({
                                'Strategy': 'Support-Based',
                                'Type': 'Below 20-Day Low',
                                'Multiplier': 'N/A',
                                'Trailing Stop': f"{currency_symbol}{support_trailing:.2f}",
                                'Distance (ATR)': f"{currency_symbol}{current_price - support_trailing:.2f}",
                                'Distance %': f"{support_distance_pct:.2f}%",
                                'Protected Profit': f"{currency_symbol}{support_protected:,.2f}" if support_protected > 0 else f"{currency_symbol}0.00"
                            })
                            
                            # Strategy 5: Profit Target Activation (different stops at different profit levels)
                            if profit_pct >= 10:
                                # At 10%+ profit, use tighter trailing
                                profit_activated_trailing = current_price - (atr * 1.5)
                                profit_activated_label = "Tight (10%+ profit)"
                            elif profit_pct >= 5:
                                # At 5-10% profit, use moderate trailing
                                profit_activated_trailing = current_price - (atr * 2.0)
                                profit_activated_label = "Moderate (5-10% profit)"
                            else:
                                # Below 5% profit, use wider trailing
                                profit_activated_trailing = current_price - (atr * 2.5)
                                profit_activated_label = "Wide (<5% profit)"
                            
                            profit_activated_distance = (atr * (1.5 if profit_pct >= 10 else (2.0 if profit_pct >= 5 else 2.5)))
                            profit_activated_pct = (profit_activated_distance / current_price) * 100
                            profit_activated_protected = (profit_activated_trailing - avg_price) * current_qty if profit_activated_trailing > avg_price else 0
                            
                            currency_symbol = get_currency_symbol(ticker_input)
                            institutional_stops.append({
                                'Strategy': 'Profit-Activated',
                                'Type': profit_activated_label,
                                'Multiplier': f"{profit_activated_distance/atr:.1f}x",
                                'Trailing Stop': f"{currency_symbol}{profit_activated_trailing:.2f}",
                                'Distance (ATR)': f"{currency_symbol}{profit_activated_distance:.2f}",
                                'Distance %': f"{profit_activated_pct:.2f}%",
                                'Protected Profit': f"{currency_symbol}{profit_activated_protected:,.2f}" if profit_activated_protected > 0 else f"{currency_symbol}0.00"
                            })
                            
                            # Display all strategies
                            institutional_df = pd.DataFrame(institutional_stops)
                            st.dataframe(institutional_df, use_container_width=True, hide_index=True)
                            
                            # Recommended strategy (institutional standard: 2x ATR)
                            recommended_atr_mult = 2.0
                            recommended_trailing_price = current_price - (atr * recommended_atr_mult)
                            recommended_distance_pct = (atr * recommended_atr_mult / current_price) * 100
                            
                            st.success(f"✅ **Recommended (Institutional Standard):** 2.0x ATR Trailing Stop = {currency_symbol}{recommended_trailing_price:.2f} ({recommended_distance_pct:.2f}% below price)")
                            st.info(f"📊 **ATR (14-day):** {currency_symbol}{atr:.2f} | **Current Price:** {currency_symbol}{current_price:.2f} | **Entry Price:** {currency_symbol}{avg_price:.2f}")
                            
                            # Trailing stop progression scenarios
                            st.markdown("---")
                            st.markdown("##### 📊 Trailing Stop Progression (Institutional Method)")
                            
                            # Show how trailing stop evolves as price moves
                            if current_price > avg_price:
                                progression_prices = [
                                    current_price * 1.03,  # +3%
                                    current_price * 1.05,  # +5%
                                    current_price * 1.08,  # +8%
                                    current_price * 1.10,  # +10%
                                    current_price * 1.15,  # +15%
                                    current_price * 1.20   # +20%
                                ]
                                
                                progressions = []
                                for prog_price in progression_prices:
                                    # Trailing stop moves up maintaining 2x ATR distance
                                    prog_trailing = prog_price - (atr * recommended_atr_mult)
                                    # But never goes below break-even after 5% profit
                                    if prog_price >= avg_price * 1.05:
                                        prog_trailing = max(prog_trailing, avg_price)
                                    
                                    locked_profit = (prog_trailing - avg_price) * current_qty if prog_trailing > avg_price else 0
                                    profit_from_entry = ((prog_price - avg_price) / avg_price * 100)
                                    profit_locked = ((prog_trailing - avg_price) / avg_price * 100) if prog_trailing > avg_price else 0
                                    
                                    progressions.append({
                                        'Price Moves To': f"{currency_symbol}{prog_price:.2f}",
                                        'Trailing Stop': f"{currency_symbol}{prog_trailing:.2f}",
                                        'Profit from Entry': f"{profit_from_entry:.1f}%",
                                        'Profit Locked': f"{profit_locked:.1f}%",
                                        'Protected': f"{currency_symbol}{locked_profit:,.2f}",
                                        'Risk Remaining': f"{currency_symbol}{(prog_price - prog_trailing) * current_qty:,.2f}"
                                    })
                                
                                progression_df = pd.DataFrame(progressions)
                                st.dataframe(progression_df, use_container_width=True, hide_index=True)
                                
                                st.info("💡 **Institutional Rule:** Trailing stop moves up with price but never below break-even after 5% profit. Risk decreases as profit increases.")
                            
                            # Risk-Reward Analysis
                            st.markdown("---")
                            st.markdown("##### ⚖️ Risk-Reward Analysis")
                            
                            # Calculate potential reward targets
                            reward_targets = [0.10, 0.15, 0.20, 0.25]  # 10%, 15%, 20%, 25% profit targets
                            risk_reward_ratios = []
                            
                            for target_pct in reward_targets:
                                target_price = avg_price * (1 + target_pct)
                                risk_amount = (avg_price - recommended_trailing_price) * current_qty
                                reward_amount = (target_price - avg_price) * current_qty
                                rr_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
                                
                                risk_reward_ratios.append({
                                    'Profit Target': f"{target_pct:.0%}",
                                    'Target Price': f"{currency_symbol}{target_price:.2f}",
                                    'Risk': f"{currency_symbol}{risk_amount:,.2f}",
                                    'Reward': f"{currency_symbol}{reward_amount:,.2f}",
                                    'R:R Ratio': f"{rr_ratio:.2f}:1"
                                })
                            
                            rr_df = pd.DataFrame(risk_reward_ratios)
                            st.dataframe(rr_df, use_container_width=True, hide_index=True)
                            
                            if current_price > avg_price:
                                current_rr = ((current_price - avg_price) * current_qty) / ((avg_price - recommended_trailing_price) * current_qty) if (avg_price - recommended_trailing_price) > 0 else 0
                                st.metric("Current Risk:Reward Ratio", f"{current_rr:.2f}:1",
                                         delta="✅ Favorable" if current_rr >= 2.0 else "⚠️ Below 2:1 target")
                            
                            # Generate trench buy levels
                            from core.trench_engine import TrenchStrategyEngine
                            
                            trench_base_price = current_price
                            trench_engine = TrenchStrategyEngine(
                                avg_price=trench_base_price,
                                base_qty=suggested_qty,
                                capital=suggested_qty * current_price,
                                risk_limit=0.25
                            )
                            
                            # Generate buy trenches below current price
                            trench_multipliers = [0.5, 1.0, 1.5]  # 0.5x, 1x, 1.5x ATR below
                            trench_weights = [0.4, 0.35, 0.25]  # More weight on first trench
                            trench_engine.generate_buy_trenches(atr, trench_multipliers, trench_weights)
                            
                            st.markdown("#### 📊 Buy Trench Levels")
                            trench_df = pd.DataFrame(trench_engine.trenches, columns=["Price Level", "Quantity"])
                            trench_df["Value"] = trench_df["Price Level"] * trench_df["Quantity"]
                            trench_df["Discount %"] = ((current_price - trench_df["Price Level"]) / current_price * 100).round(2)
                            trench_df["Cumulative Qty"] = trench_df["Quantity"].cumsum()
                            trench_df["Cumulative Cost"] = trench_df["Value"].cumsum()
                            
                            currency_symbol = get_currency_symbol(ticker_input)
                            st.dataframe(trench_df.style.format({
                                "Price Level": f"{currency_symbol}{{:.2f}}",
                                "Value": f"{currency_symbol}{{:.2f}}",
                                "Discount %": "{:.2f}%",
                                "Cumulative Cost": f"{currency_symbol}{{:.2f}}"
                            }), use_container_width=True)
                            
                            st.info(f"💡 **Strategy:** Scale into position at these levels. Total additional cost: {currency_symbol}{trench_df['Cumulative Cost'].iloc[-1]:,.2f}")
                            
                        elif action == "SELL":
                            # Calculate suggested sell size
                            if pnl_pct > 10:
                                # Profitable: sell 30-50%
                                suggested_sell_pct = 0.50 if signal_score <= -3 else 0.30
                            elif pnl_pct < -10:
                                # Losing badly: sell all or most
                                suggested_sell_pct = 1.0
                            else:
                                # Small loss: sell 25%
                                suggested_sell_pct = 0.25
                            
                            suggested_sell_qty = int(current_qty * suggested_sell_pct)
                            
                            st.markdown("#### 💰 Suggested Exit Sizing")
                            st.metric("Suggested Sell Quantity", f"{suggested_sell_qty} shares",
                                     delta=f"{suggested_sell_pct*100:.0f}% of position")
                            
                            # Generate sell levels above current price
                            profit_targets = [0.05, 0.10, 0.15, 0.20]  # 5%, 10%, 15%, 20% profit
                            sell_weights = [0.25, 0.25, 0.25, 0.25]
                            
                            # Use blended price if we have multiple buys, otherwise use avg_price
                            blended_exit_price = avg_price
                            if len(position_data.get('buys', [])) > 1:
                                from core.trench_engine import TrenchStrategyEngine
                                temp_engine = TrenchStrategyEngine(avg_price, current_qty, current_qty * avg_price)
                                # Reconstruct buys as trenches for blended price
                                total_value = sum(b['qty'] * b['price'] for b in position_data.get('buys', []))
                                total_qty = sum(b['qty'] for b in position_data.get('buys', []))
                                blended_exit_price = total_value / total_qty if total_qty > 0 else avg_price
                            
                            sell_levels = [(blended_exit_price * (1 + p), int(suggested_sell_qty * w)) 
                                         for p, w in zip(profit_targets, sell_weights)]
                            
                            st.markdown("#### 📊 Sell Target Levels")
                            sell_df = pd.DataFrame(sell_levels, columns=["Target Price", "Quantity"])
                            sell_df["Profit %"] = ((sell_df["Target Price"] / blended_exit_price) - 1) * 100
                            sell_df["Proceeds"] = sell_df["Target Price"] * sell_df["Quantity"]
                            sell_df["Cumulative Qty"] = sell_df["Quantity"].cumsum()
                            sell_df["Cumulative Proceeds"] = sell_df["Proceeds"].cumsum()
                            
                            currency_symbol = get_currency_symbol(ticker_input)
                            st.dataframe(sell_df.style.format({
                                "Target Price": f"{currency_symbol}{{:.2f}}",
                                "Profit %": "{:.2f}%",
                                "Proceeds": f"{currency_symbol}{{:.2f}}",
                                "Cumulative Proceeds": f"{currency_symbol}{{:.2f}}"
                            }), use_container_width=True)
                            
                            st.info(f"💡 **Strategy:** Scale out of position at these profit targets. Total proceeds: {currency_symbol}{sell_df['Cumulative Proceeds'].iloc[-1]:,.2f}")
                    
                    else:
                        # NEW TICKER ANALYSIS
                        st.markdown(f"#### 🆕 New Ticker Analysis: {ticker_input}")
                        
                        if signal_score >= 3:
                            recommendation = "🟢 STRONG BUY"
                            recommendation_reason = "Strong bullish signals detected. Good entry opportunity."
                            action = "BUY"
                        elif signal_score >= 1:
                            recommendation = "🟡 MODERATE BUY"
                            recommendation_reason = "Mild bullish signals. Consider entry with smaller size."
                            action = "BUY"
                        elif signal_score <= -2:
                            recommendation = "🔴 AVOID / SELL SHORT"
                            recommendation_reason = "Bearish signals detected. Avoid buying or consider short."
                            action = "AVOID"
                        else:
                            recommendation = "🟡 WAIT"
                            recommendation_reason = "Mixed signals. Wait for clearer direction."
                            action = "WAIT"
                        
                        if action == "BUY":
                            st.success(f"**{recommendation}**")
                        elif action == "AVOID":
                            st.error(f"**{recommendation}**")
                        else:
                            st.warning(f"**{recommendation}**")
                        
                        st.info(f"**Reason:** {recommendation_reason}")
                        
                        if action == "BUY":
                            # Institutional-grade position sizing
                            total_portfolio_capital = st.number_input(
                                "Total Portfolio Capital",
                                min_value=1000.0,
                                value=100000.0,
                                step=10000.0,
                                format="%.2f",
                                key="total_portfolio_capital"
                            )
                            
                            # Risk-based position sizing (institutional standard)
                            MAX_POSITION_WEIGHT_NEW = 0.15  # Max 15% per position
                            
                            # Calculate risk-adjusted position size
                            # Method 1: VaR-based sizing
                            risk_budget = abs(var_95) if var_95 else volatility / 100
                            var_based_size = min(risk_budget * 10, MAX_POSITION_WEIGHT_NEW)  # Scale VaR to position %
                            
                            # Method 2: Volatility-based sizing
                            if volatility > 40:
                                vol_based_size = 0.05  # 5% for very high volatility
                            elif volatility > 30:
                                vol_based_size = 0.08  # 8% for high volatility
                            elif volatility > 20:
                                vol_based_size = 0.12  # 12% for medium volatility
                            else:
                                vol_based_size = 0.15  # 15% for low volatility
                            
                            # Method 3: Correlation-adjusted sizing
                            if avg_correlation > 0.7:
                                corr_adjustment = 0.5  # Reduce by 50% if high correlation
                            elif avg_correlation < 0.3:
                                corr_adjustment = 1.2  # Increase by 20% if low correlation
                            else:
                                corr_adjustment = 1.0
                            
                            # Take minimum of VaR-based and volatility-based (conservative)
                            base_position_pct = min(var_based_size, vol_based_size) * corr_adjustment
                            base_position_pct = min(base_position_pct, MAX_POSITION_WEIGHT_NEW)  # Cap at max
                            base_position_pct = max(base_position_pct, 0.03)  # Minimum 3%
                            
                            suggested_capital_amount = total_portfolio_capital * base_position_pct
                            suggested_qty = int(suggested_capital_amount / current_price)
                            
                            st.markdown("#### 💰 Institutional Position Sizing")
                            
                            currency_symbol = get_currency_symbol(ticker_input)
                            sizing_breakdown = pd.DataFrame({
                                'Method': ['VaR-Based Size', 'Volatility-Based Size', 'Correlation Adjustment', 
                                          'Final Position %', 'Position Value', 'Quantity'],
                                'Value': [f"{var_based_size:.1%}", f"{vol_based_size:.1%}", f"{corr_adjustment:.2f}x",
                                         f"{base_position_pct:.1%}", f"{currency_symbol}{suggested_capital_amount:,.2f}", f"{suggested_qty} shares"]
                            })
                            st.dataframe(sizing_breakdown, use_container_width=True, hide_index=True)
                            
                            st.metric("Risk-Adjusted Position Size", f"{suggested_qty} shares",
                                     delta=f"{base_position_pct:.1%} of portfolio ({currency_symbol}{suggested_capital_amount:,.2f})")
                            
                            # Risk warnings
                            if base_position_pct > MAX_POSITION_WEIGHT_NEW * 0.8:
                                st.warning(f"⚠️ Position size ({base_position_pct:.1%}) approaching maximum limit ({MAX_POSITION_WEIGHT_NEW:.0%})")
                            if avg_correlation > 0.7:
                                st.warning(f"⚠️ High correlation ({avg_correlation:.2f}) with existing positions - position size reduced")
                            
                            # Stop-loss and Trailing Stop recommendations
                            stop_loss_pct = abs(var_95) * 2 if var_95 else 0.05
                            stop_loss_price = current_price * (1 - stop_loss_pct)
                            
                            currency_symbol = get_currency_symbol(ticker_input)
                            st.markdown("#### 🛑 Risk Management")
                            col_sl1, col_sl2 = st.columns(2)
                            with col_sl1:
                                st.metric("Fixed Stop-Loss", f"{currency_symbol}{stop_loss_price:.2f}", 
                                         delta=f"{stop_loss_pct:.1%} below entry")
                            with col_sl2:
                                max_loss = suggested_qty * (current_price - stop_loss_price)
                                st.metric("Maximum Risk", f"{currency_symbol}{max_loss:,.2f}")
                            
                            # ========== INSTITUTIONAL TRAILING STOP LOSS ==========
                            st.markdown("---")
                            st.markdown("##### 📈 Institutional Trailing Stop Loss Strategy")
                            st.info("💡 **Institutional Methods:** ATR-based, dynamic adjustments, break-even protection, profit target activation")
                            
                            # Calculate ATR-based trailing stops
                            atr_multipliers = [1.5, 2.0, 2.5, 3.0]
                            atr_labels = ["Tight (1.5x ATR)", "Standard (2x ATR)", "Moderate (2.5x ATR)", "Wide (3x ATR)"]
                            
                            # Calculate recent high for trailing stop reference
                            recent_high_20 = hist["High"].tail(20).max()
                            
                            institutional_stops = []
                            
                            # Get currency symbol for this ticker
                            currency_symbol = get_currency_symbol(ticker_input)
                            
                            # Strategy 1: ATR-Based (Most Common Institutional Method)
                            for mult, label in zip(atr_multipliers, atr_labels):
                                atr_trailing = current_price - (atr * mult)
                                atr_distance_pct = (atr * mult / current_price) * 100
                                
                                institutional_stops.append({
                                    'Strategy': 'ATR-Based',
                                    'Type': label,
                                    'Multiplier': f"{mult:.1f}x",
                                    'Trailing Stop': f"{currency_symbol}{atr_trailing:.2f}",
                                    'Distance (ATR)': f"{currency_symbol}{atr * mult:.2f}",
                                    'Distance %': f"{atr_distance_pct:.2f}%",
                                    'Max Risk/Share': f"{currency_symbol}{atr * mult:.2f}"
                                })
                            
                            # Strategy 2: Dynamic Trailing (adjusts based on volatility regime)
                            if volatility > 35:
                                dynamic_mult = 3.0
                            elif volatility > 25:
                                dynamic_mult = 2.5
                            elif volatility > 15:
                                dynamic_mult = 2.0
                            else:
                                dynamic_mult = 1.5
                            
                            dynamic_trailing = current_price - (atr * dynamic_mult)
                            dynamic_distance_pct = (atr * dynamic_mult / current_price) * 100
                            
                            institutional_stops.append({
                                'Strategy': 'Dynamic (Vol-Adj)',
                                'Type': f'Vol-Adjusted ({volatility:.1f}% vol)',
                                'Multiplier': f"{dynamic_mult:.1f}x",
                                'Trailing Stop': f"{currency_symbol}{dynamic_trailing:.2f}",
                                'Distance (ATR)': f"{currency_symbol}{atr * dynamic_mult:.2f}",
                                'Distance %': f"{dynamic_distance_pct:.2f}%",
                                'Max Risk/Share': f"{currency_symbol}{atr * dynamic_mult:.2f}"
                            })
                            
                            # Strategy 3: Support-Based
                            recent_low_20 = hist["Low"].tail(20).min()
                            support_trailing = recent_low_20 * 0.98
                            support_distance_pct = ((current_price - support_trailing) / current_price) * 100
                            
                            institutional_stops.append({
                                'Strategy': 'Support-Based',
                                'Type': 'Below 20-Day Low',
                                'Multiplier': 'N/A',
                                'Trailing Stop': f"{currency_symbol}{support_trailing:.2f}",
                                'Distance (ATR)': f"{currency_symbol}{current_price - support_trailing:.2f}",
                                'Distance %': f"{support_distance_pct:.2f}%",
                                'Max Risk/Share': f"{currency_symbol}{current_price - support_trailing:.2f}"
                            })
                            
                            # Display all strategies
                            institutional_df = pd.DataFrame(institutional_stops)
                            st.dataframe(institutional_df, use_container_width=True, hide_index=True)
                            
                            # Recommended strategy (institutional standard: 2x ATR)
                            recommended_atr_mult = 2.0
                            recommended_trailing_price = current_price - (atr * recommended_atr_mult)
                            recommended_distance_pct = (atr * recommended_atr_mult / current_price) * 100
                            
                            currency_symbol = get_currency_symbol(ticker_input)
                            st.success(f"✅ **Recommended (Institutional Standard):** 2.0x ATR Trailing Stop = {currency_symbol}{recommended_trailing_price:.2f} ({recommended_distance_pct:.2f}% below price)")
                            st.info(f"📊 **ATR (14-day):** {currency_symbol}{atr:.2f} | **Current Price:** {currency_symbol}{current_price:.2f}")
                            
                            # Trailing stop progression scenarios
                            st.markdown("---")
                            st.markdown("##### 📊 Trailing Stop Progression (Institutional Method)")
                            
                            progression_prices = [
                                current_price * 1.03,  # +3%
                                current_price * 1.05,  # +5%
                                current_price * 1.08,  # +8%
                                current_price * 1.10,  # +10%
                                current_price * 1.15,  # +15%
                                current_price * 1.20   # +20%
                            ]
                            
                            progressions = []
                            for prog_price in progression_prices:
                                # Trailing stop moves up maintaining 2x ATR distance
                                prog_trailing = prog_price - (atr * recommended_atr_mult)
                                # Break-even protection after 5% profit
                                if prog_price >= current_price * 1.05:
                                    prog_trailing = max(prog_trailing, current_price)
                                
                                profit_from_entry = ((prog_price - current_price) / current_price * 100)
                                risk_remaining = (prog_price - prog_trailing) / prog_price * 100
                                
                                currency_symbol = get_currency_symbol(ticker_input)
                                progressions.append({
                                    'Price Moves To': f"{currency_symbol}{prog_price:.2f}",
                                    'Trailing Stop': f"{currency_symbol}{prog_trailing:.2f}",
                                    'Profit from Entry': f"{profit_from_entry:.1f}%",
                                    'Risk Remaining': f"{risk_remaining:.2f}%",
                                    'Protected': f"{currency_symbol}{(prog_trailing - current_price) * suggested_qty:,.2f}",
                                    'Max Risk': f"{currency_symbol}{(prog_price - prog_trailing) * suggested_qty:,.2f}"
                                })
                            
                            progression_df = pd.DataFrame(progressions)
                            st.dataframe(progression_df, use_container_width=True, hide_index=True)
                            
                            st.info("💡 **Institutional Rule:** Trailing stop moves up with price maintaining 2x ATR distance. Break-even protection activates after 5% profit.")
                            
                            # Risk-Reward Analysis
                            st.markdown("---")
                            st.markdown("##### ⚖️ Risk-Reward Analysis")
                            
                            risk_amount = (current_price - recommended_trailing_price) * suggested_qty
                            reward_targets = [0.10, 0.15, 0.20, 0.25]
                            risk_reward_ratios = []
                            
                            for target_pct in reward_targets:
                                target_price = current_price * (1 + target_pct)
                                reward_amount = (target_price - current_price) * suggested_qty
                                rr_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
                                
                                currency_symbol = get_currency_symbol(ticker_input)
                                risk_reward_ratios.append({
                                    'Profit Target': f"{target_pct:.0%}",
                                    'Target Price': f"{currency_symbol}{target_price:.2f}",
                                    'Risk': f"{currency_symbol}{risk_amount:,.2f}",
                                    'Reward': f"{currency_symbol}{reward_amount:,.2f}",
                                    'R:R Ratio': f"{rr_ratio:.2f}:1"
                                })
                            
                            rr_df = pd.DataFrame(risk_reward_ratios)
                            st.dataframe(rr_df, use_container_width=True, hide_index=True)
                            
                            currency_symbol = get_currency_symbol(ticker_input)
                            st.metric("Entry Risk Amount", f"{currency_symbol}{risk_amount:,.2f}",
                                     delta=f"{currency_symbol}{(atr * recommended_atr_mult):.2f} per share")
                            
                            # Trailing stop scenarios using ATR-based method
                            st.markdown("---")
                            st.markdown("##### 📊 Trailing Stop Scenarios (ATR-Based)")
                            scenario_prices = [current_price * 1.05, current_price * 1.10, current_price * 1.15, current_price * 1.20]
                            scenarios = []
                            for scenario_price in scenario_prices:
                                # Trailing stop maintains 2x ATR distance as price moves up
                                trailing_at_price = scenario_price - (atr * recommended_atr_mult)
                                # Break-even protection after 5% profit
                                if scenario_price >= current_price * 1.05:
                                    trailing_at_price = max(trailing_at_price, current_price)
                                
                                protected_profit = (trailing_at_price - current_price) * suggested_qty if trailing_at_price > current_price else 0
                                profit_pct = ((scenario_price - current_price) / current_price * 100)
                                risk_remaining = ((scenario_price - trailing_at_price) / scenario_price * 100)
                                
                                currency_symbol = get_currency_symbol(ticker_input)
                                scenarios.append({
                                    'If Price Reaches': f"{currency_symbol}{scenario_price:.2f}",
                                    'Trailing Stop Moves To': f"{currency_symbol}{trailing_at_price:.2f}",
                                    'Profit from Entry': f"{profit_pct:.1f}%",
                                    'Protected Profit': f"{currency_symbol}{protected_profit:,.2f}",
                                    'Risk Remaining': f"{risk_remaining:.2f}%"
                                })
                            scenario_df = pd.DataFrame(scenarios)
                            st.dataframe(scenario_df, use_container_width=True, hide_index=True)
                            st.info("💡 **Institutional Method:** Trailing stop maintains 2x ATR distance. Break-even protection activates after 5% profit.")
                            
                            # Generate trench buy levels
                            from core.trench_engine import TrenchStrategyEngine
                            
                            trench_engine = TrenchStrategyEngine(
                                avg_price=current_price,
                                base_qty=suggested_qty,
                                capital=suggested_capital_amount,
                                risk_limit=0.25
                            )
                            
                            trench_multipliers = [0.5, 1.0, 1.5]
                            trench_weights = [0.4, 0.35, 0.25]
                            trench_engine.generate_buy_trenches(atr, trench_multipliers, trench_weights)
                            
                            st.markdown("#### 📊 Entry Trench Strategy")
                            trench_df = pd.DataFrame(trench_engine.trenches, columns=["Price Level", "Quantity"])
                            trench_df["Value"] = trench_df["Price Level"] * trench_df["Quantity"]
                            trench_df["Discount %"] = ((current_price - trench_df["Price Level"]) / current_price * 100).round(2)
                            trench_df["Cumulative Qty"] = trench_df["Quantity"].cumsum()
                            trench_df["Cumulative Cost"] = trench_df["Value"].cumsum()
                            
                            currency_symbol = get_currency_symbol(ticker_input)
                            st.dataframe(trench_df.style.format({
                                "Price Level": f"{currency_symbol}{{:.2f}}",
                                "Value": f"{currency_symbol}{{:.2f}}",
                                "Discount %": "{:.2f}%",
                                "Cumulative Cost": f"{currency_symbol}{{:.2f}}"
                            }), use_container_width=True)
                            
                            blended_price = trench_engine.blended_price()
                            st.info(f"💡 **Strategy:** Scale into position. Blended entry price: {currency_symbol}{blended_price:.2f}")
                            
                            # Generate sell targets
                            sell_levels = trench_engine.sell_levels([0.10, 0.20, 0.30, 0.50], [0.25, 0.25, 0.25, 0.25])
                            
                            st.markdown("#### 📊 Profit Target Levels")
                            sell_df = pd.DataFrame(sell_levels, columns=["Target Price", "Sell Weight"])
                            sell_df["Target %"] = ((sell_df["Target Price"] / blended_price) - 1) * 100
                            sell_df["Quantity"] = (suggested_qty * sell_df["Sell Weight"]).astype(int)
                            sell_df["Proceeds"] = sell_df["Target Price"] * sell_df["Quantity"]
                            
                            currency_symbol = get_currency_symbol(ticker_input)
                            st.dataframe(sell_df.style.format({
                                "Target Price": f"{currency_symbol}{{:.2f}}",
                                "Target %": "{:.1f}%",
                                "Sell Weight": "{:.0%}",
                                "Proceeds": f"{currency_symbol}{{:.2f}}"
                            }), use_container_width=True)
                    
                    # Display signal analysis
                    st.markdown("---")
                    st.markdown("#### 📈 Signal Analysis")
                    for reason in signal_reasons:
                        st.markdown(f"- {reason}")
                    
        except Exception as e:
            st.error(f"Error generating strategy: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    st.markdown("---")
    
    config = st.session_state.config
    
    # Check if institutional features are enabled
    enable_trench = config.get("enable_trench_execution", True)
    enable_allocator = config.get("enable_portfolio_allocator", True)
    
    if not enable_trench and not enable_allocator:
        st.info("ℹ️ Institutional features are disabled in configuration. Enable them in System Configuration to use these tools.")
    
    # ========== TRENCH EXECUTION ENGINE ==========
    if enable_trench:
        st.markdown("### 🎯 Trench Execution Strategy")
        st.markdown("**Volatility-based scaling into positions**")
        st.markdown("---")
        
        col_trench1, col_trench2 = st.columns(2)
        
        with col_trench1:
            st.markdown("#### 📊 Trench Parameters")
            avg_price = st.number_input("Average Entry Price", min_value=0.01, value=100.0, step=0.01, format="%.2f", key="trench_avg_price")
            base_qty = st.number_input("Base Quantity", min_value=1, value=100, step=10, key="trench_base_qty")
            capital = st.number_input("Available Capital", min_value=0.01, value=10000.0, step=100.0, format="%.2f", key="trench_capital")
            risk_limit = st.slider("Risk Limit", 0.05, 0.50, 0.25, step=0.05, key="trench_risk_limit")
        
        with col_trench2:
            st.markdown("#### 📈 ATR & Multipliers")
            atr = st.number_input("ATR (Average True Range)", min_value=0.01, value=2.5, step=0.1, format="%.2f", key="trench_atr")
            st.markdown("**Buy Trench Multipliers:**")
            mult1 = st.number_input("Level 1 Multiplier", 0.5, 3.0, 1.0, step=0.1, key="trench_mult1")
            mult2 = st.number_input("Level 2 Multiplier", 0.5, 3.0, 1.5, step=0.1, key="trench_mult2")
            mult3 = st.number_input("Level 3 Multiplier", 0.5, 3.0, 2.0, step=0.1, key="trench_mult3")
            
            st.markdown("**Quantity Weights:**")
            weight1 = st.number_input("Level 1 Weight", 0.1, 1.0, 0.5, step=0.1, key="trench_w1")
            weight2 = st.number_input("Level 2 Weight", 0.1, 1.0, 0.3, step=0.1, key="trench_w2")
            weight3 = st.number_input("Level 3 Weight", 0.1, 1.0, 0.2, step=0.1, key="trench_w3")
        
        if st.button("Generate Trench Strategy", key="gen_trench"):
            try:
                from core.trench_engine import TrenchStrategyEngine
                
                trench_engine = TrenchStrategyEngine(avg_price, base_qty, capital, risk_limit)
                trench_engine.generate_buy_trenches(
                    atr=atr,
                    multipliers=[mult1, mult2, mult3],
                    qty_weights=[weight1, weight2, weight3]
                )
                
                blended_price = trench_engine.blended_price()
                
                st.success("✅ Trench Strategy Generated")
                
                # Default to USD for trench strategy tool (no ticker input)
                currency_symbol = '$'
                col_t1, col_t2, col_t3 = st.columns(3)
                with col_t1:
                    st.metric("Average Entry Price", f"{currency_symbol}{avg_price:.2f}")
                with col_t2:
                    st.metric("Base Quantity", f"{base_qty}")
                with col_t3:
                    st.metric("Blended Price (with trenches)", f"{currency_symbol}{blended_price:.2f}")
                
                st.markdown("#### 📋 Buy Trenches")
                trench_df = pd.DataFrame(trench_engine.trenches, columns=["Price Level", "Quantity"])
                trench_df["Value"] = trench_df["Price Level"] * trench_df["Quantity"]
                trench_df["Cumulative Qty"] = trench_df["Quantity"].cumsum()
                trench_df["Cumulative Value"] = trench_df["Value"].cumsum()
                st.dataframe(trench_df.style.format({"Price Level": f"{currency_symbol}{{:.2f}}", "Value": f"{currency_symbol}{{:.2f}}", 
                                                     "Cumulative Value": f"{currency_symbol}{{:.2f}}"}), use_container_width=True)
                
                # Sell levels
                profit_steps = [0.05, 0.10, 0.15, 0.20]  # 5%, 10%, 15%, 20% profit targets
                sell_weights = [0.25, 0.25, 0.25, 0.25]  # Equal distribution
                sell_levels = trench_engine.sell_levels(profit_steps, sell_weights)
                
                st.markdown("#### 💰 Sell Levels (Profit Targets)")
                sell_df = pd.DataFrame(sell_levels, columns=["Target Price", "Sell Weight"])
                sell_df["Target %"] = ((sell_df["Target Price"] / blended_price) - 1) * 100
                sell_df["Quantity to Sell"] = (base_qty * sell_df["Sell Weight"]).astype(int)
                # Default to USD for trench strategy tool (no ticker input)
                currency_symbol = '$'
                st.dataframe(sell_df.style.format({"Target Price": f"{currency_symbol}{{:.2f}}", "Target %": "{:.1f}%", 
                                                   "Sell Weight": "{:.0%}"}), use_container_width=True)
                
            except Exception as e:
                st.error(f"Error generating trench strategy: {str(e)}")
        
        st.divider()
    
    # ========== PORTFOLIO ALLOCATOR ==========
    if enable_allocator:
        st.markdown("### 📊 Portfolio Allocator")
        st.markdown("**Correlation-aware position sizing**")
        st.markdown("---")
        
        st.markdown("#### 📈 Multi-Asset Allocation")
        st.info("Enter ticker symbols (one per line) to calculate correlation-aware allocation")
        
        tickers_input = st.text_area(
            "Ticker Symbols",
            value="AAPL\nMSFT\nGOOGL\nTSLA",
            height=100,
            help="Enter one ticker per line"
        )
        
        allocation_capital = st.number_input("Total Capital for Allocation", min_value=1000.0, value=100000.0, 
                                            step=1000.0, format="%.2f", key="alloc_capital")
        max_weight = st.slider("Maximum Weight per Asset", 0.10, 0.50, 0.30, step=0.05, key="max_weight")
        
        if st.button("Calculate Allocation", key="calc_alloc"):
            try:
                from core.portfolio_allocator import PortfolioAllocator
                import yfinance as yf
                
                ticker_list = [t.strip().upper() for t in tickers_input.split("\n") if t.strip()]
                
                if len(ticker_list) < 2:
                    st.warning("⚠️ Please enter at least 2 tickers for correlation analysis")
                else:
                    with st.spinner("Fetching data and calculating allocation..."):
                        # Fetch historical data
                        returns_dict = {}
                        for ticker in ticker_list:
                            try:
                                stock = yf.Ticker(ticker)
                                hist = stock.history(period="1y")
                                if not hist.empty:
                                    returns_dict[ticker] = hist["Close"].pct_change().dropna()
                            except:
                                st.warning(f"⚠️ Could not fetch data for {ticker}")
                        
                        if len(returns_dict) >= 2:
                            returns_df = pd.DataFrame(returns_dict)
                            returns_df = returns_df.dropna()
                            
                            if len(returns_df) > 0:
                                allocator = PortfolioAllocator(allocation_capital)
                                weights, corr_matrix = allocator.allocate(returns_df, max_weight=max_weight)
                                
                                st.success(f"✅ Allocation calculated for {len(returns_dict)} assets")
                                
                                col_a1, col_a2 = st.columns(2)
                                
                                with col_a1:
                                    st.markdown("#### 💰 Allocation Weights")
                                    alloc_df = pd.DataFrame({
                                        "Ticker": weights.index,
                                        "Weight": weights.values,
                                        "Allocation ($)": (weights.values * allocation_capital).round(2)
                                    })
                                    alloc_df = alloc_df.sort_values("Weight", ascending=False)
                                    # Determine currency from first ticker in list
                                    first_ticker = ticker_list[0] if ticker_list else 'USD'
                                    currency_symbol = get_currency_symbol(first_ticker)
                                    st.dataframe(alloc_df.style.format({"Weight": "{:.1%}", "Allocation ($)": f"{currency_symbol}{{:,.2f}}"}), 
                                               use_container_width=True)
                                
                                with col_a2:
                                    st.markdown("#### 🔗 Correlation Matrix")
                                    st.dataframe(corr_matrix.style.format("{:.2f}"), use_container_width=True)
                                
                                # Correlation-adjusted sizing
                                st.markdown("#### 🎯 Correlation-Adjusted Sizing")
                                from core.correlation_adjustment import correlation_adjusted_size
                                
                                base_size = allocation_capital / len(ticker_list)
                                adj_sizes = []
                                for ticker in weights.index:
                                    # Get average correlation with other assets
                                    avg_corr = corr_matrix.loc[ticker].drop(ticker).mean()
                                    adj_size = correlation_adjusted_size(base_size, avg_corr)
                                    adj_sizes.append({
                                        "Ticker": ticker,
                                        "Base Size": base_size,
                                        "Avg Correlation": avg_corr,
                                        "Adjusted Size": adj_size,
                                        "Adjustment %": ((adj_size / base_size) - 1) * 100
                                    })
                                
                                adj_df = pd.DataFrame(adj_sizes)
                                # Determine currency from first ticker in list
                                first_ticker = ticker_list[0] if ticker_list else 'USD'
                                currency_symbol = get_currency_symbol(first_ticker)
                                st.dataframe(adj_df.style.format({"Base Size": f"{currency_symbol}{{:,.2f}}", "Avg Correlation": "{:.2f}", 
                                                                 "Adjusted Size": f"{currency_symbol}{{:,.2f}}", "Adjustment %": "{:.1f}%"}), 
                                           use_container_width=True)
                            else:
                                st.error("❌ Insufficient overlapping data for correlation calculation")
                        else:
                            st.error("❌ Need at least 2 valid tickers for allocation")
            except Exception as e:
                st.error(f"Error calculating allocation: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
        
        st.divider()
    
    # ========== MICROSTRUCTURE & SLIPPAGE ==========
    st.markdown("### 💱 Microstructure & Execution Cost Model")
    st.markdown("**Market impact and slippage estimation**")
    st.markdown("---")
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        mid_price = st.number_input("Mid Price", min_value=0.01, value=100.0, step=0.01, format="%.2f", key="micro_mid")
        spread = st.number_input("Bid-Ask Spread (%)", min_value=0.01, max_value=5.0, value=0.1, step=0.01, format="%.2f", key="micro_spread")
        adv = st.number_input("Average Daily Volume", min_value=1, value=1000000, step=10000, key="micro_adv")
    
    with col_m2:
        trade_qty = st.number_input("Trade Quantity", min_value=1, value=1000, step=100, key="micro_qty")
        trade_side = st.selectbox("Trade Side", ["BUY", "SELL"], key="micro_side")
        
        if st.button("Calculate Execution Cost", key="calc_micro"):
            try:
                from core.microstructure import MicrostructureModel
                
                microstructure = MicrostructureModel(spread=spread/100, adv=adv)
                impact_cost = microstructure.impact_cost(trade_qty)
                expected_fill = microstructure.expected_fill_price(mid_price, trade_qty, trade_side.lower())
                
                slippage = abs(expected_fill - mid_price)
                slippage_pct = (slippage / mid_price) * 100
                
                st.success("✅ Execution Cost Calculated")
                
                # Default to USD for microstructure tool (no ticker input)
                currency_symbol = '$'
                col_e1, col_e2, col_e3 = st.columns(3)
                with col_e1:
                    st.metric("Impact Cost", f"{impact_cost:.4f}")
                with col_e2:
                    st.metric("Expected Fill Price", f"{currency_symbol}{expected_fill:.2f}")
                with col_e3:
                    st.metric("Slippage", f"{currency_symbol}{slippage:.2f}", delta=f"{slippage_pct:.2f}%", delta_color="inverse")
                
                total_cost = slippage * trade_qty
                st.info(f"💰 **Total Execution Cost:** {currency_symbol}{total_cost:,.2f} for {trade_qty} shares")
                
            except Exception as e:
                st.error(f"Error calculating execution cost: {str(e)}")
    
    st.divider()
    
    # ========== INTEGRATION WITH RISK METRICS ==========
    st.markdown("### ⚠️ Integrated Risk Metrics")
    st.markdown("**VaR/CVaR and Stress Testing (from Risk Monitor)**")
    st.markdown("---")
    
    if st.session_state.equity_history:
        equity_series = pd.Series(st.session_state.equity_history)
        returns = equity_series.pct_change().dropna()
        
        if len(returns) > 0:
            col_r1, col_r2, col_r3 = st.columns(3)
            
            with col_r1:
                var_95 = st.session_state.risk_manager.get_var(level=0.05)
                if var_95 is not None:
                    st.metric("VaR (95%)", f"{var_95:.2%}")
                else:
                    st.metric("VaR (95%)", "N/A")
            
            with col_r2:
                cvar_95 = st.session_state.risk_manager.get_cvar(level=0.05)
                if cvar_95 is not None:
                    st.metric("CVaR (95%)", f"{cvar_95:.2%}")
                else:
                    st.metric("CVaR (95%)", "N/A")
            
            with col_r3:
                st.info("💡 Use Risk Monitor tab for detailed stress testing scenarios")
    else:
        st.info("ℹ️ Analyze equity in Dashboard tab to see risk metrics here")

# Enhanced Footer
st.markdown("---")
st.markdown("""
<div style="background: #f8fafc; padding: 2rem; border-radius: 12px; text-align: center; margin-top: 3rem;">
    <p style="color: #64748b; margin: 0; font-size: 0.875rem;">
        ⚠️ <strong>Educational / Research Use Only</strong> - Not for actual trading
    </p>
    <p style="color: #94a3b8; margin: 0.5rem 0 0 0; font-size: 0.75rem;">
        Nashor Portfolio Quant Trading System v1.0.0 | © 2026
    </p>
</div>
""", unsafe_allow_html=True)
