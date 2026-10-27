---
title: "Quantitative Trading & Predictive Signals Workspace"
type: "workspace_catalog"
tags:
  - cortex/workspaces
  - cortex/trading
  - cortex/quant
  - cortex/machine_learning
  - cortex/xgboost
  - cortex/dhan
last_updated: "2026-10-27"
status: "verified"
---

# 📈 Quantitative Trading & Predictive Signals Workspace

- **Primary Locations**:
  - `C:\Users\soham\Desktop\stock-signal-predictor` (ML feature pipelines, XGBoost models & Dhan API)
  - `C:\Users\soham\Desktop\stockgro` (Interactive financial simulation & Streamlit dashboard)
  - `C:\Users\soham\Desktop\Trading_Bot` (Modular algorithmic order executor & risk validator)
- **Domain**: Financial Time-Series Forecasting, Feature Engineering, Dhan Broker Integration, Telegram Alerts
- **Primary Toolchains**: Python 3.10 / 3.12, XGBoost, scikit-learn, joblib, pandas, Streamlit, Docker Compose

## 🏛️ System Architecture (`stock-signal-predictor`)

```
Historical Tick CSVs          Dhan Live Feed / Websockets
(HDFCBANK, INFY, etc.)                 │
         │                             ▼
         ▼                      [live_ingest.py]
  [build_features.py]                  │
         │                             ▼
         ▼                     [live_features.py]
  [train_model.py]                     │
         │                             ▼
  XGBoost Joblib Model ──────► [live_signals.py]
  (xgb_signal_model.joblib)            │
                                       ├── [Signal Fired] ──► [telegram_alert.py]
                                       └── [Audit Log]   ──► SQLite Database
```

---

## 🛠️ Key Pipeline Scripts & Artifacts

| Component | File Path | Technical Details |
|---|---|---|
| **Trained ML Model** | `models/xgb_signal_model.joblib` | Gradient boosted tree classifier trained on technical momentum, volatility, and mean-reversion features. |
| **Label Encoder** | `models/label_encoder.joblib` | Maps categorical target labels (`BUY`, `SELL`, `HOLD`) to numeric model outputs. |
| **Feature Pipeline** | [`build_features.py`](file:///c:/Users/soham/Desktop/stock-signal-predictor/build_features.py) | Generates RSI (14), MACD (12, 26, 9), Bollinger Bands ($\pm 2\sigma$), EMA (20/50/200), and ATR volatility bands. |
| **Model Training** | [`train_model.py`](file:///c:/Users/soham/Desktop/stock-signal-predictor/train_model.py) | Time-series cross-validation avoiding lookahead bias; evaluates precision, recall, and F1 per class. |
| **Backtesting Engine** | [`backtest.py`](file:///c:/Users/soham/Desktop/stock-signal-predictor/backtest.py) | Event-driven historical simulation accounting for transaction fees, slippage, and position sizing. |
| **Dhan Broker Integration**| [`resolve_security_ids.py`](file:///c:/Users/soham/Desktop/stock-signal-predictor/resolve_security_ids.py) | Maps NSE equity tickers to Dhan instrument security IDs (`security_id_list.csv`, `DHAN_SETUP.md`). |
| **Live Ingestion** | [`live_ingest.py`](file:///c:/Users/soham/Desktop/stock-signal-predictor/live_ingest.py) & [`live_signals.py`](file:///c:/Users/soham/Desktop/stock-signal-predictor/live_signals.py) | Streams market ticks, updates rolling feature buffers in real-time, and scores incoming ticks. |
| **Alert Dispatcher** | [`telegram_alert.py`](file:///c:/Users/soham/Desktop/stock-signal-predictor/telegram_alert.py) | Formats trade triggers with entry price, stop-loss, and take-profit targets, sending push alerts via Telegram Bot API (`TELEGRAM_SETUP.md`). |
| **Historical Datasets** | `data/` | Historical daily and minute bars for `HDFCBANK.NS.csv`, `INFY.NS.csv`, `RELIANCE.NS.csv`, `TCS.NS.csv`, and `IDX_NSEI.csv` (Nifty 50). |

---

## 🤖 Companion Modules: `Trading_Bot` & `stockgro`
- **`Trading_Bot`**:
  - `bot/orders.py`: Market, limit, and stop-loss order constructors with strict parameter verification (`bot/validators.py`).
  - `bot/client.py`: Thread-safe exchange client wrapper.
  - `cli.py`: Interactive CLI for monitoring open positions and account equity.
- **`stockgro`**:
  - Streamlit interactive web dashboard for real-time visualization of price charts, indicators, and model predictions.

---

## 🛡️ Risk & Governance Guidelines
- All live trading bots require strict operator approval boundaries prior to order submission.
- CortexOS enforces hardware monitoring during compute-intensive parameter grid searches to prevent CPU thermal throttling.
- No broker credentials or Telegram bot tokens may be logged or committed without `.env` exclusion.

---
## Related Notes
- [[07_Workspace_Index/Desktop_Workspace_Master_Index|Desktop Workspace Master Index]]
- [[05_System_State/Operator_Profile_and_Habits|Operator Profile and Habits]]
- [[01_Architecture/Governance_Cedar|Cedar Security Governance]]
- [[05_System_State/Hardware_Topology|Hardware Topology]]
- [[05_System_State/Filesystem_and_Workspaces|Filesystem and Workspaces]]
