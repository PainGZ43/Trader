import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
import sys

def generate_report(result_file, trade_file, output_file="data/backtest_report.html"):
    print("Generating HTML Report...", flush=True)
    
    if not os.path.exists(result_file):
        print("Result file not found.")
        return

    # Load Data
    df_results = pd.read_csv(result_file)
    
    df_trades = pd.DataFrame()
    if os.path.exists(trade_file):
        df_trades = pd.read_csv(trade_file)
        if not df_trades.empty:
            df_trades['time'] = pd.to_datetime(df_trades['time'])

    # 1. Equity Curve & Drawdown
    # We need equity curve data. It's inside result_file as a string representation of Series?
    # Or we can reconstruct it if we saved it properly.
    # In run_backtest_with_csv.py, we saved 'equity_curve' column in results? 
    # No, we popped it before saving to CSV to avoid huge file size.
    # We only saved the plot image.
    
    # To make interactive chart, we need the equity curve data.
    # We should modify run_backtest to save equity curve data to a separate JSON or CSV.
    # OR, for now, we can just visualize the per-stock metrics and trades.
    
    # Let's visualize:
    # A. Performance Distribution (Histogram of Returns)
    # B. Scatter Plot (Return vs MDD)
    # C. Top/Bottom Performers Table
    # D. Monthly Heatmap (if we had daily portfolio values)
    
    # Create Subplots
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{"type": "xy"}, {"type": "xy"}],
               [{"type": "table"}, {"type": "table"}]],
        subplot_titles=("Return Distribution", "Risk vs Return", "Top 10 Performers", "Worst 10 Performers")
    )
    
    # A. Return Distribution
    fig.add_trace(
        go.Histogram(x=df_results['return'], nbinsx=50, name="Return %"),
        row=1, col=1
    )
    
    # B. Risk vs Return
    fig.add_trace(
        go.Scatter(
            x=df_results['mdd'], 
            y=df_results['return'], 
            mode='markers',
            text=df_results['name'],
            marker=dict(
                size=8,
                color=df_results['sharpe'], # Color by Sharpe
                colorscale='Viridis',
                showscale=True
            ),
            name="Stocks"
        ),
        row=1, col=2
    )
    fig.update_xaxes(title_text="Max Drawdown (%)", row=1, col=2)
    fig.update_yaxes(title_text="Return (%)", row=1, col=2)
    
    # C. Top 10 Table
    top_10 = df_results.sort_values('return', ascending=False).head(10)
    fig.add_trace(
        go.Table(
            header=dict(values=["Name", "Return %", "MDD %", "Win Rate %", "Sharpe"],
                        fill_color='paleturquoise',
                        align='left'),
            cells=dict(values=[top_10.name, top_10['return'].round(2), top_10.mdd.round(2), top_10.win_rate.round(2), top_10.sharpe.round(2)],
                       fill_color='lavender',
                       align='left')
        ),
        row=2, col=1
    )
    
    # D. Worst 10 Table
    worst_10 = df_results.sort_values('return', ascending=True).head(10)
    fig.add_trace(
        go.Table(
            header=dict(values=["Name", "Return %", "MDD %", "Win Rate %", "Sharpe"],
                        fill_color='lightpink',
                        align='left'),
            cells=dict(values=[worst_10.name, worst_10['return'].round(2), worst_10.mdd.round(2), worst_10.win_rate.round(2), worst_10.sharpe.round(2)],
                       fill_color='mistyrose',
                       align='left')
        ),
        row=2, col=2
    )
    
    fig.update_layout(height=800, title_text="Backtest Summary Report", showlegend=False)
    
    # Save
    fig.write_html(output_file)
    print(f"Report saved to {output_file}")

if __name__ == "__main__":
    generate_report("data/backtest_results.csv", "data/backtest_trades.csv")
