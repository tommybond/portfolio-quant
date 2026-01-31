"""Alert manager for risk and trade notifications."""

import logging
from enum import Enum

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AlertManager:
    """Sends risk and trade alerts (logs by default; can be extended for email/Slack)."""

    def send_risk_alert(self, alert_type: str, details: dict) -> None:
        """Emit a risk alert (e.g. VAR_LIMIT_BREACHED)."""
        logger.warning(
            "RISK_ALERT %s | %s",
            alert_type,
            details,
            extra={"alert_type": alert_type, "details": details},
        )

    def send_trade_alert(self, details: dict) -> None:
        """Emit a trade alert (symbol, side, quantity, price)."""
        logger.info(
            "TRADE_ALERT | %s",
            details,
            extra={"details": details},
        )


_alert_manager: AlertManager | None = None


def get_alert_manager() -> AlertManager:
    """Return the shared AlertManager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
