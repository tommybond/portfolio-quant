
from monitoring.audit import log_event
from monitoring.compliance import ComplianceLogger

class TradeApproval:
    def __init__(self, mode="SEMI", enable_compliance=True):
        self.mode = mode
        self.compliance_logger = ComplianceLogger() if enable_compliance else None

    def approve(self, trade):
        if self.mode == "AUTO":
            approved = True
        elif self.mode == "SEMI":
            # In Streamlit context, this would be handled via UI
            # For CLI, fallback to input
            try:
                print("Approval needed:", trade)
                decision = input("Approve? y/n: ").lower() == "y"
                approved = decision
            except:
                # In non-interactive context, default to False for SEMI mode
                approved = False
        else:  # MANUAL
            try:
                print("Manual approval needed:", trade)
                decision = input("Approve? y/n: ").lower() == "y"
                approved = decision
            except:
                approved = False
        
        # Log to audit system
        log_event("APPROVAL", {"trade": trade, "approved": approved, "mode": self.mode})
        
        # Log to compliance system if enabled
        if self.compliance_logger and approved:
            symbol = trade.get('symbol', 'UNKNOWN')
            side = trade.get('side', 'UNKNOWN')
            qty = trade.get('quantity', 0)
            price = trade.get('price', 0)
            reason = f"Approved via {self.mode} mode"
            self.compliance_logger.log_trade(symbol, side, qty, price, reason)
        
        return approved
