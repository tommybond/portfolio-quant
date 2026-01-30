#!/usr/bin/env python3
"""Test script to verify all connections and imports."""

import sys
import os

print('=== Python Environment Check ===')
print(f'Python version: {sys.version}')
print(f'Python executable: {sys.executable}')
print()

print('=== Testing Key Imports ===')
try:
    import streamlit as st
    print('✓ streamlit')
except Exception as e:
    print(f'✗ streamlit: {e}')

try:
    import pandas as pd
    print('✓ pandas')
except Exception as e:
    print(f'✗ pandas: {e}')

try:
    import numpy as np
    print('✓ numpy')
except Exception as e:
    print(f'✗ numpy: {e}')

try:
    import yfinance as yf
    print('✓ yfinance')
except Exception as e:
    print(f'✗ yfinance: {e}')

try:
    import yaml
    print('✓ yaml')
except Exception as e:
    print(f'✗ yaml: {e}')

try:
    import matplotlib
    print('✓ matplotlib')
except Exception as e:
    print(f'✗ matplotlib: {e}')

print()
print('=== Testing Project Modules ===')

try:
    from core.risk import RiskManager
    print('✓ core.risk.RiskManager')
except Exception as e:
    print(f'✗ core.risk.RiskManager: {e}')

try:
    from database.models import init_database
    print('✓ database.models')
except Exception as e:
    print(f'✗ database.models: {e}')

try:
    from auth.auth import AuthManager
    print('✓ auth.auth.AuthManager')
except Exception as e:
    print(f'✗ auth.auth.AuthManager: {e}')

try:
    from oms.oms import OrderManager
    print('✓ oms.oms.OrderManager')
except Exception as e:
    print(f'✗ oms.oms.OrderManager: {e}')

try:
    from oms.broker_alpaca import AlpacaBroker
    print('✓ oms.broker_alpaca.AlpacaBroker')
except Exception as e:
    print(f'✗ oms.broker_alpaca.AlpacaBroker: {e}')

print()
print('=== Testing Streamlit App Syntax ===')
try:
    with open('app.py', 'r') as f:
        code = f.read()
    compile(code, 'app.py', 'exec')
    print('✓ app.py syntax is valid')
except Exception as e:
    print(f'✗ app.py syntax error: {e}')

print()
print('=== Connection Test Complete ===')
