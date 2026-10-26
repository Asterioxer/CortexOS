# Quantitative Trading & Predictive Signals Workspace

- **Primary Locations**:
  - `C:\Users\soham\Desktop\stock-signal-predictor`
  - `C:\Users\soham\Desktop\stockgro`
  - `C:\Users\soham\Desktop\Trading_Bot`
- **Domain**: Financial Time-Series Forecasting, Technical Indicators, Automated Execution
- **Primary Toolchains**: Python 3 (pandas, numpy, scikit-learn, ta-lib / pandas-ta), Jupyter Notebooks, Flask / Streamlit

## Architecture & Data Flow
1. **Feature Engineering (`build_features.py`)**:
   - Computes rolling momentum indicators: RSI (Relative Strength Index), MACD (Moving Average Convergence Divergence), Bollinger Bands, and Exponential Moving Averages (EMA 20/50/200).
   - Generates normalized target labels for classification (Long, Short, Neutral) based on forward-looking $N$-bar return thresholds.
2. **Backtesting Pipeline (`backtest.py`)**:
   - Event-driven backtester accounting for transaction slippage, bid-ask spreads, and capital allocation constraints.
   - Outputs Sharpe ratio, Sortino ratio, Maximum Drawdown (MDD), and win/loss hit rates.
3. **Automated Trading & Monitoring**:
   - `trading_bot`: Automated order placement engine with risk management stop-loss and take-profit triggers.
   - `stockgro`: Portfolio tracking and simulation platform.

## Risk & Execution Constraints
- All live trading bots require strict operator approval boundaries prior to order submission.
- CortexOS enforces hardware monitoring during compute-intensive parameter grid searches to prevent CPU thermal throttling.

---
## Related Notes
- [[Operator_Profile_and_Habits]]
- [[Autonomy_Boundaries]]
- [[Hardware_Topology]]
