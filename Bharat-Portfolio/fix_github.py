import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Connect to the user's existing Chrome session (since they are logged in)
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        
        # Open a new page and go to the edit URL
        page = await context.new_page()
        await page.goto("https://github.com/venomy46/Bharath-portfolio/edit/main/Bharat-Portfolio/app.py")
        
        # Wait for the CodeMirror editor to load
        await page.wait_for_selector(".cm-content")
        
        # Use evaluation to completely replace the editor's text
        # This bypasses all typing/indentation UI bugs
        new_content = """import json
import os
import time
from datetime import datetime
from threading import Thread

import yfinance as yf
from flask import Flask, render_template, request, redirect, jsonify, send_file
from flask_socketio import SocketIO

app = Flask(__name__)
app.config["SECRET_KEY"] = "stockai-secret-2025"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "portfolio.json")

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as file:
            return json.load(file)
    return {}

def save_portfolio(data):
    with open(PORTFOLIO_FILE, "w") as file:
        json.dump(data, file, indent=4)

portfolio = load_portfolio()
_price_cache = {}
CACHE_SECONDS = 30

def get_live_price(symbol: str) -> float:
    now = time.time()
    if symbol in _price_cache:
        cached_price, cached_time = _price_cache[symbol]
        if now - cached_time < CACHE_SECONDS:
            return cached_price
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="2d")
        if not history.empty:
            price = float(history["Close"].iloc[-1])
            _price_cache[symbol] = (price, now)
            return price
    except Exception:
        pass
    return _price_cache.get(symbol, (0, 0))[0]

def get_price_history(symbol: str, days: int = 30):
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=f"{days}d")
        result = []
        for date_index, row in history.iterrows():
            result.append({
                "date":  date_index.strftime("%b %d"),
                "close": round(float(row["Close"]), 2),
            })
        return result
    except Exception:
        return []

def compute_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    gains  = []
    losses = []
    for i in range(1, period + 1):
        daily_change = prices[i] - prices[i - 1]
        gains.append(max(daily_change, 0))
        losses.append(abs(min(daily_change, 0)))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs  = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 1)

def compute_sma(prices, period):
    if len(prices) < period:
        return None
    return round(sum(prices[-period:]) / period, 2)

def generate_ai_insight(symbol: str, buy_price: float) -> dict:
    try:
        ticker  = yf.Ticker(symbol)
        history = ticker.history(period="60d")
        if history.empty or len(history) < 5:
            return {
                "signal": "NEUTRAL",
                "summary": "Not enough data to analyse this stock.",
                "bullets": []
            }
        closes  = [float(v) for v in history["Close"].tolist()]
        volumes = [float(v) for v in history["Volume"].tolist()]
        latest_price = closes[-1]
        rsi          = compute_rsi(closes)
        sma_7        = compute_sma(closes, 7)
        sma_21       = compute_sma(closes, 21)
        week_change = None
        if len(closes) >= 5:
            week_change = round((closes[-1] - closes[-5]) / closes[-5] * 100, 2)
        month_change = None
        if len(closes) >= 22:
            month_change = round((closes[-1] - closes[-22]) / closes[-22] * 100, 2)
        vol_spike = None
        if len(volumes) >= 10:
            avg_volume = sum(volumes[-10:]) / 10
            if avg_volume > 0:
                vol_spike = round(volumes[-1] / avg_volume, 2)
        pl_vs_buy = None
        if buy_price and buy_price > 0:
            pl_vs_buy = round((latest_price - buy_price) / buy_price * 100, 2)
            
        bullish_signals = 0
        bearish_signals = 0
        if rsi is not None:
            if rsi < 35:   bullish_signals += 2
            elif rsi > 70: bearish_signals += 2
        if sma_7 and sma_21:
            if sma_7 > sma_21: bullish_signals += 1
            else:              bearish_signals += 1
        if week_change is not None:
            if week_change > 3:    bullish_signals += 1
            elif week_change < -3: bearish_signals += 1
        if vol_spike and vol_spike > 1.5:
            bullish_signals += 1

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

def stream_prices():
    while True:
        try:
            stock_results = []
            total_invested = 0.0
            total_current  = 0.0
            for symbol, holding_data in list(portfolio.items()):
                quantity  = holding_data.get("quantity", 0)
                buy_price = holding_data.get("buy_price", 0)
                amount_invested = quantity * buy_price
                live_price      = get_live_price(symbol)
                current_value   = quantity * live_price
                profit_loss     = current_value - amount_invested
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
            total_pnl = total_current - total_invested
            total_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0
            socketio.emit("price_update", {
                "stocks":         stock_results,
                "total_invested": round(total_invested, 2),
                "total_current":  round(total_current, 2),
                "total_pnl":      round(total_pnl, 2),
                "total_pct":      round(total_pct, 2),
                "timestamp":      datetime.now().strftime("%H:%M:%S"),
            })
        except Exception:
            pass
        time.sleep(5)

Thread(target=stream_prices, daemon=True).start()

@app.route("/", methods=["GET", "POST"])
def index():
    global portfolio
    if request.method == "POST":
        symbol = request.form.get("symbol", "").upper().strip()
        try:
            quantity  = int(request.form.get("quantity", 0))
            buy_price = float(request.form.get("buy_price", 0))
        except ValueError:
            return redirect("/")
        if symbol and quantity > 0 and buy_price > 0:
            if symbol in portfolio:
                old_qty  = portfolio[symbol]["quantity"]
                old_buy  = portfolio[symbol]["buy_price"]
                new_qty  = old_qty + quantity
                new_buy  = (old_qty * old_buy + quantity * buy_price) / new_qty
                portfolio[symbol] = {"quantity": new_qty, "buy_price": round(new_buy, 4)}
            else:
                portfolio[symbol] = {"quantity": quantity, "buy_price": buy_price}
            save_portfolio(portfolio)
        return redirect("/")
    return render_template("index.html")

@app.route("/remove/<symbol>", methods=["POST"])
def remove_stock(symbol):
    global portfolio
    symbol = symbol.upper()
    if symbol in portfolio:
        del portfolio[symbol]
        save_portfolio(portfolio)
    return jsonify({"status": "ok", "removed": symbol})

@app.route("/ai-insight/<symbol>")
def ai_insight(symbol):
    symbol    = symbol.upper()
    buy_price = portfolio.get(symbol, {}).get("buy_price", 0)
    insight   = generate_ai_insight(symbol, buy_price)
    return jsonify(insight)

@app.route("/chart-data/<symbol>")
def chart_data(symbol):
    symbol = symbol.upper()
    data   = get_price_history(symbol, days=30)
    return jsonify(data)

if __name__ == "__main__":
    print("\\n📈 Stock Portfolio Tracker")
    print("   Starting server...")
    import os
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, debug=False, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)
"""
        
        # Inject the text into CodeMirror instance
        await page.evaluate(f'''() => {{
            const editor = document.querySelector('.cm-content');
            if(editor && editor.cmView) {{
                const view = editor.cmView.view;
                view.dispatch({{
                    changes: {{from: 0, to: view.state.doc.length, insert: `{new_content}`}}
                }});
            }}
        }}''')
        
        # Give UI a moment to register changes
        await page.wait_for_timeout(1000)
        
        # Click "Commit changes..."
        await page.click('button:has-text("Commit changes...")')
        await page.wait_for_selector('text="Commit changes"', state="visible")
        
        # Click the confirm "Commit changes" button in the dialog
        await page.click('button[data-testid="code-editor-commit-button"]')
        
        # Wait for navigation back to the file view
        await page.wait_for_url("**/Bharath-portfolio/blob/main/**")
        print("Success! Github file successfully updated.")
        
        await page.close()

asyncio.run(run())
