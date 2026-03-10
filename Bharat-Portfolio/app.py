"""
╔══════════════════════════════════════════════════════════════╗
║         STOCK PORTFOLIO TRACKER — Beginner Friendly Edition  ║
║                                                              ║
║  What this project does:                                     ║
║  → A real-time web dashboard to track your stock portfolio.  ║
║  → Prices update live (every 5 seconds) via WebSockets.      ║
║  → An AI engine analyses each stock and gives BUY/HOLD/SELL  ║
║    recommendations based on technical indicators.            ║
║                                                              ║
║  Tech Stack:                                                 ║
║  → Flask       : Python web framework (creates the server)   ║
║  → Flask-SocketIO: Enables real-time communication           ║
║                   between server and browser (WebSockets)    ║
║  → yfinance    : Free library to fetch stock price data      ║
║                  from Yahoo Finance (no API key needed!)     ║
║                                                              ║
║  Key Concepts Used (great for interviews!):                  ║
║  → REST API   — routes that the browser calls (GET/POST)     ║
║  → WebSockets — two-way real-time connection (like a chat)   ║
║  → Threading  — background task that streams prices          ║
║  → JSON       — data format used between server and browser  ║
║  → Technical Indicators — RSI, SMA (explained below)         ║
║  → Decorators — @app.route() is a Python decorator           ║
╚══════════════════════════════════════════════════════════════╝

HOW TO RUN:
    1. pip install flask flask-socketio yfinance
    2. python app.py
    3. Open browser: http://localhost:5000
"""

import json         # For reading/writing portfolio data as JSON files
import os           # For file path operations
import time         # For adding delays in the price streaming loop
from datetime import datetime       # For timestamps (last-updated display)
from threading import Thread        # To run price streaming in the background

import yfinance as yf               # Yahoo Finance — free stock data
from flask import Flask, render_template, request, redirect, jsonify, send_file
from flask_socketio import SocketIO # Real-time WebSocket communication


# ──────────────────────────────────────────────────────────────
#  FLASK APP SETUP
#  Flask is a "micro web framework" — it turns your Python script
#  into a web server that browsers can connect to.
#
#  SocketIO adds WebSocket support so the server can PUSH data
#  to all connected browsers without them having to refresh.
# ──────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = "stockai-secret-2025"   # Required for SocketIO sessions

# async_mode="threading" means we use Python threads (not async/await)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")


# ──────────────────────────────────────────────────────────────
#  SECTION 1: PORTFOLIO PERSISTENCE
#
#  We save the portfolio to a JSON file so data isn't lost
#  when the server restarts. JSON is a simple text format:
#  {"AAPL": {"quantity": 10, "buy_price": 150.0}, ...}
#
#  Interview talking point:
#  "I used JSON file storage because this is a simple project
#   without a database. For production, I'd use SQLite or PostgreSQL."
# ──────────────────────────────────────────────────────────────

# Build the full path to portfolio.json, relative to this script's location
PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "portfolio.json")


def load_portfolio():
    """
    Load portfolio data from the JSON file.
    Returns a dictionary of stock holdings.
    If the file doesn't exist yet, return an empty dict.
    """
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as file:
            return json.load(file)   # Parse JSON string → Python dictionary
    return {}   # Default: empty portfolio


def save_portfolio(data):
    """
    Save the portfolio dictionary to the JSON file.
    indent=4 makes the file human-readable (pretty-printed).
    """
    with open(PORTFOLIO_FILE, "w") as file:
        json.dump(data, file, indent=4)   # Python dict → JSON string → file


# Load portfolio at startup (so it's available when the server starts)
portfolio = load_portfolio()


# ──────────────────────────────────────────────────────────────
#  SECTION 2: PRICE FETCHING WITH CACHING
#
#  yfinance makes one HTTP request per call, which can be slow.
#  We use a simple cache: store the last price and when we got it.
#  If it's less than 30 seconds old, return the cached price.
#
#  This is the "cache-aside" pattern — very common in real software!
# ──────────────────────────────────────────────────────────────

# Cache: { "AAPL": (price, timestamp), "TSLA": (price, timestamp), ... }
_price_cache = {}
CACHE_SECONDS = 30   # How long before we fetch a fresh price


def get_live_price(symbol: str) -> float:
    """
    Fetch the latest stock price for a given ticker symbol.
    Uses a 30-second in-memory cache to avoid excessive API calls.

    Args:
        symbol: Stock ticker, e.g. "AAPL", "TSLA"
    Returns:
        Latest price as a float, or 0 if fetch fails
    """
    now = time.time()   # Current time in seconds (Unix timestamp)

    # Check if we have a recent cached price
    if symbol in _price_cache:
        cached_price, cached_time = _price_cache[symbol]
        if now - cached_time < CACHE_SECONDS:
            return cached_price   # Return cached value — no API call needed

    # Cache is empty or expired → fetch from Yahoo Finance
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="2d")   # Get last 2 days of data

        if not history.empty:
            price = float(history["Close"].iloc[-1])   # Latest closing price
            _price_cache[symbol] = (price, now)         # Store in cache
            return price

    except Exception:
        pass   # If fetch fails, fall through to return last known price

    # Return last cached price (even if expired) or 0 if never fetched
    return _price_cache.get(symbol, (0, 0))[0]


def get_price_history(symbol: str, days: int = 30):
    """
    Fetch historical closing prices for the past N days.
    Returns a list of dicts: [{"date": "Jan 01", "close": 150.5}, ...]
    This is used by the Chart.js graphs in the frontend.
    """
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=f"{days}d")

        result = []
        for date_index, row in history.iterrows():
            result.append({
                "date":  date_index.strftime("%b %d"),     # e.g. "Mar 01"
                "close": round(float(row["Close"]), 2),    # 2 decimal places
            })
        return result

    except Exception:
        return []   # Return empty list if anything goes wrong


# ──────────────────────────────────────────────────────────────
#  SECTION 3: AI MARKET ANALYST ENGINE
#
#  No external AI API needed! We calculate real technical indicators
#  from the price history and use rule-based logic to generate insights.
#
#  THREE INDICATORS WE USE:
#
#  1. RSI (Relative Strength Index) — range 0 to 100
#     • Measures if a stock is being over-bought or over-sold
#     • RSI < 35 → stock may be undervalued (BULLISH signal 🟢)
#     • RSI > 70 → stock may be overvalued  (BEARISH signal 🔴)
#     • RSI 35-70 → neutral territory
#
#  2. SMA (Simple Moving Average)
#     • Average closing price over the last N days
#     • SMA-7 (7-day average) vs SMA-21 (21-day average)
#     • When SMA-7 crosses above SMA-21 → "golden cross" (BULLISH 🟢)
#     • When SMA-7 crosses below SMA-21 → "death cross"  (BEARISH 🔴)
#
#  3. Volume Spike
#     • High trading volume = lots of market interest
#     • If today's volume > 1.5× the 10-day average → elevated activity
#
#  Interview talking point:
#  "I implemented technical analysis algorithms from scratch using
#   only Python math. The AI computes RSI, SMA crossovers, and volume
#   spikes, then combines the signals to give a BUY/HOLD/SELL
#   recommendation — all without any external AI API."
# ──────────────────────────────────────────────────────────────

def compute_rsi(prices, period=14):
    """
    Calculate the Relative Strength Index (RSI).

    RSI Formula:
      1. Find daily gains and losses over the last 14 days
      2. Average Gain = sum of gains / 14
      3. Average Loss = sum of losses / 14
      4. RS = Average Gain / Average Loss
      5. RSI = 100 - (100 / (1 + RS))

    Args:
        prices: List of closing prices (oldest → newest)
        period: Number of days to look back (default: 14)
    Returns:
        RSI value (float 0-100), or None if not enough data
    """
    if len(prices) < period + 1:
        return None   # Not enough data points to calculate

    gains  = []   # Days when price went up
    losses = []   # Days when price went down

    for i in range(1, period + 1):
        daily_change = prices[i] - prices[i - 1]
        gains.append(max(daily_change, 0))          # Gain = max(change, 0)
        losses.append(abs(min(daily_change, 0)))    # Loss = abs(min(change, 0))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    if avg_loss == 0:
        return 100.0   # No losses at all = maximum RSI

    rs  = avg_gain / avg_loss          # Relative Strength ratio
    rsi = 100 - (100 / (1 + rs))      # RSI formula
    return round(rsi, 1)


def compute_sma(prices, period):
    """
    Calculate Simple Moving Average (SMA) over the last N prices.

    SMA = sum of last N closing prices / N
    Example: SMA-7 for [10, 12, 11, 13, 14, 12, 15] = (10+12+...+15) / 7

    Args:
        prices: List of closing prices
        period: How many days to average
    Returns:
        SMA value (float), or None if not enough data
    """
    if len(prices) < period:
        return None
    return round(sum(prices[-period:]) / period, 2)


def generate_ai_insight(symbol: str, buy_price: float) -> dict:
    """
    The main AI analysis function.
    Fetches 60 days of price data, calculates indicators, and
    determines a BUY, HOLD, or SELL signal with bullet-point reasoning.

    Args:
        symbol:    Stock ticker symbol (e.g. "AAPL")
        buy_price: Your original purchase price (to show your own P/L)
    Returns:
        A dictionary with signal, headline, and bullet points
    """
    try:
        # STEP 1: Fetch 60 days of historical price data
        ticker  = yf.Ticker(symbol)
        history = ticker.history(period="60d")

        if history.empty or len(history) < 5:
            return {
                "signal": "NEUTRAL",
                "summary": "Not enough data to analyse this stock.",
                "bullets": []
            }

        # STEP 2: Extract closing prices and volumes as Python lists
        closes  = [float(v) for v in history["Close"].tolist()]
        volumes = [float(v) for v in history["Volume"].tolist()]
        latest_price = closes[-1]

        # STEP 3: Calculate all the indicators
        rsi          = compute_rsi(closes)
        sma_7        = compute_sma(closes, 7)
        sma_21       = compute_sma(closes, 21)

        # 5-day price change: how did it move this week?
        week_change = None
        if len(closes) >= 5:
            week_change = round((closes[-1] - closes[-5]) / closes[-5] * 100, 2)

        # 30-day price change: how did it move this month?
        month_change = None
        if len(closes) >= 22:
            month_change = round((closes[-1] - closes[-22]) / closes[-22] * 100, 2)

        # Volume spike: is today's volume higher than usual?
        vol_spike = None
        if len(volumes) >= 10:
            avg_volume = sum(volumes[-10:]) / 10   # 10-day average volume
            if avg_volume > 0:
                vol_spike = round(volumes[-1] / avg_volume, 2)

        # Your personal P&L vs your buy price
        pl_vs_buy = None
        if buy_price and buy_price > 0:
            pl_vs_buy = round((latest_price - buy_price) / buy_price * 100, 2)

        # STEP 4: Tally bullish vs bearish signals
        # More bullish signals → BUY, more bearish → SELL, roughly equal → HOLD
        bullish_signals = 0
        bearish_signals = 0

        if rsi is not None:
            if rsi < 35:   bullish_signals += 2   # Strong bullish (oversold)
            elif rsi > 70: bearish_signals += 2   # Strong bearish (overbought)

        if sma_7 and sma_21:
            if sma_7 > sma_21: bullish_signals += 1   # Positive crossover
            else:              bearish_signals += 1   # Negative crossover

        if week_change is not None:
            if week_change > 3:    bullish_signals += 1  # Strong week
            elif week_change < -3: bearish_signals += 1  # Bad week

        if vol_spike and vol_spike > 1.5:
            bullish_signals += 1   # High volume = market interest

        # STEP 5: Determine final signal based on tally
        if bullish_signals > bearish_signals + 1:
            signal     = "BUY"
            sig_color  = "#00ff88"
            headline   = f"{symbol} shows bullish momentum — uptrend indicators are aligned."
        elif bearish_signals > bullish_signals + 1:
            signal     = "SELL"
            sig_color  = "#ff4466"
            headline   = f"{symbol} shows bearish pressure — consider reviewing your position."
        else:
            signal     = "HOLD"
            sig_color  = "#ffcc00"
            headline   = f"{symbol} is consolidating — mixed signals suggest holding steady."

        # STEP 6: Build the human-readable bullet points
        bullets = []

        if rsi is not None:
            rsi_status = "oversold 🟢" if rsi < 35 else ("overbought 🔴" if rsi > 70 else "neutral ⚪")
            bullets.append(f"RSI = {rsi} — {rsi_status} (under 35 = buy zone, over 70 = sell zone)")

        if sma_7 and sma_21:
            crossover = "above (bullish ↗)" if sma_7 > sma_21 else "below (bearish ↘)"
            bullets.append(f"7-day SMA (${sma_7}) is {crossover} the 21-day SMA (${sma_21})")

        if week_change is not None:
            direction = "📈" if week_change >= 0 else "📉"
            bullets.append(f"5-day price change: {week_change:+.2f}% {direction}")

        if month_change is not None:
            bullets.append(f"30-day price change: {month_change:+.2f}%")

        if vol_spike is not None:
            activity = "(elevated — market is active!)" if vol_spike > 1.5 else "(normal)"
            bullets.append(f"Today's volume: {vol_spike}× the 10-day average {activity}")

        if pl_vs_buy is not None:
            bullets.append(f"Your position P/L vs buy price: {pl_vs_buy:+.2f}%")

        return {
            "signal":    signal,
            "sig_color": sig_color,
            "headline":  headline,
            "bullets":   bullets,
        }

    except Exception as error:
        return {"signal": "ERROR", "summary": str(error), "bullets": []}


# ──────────────────────────────────────────────────────────────
#  SECTION 4: REAL-TIME PRICE STREAMING (Background Thread)
#
#  This function runs in a separate thread so it doesn't block
#  the main Flask server. Every 5 seconds it:
#  1. Fetches latest prices for all stocks
#  2. Calculates P&L figures
#  3. Emits "price_update" event to ALL connected browsers via SocketIO
#
#  Interview talking point:
#  "I used Python's threading module to run price updates in the
#   background. The thread emits a SocketIO event every 5 seconds,
#   which the JavaScript frontend listens for and updates the UI
#   without any page refresh."
# ──────────────────────────────────────────────────────────────

def stream_prices():
    """
    Background thread that continuously fetches prices and pushes
    them to all connected browser clients via WebSocket.

    The 'while True' loop runs forever (as a daemon thread —
    it stops automatically when the main program exits).
    """
    while True:
        try:
            stock_results = []
            total_invested = 0.0
            total_current  = 0.0

            # Loop through every stock in the portfolio
            for symbol, holding_data in list(portfolio.items()):
                quantity  = holding_data.get("quantity", 0)
                buy_price = holding_data.get("buy_price", 0)

                # Calculate financial metrics
                amount_invested = quantity * buy_price
                live_price      = get_live_price(symbol)
                current_value   = quantity * live_price
                profit_loss     = current_value - amount_invested

                # Percentage gain/loss = (profit / invested) × 100
                percent = (profit_loss / amount_invested * 100) if amount_invested > 0 else 0

                total_invested += amount_invested
                total_current  += current_value

                stock_results.append({
                    "symbol":     symbol,
                    "qty":        quantity,
                    "buy_price":  round(buy_price, 2),
                    "live_price": round(live_price, 2),
                    "invested":   round(amount_invested, 2),
                    "current":    round(current_value, 2),
                    "profit":     round(profit_loss, 2),
                    "percent":    round(percent, 2),
                })

            # Portfolio-level totals
            total_pnl = total_current - total_invested
            total_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0

            # Push data to ALL connected browsers simultaneously
            # The JavaScript frontend listens for "price_update" and refreshes the table
            socketio.emit("price_update", {
                "stocks":         stock_results,
                "total_invested": round(total_invested, 2),
                "total_current":  round(total_current, 2),
                "total_pnl":      round(total_pnl, 2),
                "total_pct":      round(total_pct, 2),
                "timestamp":      datetime.now().strftime("%H:%M:%S"),
            })

        except Exception:
            pass   # Silently ignore errors — never crash the streaming thread

        time.sleep(5)   # Wait 5 seconds before the next update


# Start the streaming thread as a daemon (runs in background, stops on exit)
Thread(target=stream_prices, daemon=True).start()


# ──────────────────────────────────────────────────────────────
#  SECTION 5: FLASK ROUTES (REST API ENDPOINTS)
#
#  A "route" is a URL pattern. When a browser visits that URL,
#  Flask calls the function decorated with @app.route().
#
#  @app.route() is a Python DECORATOR — it wraps the function
#  with extra behaviour (url mapping) without changing its code.
#
#  HTTP METHODS:
#  GET  → Browser is asking for data (e.g., loading a page)
#  POST → Browser is sending data (e.g., submitting a form)
# ──────────────────────────────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Main page route.

    GET  request → Render and return the HTML dashboard.
    POST request → Process the Add Stock form, update portfolio, redirect.

    The 'global portfolio' line tells Python we're modifying the
    module-level portfolio variable (not creating a new local one).
    """
    global portfolio

    if request.method == "POST":
        # Read form values submitted from the HTML form
        symbol = request.form.get("symbol", "").upper().strip()

        try:
            quantity  = int(request.form.get("quantity", 0))
            buy_price = float(request.form.get("buy_price", 0))
        except ValueError:
            return redirect("/")   # Invalid input → just reload the page

        # Only add if all inputs are valid
        if symbol and quantity > 0 and buy_price > 0:
            if symbol in portfolio:
                # Stock already exists → calculate weighted average buy price
                # (so adding more shares properly adjusts your cost basis)
                old_qty  = portfolio[symbol]["quantity"]
                old_buy  = portfolio[symbol]["buy_price"]
                new_qty  = old_qty + quantity
                # Weighted average: ((old shares × old price) + (new shares × new price)) / total shares
                new_buy  = (old_qty * old_buy + quantity * buy_price) / new_qty
                portfolio[symbol] = {"quantity": new_qty, "buy_price": round(new_buy, 4)}
            else:
                # New stock → just add it
                portfolio[symbol] = {"quantity": quantity, "buy_price": buy_price}

            save_portfolio(portfolio)   # Persist changes to JSON file

        return redirect("/")   # Redirect back to the dashboard (GET request)

    # GET request → just show the dashboard HTML
    return render_template("index.html")


@app.route("/remove/<symbol>", methods=["POST"])
def remove_stock(symbol):
    """
    Remove a stock from the portfolio.

    URL pattern: /remove/AAPL  (symbol comes from the URL)
    Returns JSON: {"status": "ok", "removed": "AAPL"}

    The frontend JavaScript calls this with fetch() and removes
    the table row with a fade-out animation.
    """
    global portfolio
    symbol = symbol.upper()

    if symbol in portfolio:
        del portfolio[symbol]
        save_portfolio(portfolio)

    return jsonify({"status": "ok", "removed": symbol})


@app.route("/ai-insight/<symbol>")
def ai_insight(symbol):
    """
    Return AI analysis for a given stock as JSON.

    When the user clicks a stock row in the dashboard, the JavaScript
    calls /ai-insight/AAPL (for example), and this function returns
    the analysis which is then displayed in the AI panel.
    """
    symbol    = symbol.upper()
    buy_price = portfolio.get(symbol, {}).get("buy_price", 0)
    insight   = generate_ai_insight(symbol, buy_price)
    return jsonify(insight)


@app.route("/chart-data/<symbol>")
def chart_data(symbol):
    """
    Return 30-day price history for a stock as JSON.
    Used by the Chart.js line graph in the frontend.
    Example response: [{"date": "Feb 01", "close": 150.5}, ...]
    """
    symbol = symbol.upper()
    data   = get_price_history(symbol, days=30)
    return jsonify(data)

# ──────────────────────────────────────────────────────────────
#  ENTRY POINT
#  Start the Flask-SocketIO server on http://127.0.0.1:5000
#  debug=True → auto-reloads the server when code changes (dev mode)
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n📈 Stock Portfolio Tracker")
    print("   Starting server...")
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, debug=False, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)
