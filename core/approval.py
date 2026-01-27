
from monitoring.audit import log_event

class TradeApproval:
    def __init__(self, mode="SEMI"):
        self.mode = mode

    def approve(self, trade):
        if self.mode == "AUTO":
            return True
        print("Approval needed:", trade)
        decision = input("Approve? y/n: ").lower() == "y"
        log_event("APPROVAL", {"trade": trade, "approved": decision})
        return decision
