# 🇮🇳 Bharat Portfolio — AI Stock Tracker

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Flask](https://img.shields.io/badge/Flask-Backend-black)
![SocketIO](https://img.shields.io/badge/WebSocket-RealTime-green)
![License](https://img.shields.io/badge/License-MIT-orange)

A **premium Indian stock portfolio tracker** with **real-time NSE/BSE prices, AI-powered buy/sell signals, and a modern glassmorphism UI inspired by the Indian tricolor 🇮🇳.**

This project demonstrates **real-time data streaming, financial analysis logic, and interactive frontend dashboards using Python.**

---

# 🌐 Live Demo

🚀 **Try the application here**

🔗 https://bharath-portfolio-zzet.onrender.com

---

# ✨ Features

| Feature                            | Description                                                 |
| ---------------------------------- | ----------------------------------------------------------- |
| 🇮🇳 **Indian Theme UI**           | Saffron & green tricolor palette with ₹ INR currency format |
| 📊 **30+ NSE Stocks**              | Includes RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK and more  |
| ⚡ **Real-Time Price Updates**      | WebSocket live streaming using Flask-SocketIO               |
| 🤖 **AI Stock Analyst**            | Buy/Sell/Hold signals using RSI + SMA crossover             |
| 📈 **Portfolio Performance Chart** | Line chart comparing invested vs current value              |
| 🥧 **Allocation Visualization**    | Doughnut chart showing stock allocation                     |
| 🪟 **Glassmorphism UI**            | Frosted glass cards with animated gradient background       |
| 💾 **Persistent Storage**          | Portfolio saved locally using `portfolio.json`              |

---

# 🧠 AI Trading Logic

The built-in **AI Analyst Engine** evaluates stocks using simple but effective technical indicators.

### 1️⃣ RSI (Relative Strength Index)

* RSI < 30 → **Oversold → BUY signal**
* RSI > 70 → **Overbought → SELL signal**

### 2️⃣ SMA Crossover Strategy

* **20-Day Moving Average**
* **50-Day Moving Average**

If:

* 20 SMA crosses **above** 50 SMA → **Bullish**
* 20 SMA crosses **below** 50 SMA → **Bearish**

### 3️⃣ Volume Spike Detection

Detects unusual trading activity compared with **20-day average volume**, signaling possible momentum.

> This AI logic runs **locally** — no paid API or API keys required.

---

# ⚡ Quick Start

Clone the repository

```
git clone https://github.com/yourusername/Bharat-Portfolio.git
cd Bharat-Portfolio
```

Install dependencies

```
pip install -r requirements.txt
```

Run the application

```
python app.py
```

Open in browser

```
http://127.0.0.1:5000
```

---

# 📂 Project Structure

```
Bharat-Portfolio
│
├── app.py
│   Flask backend + AI engine + WebSocket server
│
├── templates
│   └── index.html
│       Frontend UI (glassmorphism dashboard)
│
├── portfolio.json
│   Local storage for portfolio holdings
│
├── requirements.txt
│   Python dependencies
│
├── .gitignore
│
└── README.md
```

---

# 🛠️ Tech Stack

### Backend

* Python
* Flask
* Flask-SocketIO
* yfinance

### Frontend

* HTML / CSS / JavaScript
* Chart.js
* Socket.IO

### Deployment

* Render Cloud Hosting

### UI

* Glassmorphism design
* Indian tricolor palette
* Google Font **Outfit**

---

# 📦 Requirements

```
flask
flask-socketio
yfinance
```

Install with:

```
pip install -r requirements.txt
```

---

# 🎯 Future Improvements

* 📊 Candlestick charts
* 🧠 Advanced AI prediction model (LSTM / ML)
* 📱 Mobile responsive dashboard
* 📩 Price alerts & notifications
* ☁️ Cloud portfolio storage (Firebase / Supabase)

---

# 👨‍💻 Author

**Srikanth M**

💼 GitHub
https://github.com/venomy46

🔗 LinkedIn
https://www.linkedin.com/in/srikanth-m-b22105276/

---

⭐ If you like this project, **consider giving it a star on GitHub!**
