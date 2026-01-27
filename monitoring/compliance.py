
import json
from datetime import datetime

class ComplianceLogger:
    def __init__(self, logfile='compliance_log.json'):
        self.logfile = logfile

    def log_trade(self, symbol, side, qty, price, reason):
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'symbol': symbol,
            'side': side,
            'quantity': qty,
            'price': price,
            'reason': reason
        }
        with open(self.logfile, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def log_risk_event(self, event, metrics):
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': event,
            'metrics': metrics
        }
        with open(self.logfile, 'a') as f:
            f.write(json.dumps(entry) + '\n')
