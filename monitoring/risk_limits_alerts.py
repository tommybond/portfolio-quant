
import smtplib
from email.mime.text import MIMEText

class RiskLimits:
    def __init__(self, max_drawdown, max_var):
        self.max_drawdown = max_drawdown
        self.max_var = max_var

    def check(self, metrics):
        alerts = []
        if metrics.get('Max Drawdown', 0) < self.max_drawdown:
            alerts.append('MAX DRAWDOWN BREACHED')
        if metrics.get('VaR', 0) < self.max_var:
            alerts.append('VAR LIMIT BREACHED')
        return alerts

    def send_alert(self, message, to_email):
        msg = MIMEText(message)
        msg['Subject'] = 'RISK LIMIT ALERT'
        msg['From'] = 'risk@system'
        msg['To'] = to_email
        # SMTP configuration would go here
