from oms.broker_ibkr import IBKRBroker

# pick a unique client id (avoid ones shown in TWS/IB Gateway "Active Clients")
broker = IBKRBroker(client_id=12345)  

try:
    broker.connect()
    print("Connected:", broker.ib.isConnected(), "clientId=", broker.client_id)
    print("Managed accounts:", broker.ib.managedAccounts())
    broker.disconnect()
except Exception as e:
    print("Connect failed:", e)
    import traceback; traceback.print_exc()