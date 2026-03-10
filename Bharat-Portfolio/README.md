# 🇮🇳 Bharat Portfolio — AI Stock Tracker

A **premium Indian stock portfolio tracker** with real-time NSE/BSE prices, AI buy/sell/hold signals, and a beautiful glassmorphism UI with saffron & green tricolor theme.

---

## ✨ Features

| Feature | Details |
|---------|---------|
| 🇮🇳 **Indian Theme** | Saffron & green tricolor palette, ₹ INR currency, Indian number format |
| 📊 **30+ NSE Stocks** | RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK and more |
| ⚡ **Real-time Prices** | WebSocket live feed via yfinance + Flask-SocketIO |
| 🤖 **AI Analyst** | RSI, SMA crossover & volume-based buy/sell/hold signals |
| 🪟 **Glassmorphism UI** | Frosted glass cards, animated background blobs |
| 📈 **Portfolio Chart** | Line chart — invested vs current value per stock |
| 🥧 **Allocation Chart** | Doughnut chart showing portfolio allocation |
| 💾 **Persistent** | Portfolio saved to `portfolio.json` locally |

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install flask flask-socketio yfinance

# 2. Run the app
python app.py

# 3. Open in browser
# http://127.0.0.1:5000
```

---

## 🤖 How the AI Works

1. **RSI (Relative Strength Index)** — if RSI < 30 → oversold (BUY), RSI > 70 → overbought (SELL)
2. **SMA Crossover** — 20-day vs 50-day moving average crossover signal
3. **Volume Spike** — unusual volume vs 20-day average flags momentum

No paid API or internet key needed — all logic runs locally with yfinance data.

---

## 📁 File Structure

```
Bharat-Portfolio/
├── app.py                ← Flask backend + AI engine + WebSocket
├── templates/
│   └── index.html        ← Frontend (glassmorphism UI)
├── portfolio.json        ← Your holdings (auto-created, gitignored)
├── requirements.txt      ← Python dependencies
├── .gitignore
└── README.md
```

---

## 📦 Requirements

```
flask
flask-socketio
yfinance
```

Or install via:
```bash
pip install -r requirements.txt
```

---

## 🛠️ Tech Stack

- **Backend:** Python · Flask · Flask-SocketIO · yfinance
- **Frontend:** Vanilla HTML/CSS/JS · Chart.js · Socket.IO
- **Fonts:** [Outfit](https://fonts.google.com/specimen/Outfit) via Google Fonts
- **Real-time:** WebSocket streaming (no page refresh needed)
- **AI Engine:** Rule-based RSI + SMA + Volume analysis
