
import logging
import json
from datetime import datetime
from monitoring.compliance import ComplianceLogger

logging.basicConfig(
    filename="audit.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# Initialize compliance logger for risk events
_compliance_logger = ComplianceLogger()

def log_event(event, details):
    """Log event to audit log and compliance system if applicable"""
    # Format details for logging
    if isinstance(details, dict):
        log_message = f"{event} | {json.dumps(details)}"
    else:
        log_message = f"{event} | {details}"
    
    logging.info(log_message)
    
    # Log risk events to compliance system
    if event in ["KILL_SWITCH", "RISK_LIMIT_ALERT", "VAR_BREACH", "DRAWDOWN_BREACH"]:
        if isinstance(details, dict):
            _compliance_logger.log_risk_event(event, details)
        else:
            _compliance_logger.log_risk_event(event, {"details": str(details)})

def log_risk_alert(alert_type, metrics, severity="WARNING"):
    """Log risk alert with severity level"""
    log_event(f"RISK_ALERT_{alert_type}", {
        "severity": severity,
        "metrics": metrics,
        "timestamp": datetime.utcnow().isoformat()
    })
