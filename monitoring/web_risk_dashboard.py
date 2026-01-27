
import plotly.graph_objects as go
import pandas as pd

class WebRiskDashboard:
    def __init__(self, equity_curve):
        self.equity = equity_curve

    def render(self):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=self.equity.index,
            y=self.equity.values,
            mode='lines',
            name='Equity Curve'
        ))
        fig.update_layout(
            title='Institutional Trench Strategy – Risk Dashboard',
            xaxis_title='Time',
            yaxis_title='Equity'
        )
        fig.show()
