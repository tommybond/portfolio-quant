def get_broker_instance(broker_name: str = None):
    """
    Get broker instance based on selection - cached in session state
    """
    if not INTEGRATIONS_AVAILABLE:
        return None

    if broker_name is None:
        broker_name = st.session_state.get('selected_broker', 'Alpaca')

    # Cache key for this broker
    cache_key = f'broker_instance_{broker_name}'
    
    # Return cached instance if available and still connected
    if cache_key in st.session_state:
        broker = st.session_state[cache_key]
        if broker is not None:
            # Check if still connected
            if broker_name == 'IBKR' and hasattr(broker, 'ib'):
                if broker.ib.isConnected():
                    return broker
                # If disconnected, remove from cache and recreate below
                del st.session_state[cache_key]
            else:
                return broker

    try:
        if broker_name == 'Alpaca':
            broker = AlpacaBroker()
        elif broker_name == "IBKR" and IBKR_AVAILABLE and IBKRBroker:
            client_id = st.session_state["ibkr_client_id"]
            broker = IBKRBroker(client_id=client_id, auto_connect=False)
            # Try to connect
            try:
                broker.connect(timeout=3.0)
                if broker.ib.isConnected():
                    print(f"✅ IBKR connected successfully (client_id={client_id})")
                else:
                    print(f"⚠️ IBKR connection returned but not connected (client_id={client_id})")
            except Exception as conn_error:
                print(f"❌ IBKR connection error: {conn_error}")
                # Store error in session state for debugging
                st.session_state['ibkr_last_error'] = str(conn_error)
                # Return broker instance anyway (will show as not connected)
        else:
            broker = AlpacaBroker()
        
        # Cache the broker instance
        st.session_state[cache_key] = broker
        return broker
        
    except Exception as e:
        print(f"Failed to initialize {broker_name} broker: {e}")
        return None
