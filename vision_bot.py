#!/usr/bin/env python3
"""
🤖 Vision Bot — Telegram Unified Bot
يخدم BTCvision.org و SolanaVision.org
- تنبيهات الزوار الجدد
- تقرير يومي
- تنبيهات السعر BTC و SOL
"""

import requests
import time
import json
import threading
from datetime import datetime, date
import schedule

# ═══════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════
BOT_TOKEN = "8927812046:AAHdEkFO4K1-7Q_01gROaThVbUtqihWaF4Y"
CHAT_ID = "446628442"

# Supabase
SB_BTC_URL = "https://dcemgonadsuwwagyaahu.supabase.co"
SB_BTC_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRjZW1nb25hZHN1d3dhZ3lhYWh1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODAwNTkyNzMsImV4cCI6MjA5NTYzNTI3M30.3ZAZXt3HUiIEhTE7ES_bRVYHs9sYj_hN2GGjIchsc3M"

SB_SOL_URL = "https://ztovrrqksbohqpeelsxa.supabase.co"
SB_SOL_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp0b3ZycnFrc2JvaHFwZWVsc3hhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODExMTMyMzYsImV4cCI6MjA5NjY4OTIzNn0.BgcV5Rr6M7SVIeSszND_q5DTLuxOALr89Uq6dcDw8Hc"

# Price alert thresholds (%)
PRICE_ALERT_THRESHOLD = 3.0

# Track last known prices
last_btc_price = None
last_sol_price = None
last_visitor_count_btc = 0
last_visitor_count_sol = 0

# ═══════════════════════════════════════
# TELEGRAM
# ═══════════════════════════════════════
def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        r = requests.post(url, json=payload, timeout=10)
        return r.json()
    except Exception as e:
        print(f"Telegram error: {e}")
        return None

# ═══════════════════════════════════════
# PRICES
# ═══════════════════════════════════════
def get_prices():
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/24hr",
            params={"symbols": '["BTCUSDT","SOLUSDT"]'},
            timeout=10
        )
        data = r.json()
        btc = next((x for x in data if x['symbol'] == 'BTCUSDT'), None)
        sol = next((x for x in data if x['symbol'] == 'SOLUSDT'), None)
        return {
            'btc': {'price': float(btc['lastPrice']), 'change': float(btc['priceChangePercent'])},
            'sol': {'price': float(sol['lastPrice']), 'change': float(sol['priceChangePercent'])}
        } if btc and sol else None
    except Exception as e:
        print(f"Price fetch error: {e}")
        return None

def check_price_alerts():
    global last_btc_price, last_sol_price
    prices = get_prices()
    if not prices:
        return

    btc = prices['btc']
    sol = prices['sol']

    # BTC alert
    if last_btc_price:
        change_pct = abs((btc['price'] - last_btc_price) / last_btc_price * 100)
        if change_pct >= PRICE_ALERT_THRESHOLD:
            direction = "🚀" if btc['price'] > last_btc_price else "📉"
            msg = f"""{direction} <b>BTC PRICE ALERT</b>

💰 Price: <b>${btc['price']:,.0f}</b>
📊 24h Change: {btc['change']:+.2f}%
🔗 <a href="https://btcvision.org">btcvision.org</a>"""
            send_telegram(msg)

    # SOL alert
    if last_sol_price:
        change_pct = abs((sol['price'] - last_sol_price) / last_sol_price * 100)
        if change_pct >= PRICE_ALERT_THRESHOLD:
            direction = "🚀" if sol['price'] > last_sol_price else "📉"
            msg = f"""{direction} <b>SOL PRICE ALERT</b>

💰 Price: <b>${sol['price']:,.2f}</b>
📊 24h Change: {sol['change']:+.2f}%
🔗 <a href="https://solanavision.org">solanavision.org</a>"""
            send_telegram(msg)

    last_btc_price = btc['price']
    last_sol_price = sol['price']

# ═══════════════════════════════════════
# VISITORS
# ═══════════════════════════════════════
def get_visitors(sb_url, sb_key, site_name):
    try:
        headers = {"apikey": sb_key, "Authorization": f"Bearer {sb_key}"}
        r = requests.get(
            f"{sb_url}/rest/v1/visitors",
            headers=headers,
            params={"select": "id,country,city,browser,device,wallet_detected,created_at",
                    "order": "created_at.desc", "limit": "500"},
            timeout=10
        )
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        print(f"Visitor fetch error ({site_name}): {e}")
        return []

def check_new_visitors():
    global last_visitor_count_btc, last_visitor_count_sol

    # BTCvision
    btc_visitors = get_visitors(SB_BTC_URL, SB_BTC_KEY, "BTCvision")
    if btc_visitors and len(btc_visitors) > last_visitor_count_btc and last_visitor_count_btc > 0:
        new_count = len(btc_visitors) - last_visitor_count_btc
        latest = btc_visitors[0]
        wallet = f"✅ {latest.get('wallet_detected','')}" if latest.get('wallet_detected') and latest.get('wallet_detected') != 'none' else "—"
        msg = f"""👁️ <b>BTCvision — {new_count} زائر جديد</b>

🌍 {latest.get('country','?')} {f"· {latest.get('city','')}" if latest.get('city') else ''}
🌐 {latest.get('browser','?')} · {latest.get('device','?')}
💰 Wallet: {wallet}
📊 Total: {len(btc_visitors)} زائر"""
        send_telegram(msg)
    last_visitor_count_btc = len(btc_visitors) if btc_visitors else last_visitor_count_btc

    # SolanaVision
    sol_visitors = get_visitors(SB_SOL_URL, SB_SOL_KEY, "SolanaVision")
    if sol_visitors and len(sol_visitors) > last_visitor_count_sol and last_visitor_count_sol > 0:
        new_count = len(sol_visitors) - last_visitor_count_sol
        latest = sol_visitors[0]
        wallet = f"✅ {latest.get('wallet_detected','')}" if latest.get('wallet_detected') and latest.get('wallet_detected') != 'none' else "—"
        msg = f"""👁️ <b>SolanaVision — {new_count} زائر جديد</b>

🌍 {latest.get('country','?')} {f"· {latest.get('city','')}" if latest.get('city') else ''}
🌐 {latest.get('browser','?')} · {latest.get('device','?')}
💰 Wallet: {wallet}
📊 Total: {len(sol_visitors)} زائر"""
        send_telegram(msg)
    last_visitor_count_sol = len(sol_visitors) if sol_visitors else last_visitor_count_sol

# ═══════════════════════════════════════
# DAILY REPORT
# ═══════════════════════════════════════
def send_daily_report():
    prices = get_prices()
    btc_visitors = get_visitors(SB_BTC_URL, SB_BTC_KEY, "BTCvision")
    sol_visitors = get_visitors(SB_SOL_URL, SB_SOL_KEY, "SolanaVision")

    today = date.today().isoformat()

    # Count today's visitors
    btc_today = [v for v in btc_visitors if v.get('created_at','').startswith(today)] if btc_visitors else []
    sol_today = [v for v in sol_visitors if v.get('created_at','').startswith(today)] if sol_visitors else []

    # Count wallets
    btc_wallets = [v for v in btc_visitors if v.get('wallet_detected') and v.get('wallet_detected') != 'none'] if btc_visitors else []
    sol_wallets = [v for v in sol_visitors if v.get('wallet_detected') and v.get('wallet_detected') != 'none'] if sol_visitors else []

    btc_price_str = f"${prices['btc']['price']:,.0f} ({prices['btc']['change']:+.2f}%)" if prices else "N/A"
    sol_price_str = f"${prices['sol']['price']:,.2f} ({prices['sol']['change']:+.2f}%)" if prices else "N/A"

    msg = f"""📊 <b>DAILY REPORT — {today}</b>

━━━━━━━━━━━━━━━━
💛 <b>BTCvision.org</b>
👁️ Today: {len(btc_today)} | Total: {len(btc_visitors)}
💰 Wallets: {len(btc_wallets)}
₿ BTC: {btc_price_str}

━━━━━━━━━━━━━━━━
🟣 <b>SolanaVision.org</b>
👁️ Today: {len(sol_today)} | Total: {len(sol_visitors)}
💰 Wallets: {len(sol_wallets)}
◎ SOL: {sol_price_str}

━━━━━━━━━━━━━━━━
🔗 <a href="https://btcvision.org/dashboard.html">BTCvision Dashboard</a>
🔗 <a href="https://solanavision.org/dashboard.html">SolanaVision Dashboard</a>"""

    send_telegram(msg)

# ═══════════════════════════════════════
# STARTUP MESSAGE
# ═══════════════════════════════════════
def send_startup():
    prices = get_prices()
    btc_str = f"${prices['btc']['price']:,.0f}" if prices else "N/A"
    sol_str = f"${prices['sol']['price']:,.2f}" if prices else "N/A"
    msg = f"""🤖 <b>Vision Bot Started!</b>

✅ BTCvision.org — monitoring
✅ SolanaVision.org — monitoring

₿ BTC: {btc_str}
◎ SOL: {sol_str}

📡 Alerts: visitors + prices (+{PRICE_ALERT_THRESHOLD}%)
📊 Daily report: 9:00 AM"""
    send_telegram(msg)

# ═══════════════════════════════════════
# MAIN
# ═══════════════════════════════════════
def main():
    print("🚀 Vision Bot starting...")

    # Initialize visitor counts
    global last_visitor_count_btc, last_visitor_count_sol
    btc_v = get_visitors(SB_BTC_URL, SB_BTC_KEY, "BTCvision")
    sol_v = get_visitors(SB_SOL_URL, SB_SOL_KEY, "SolanaVision")
    last_visitor_count_btc = len(btc_v) if btc_v else 0
    last_visitor_count_sol = len(sol_v) if sol_v else 0

    # Initialize prices
    global last_btc_price, last_sol_price
    prices = get_prices()
    if prices:
        last_btc_price = prices['btc']['price']
        last_sol_price = prices['sol']['price']

    # Send startup message
    send_startup()

    # Schedule tasks
    schedule.every(2).minutes.do(check_new_visitors)      # Check new visitors every 2 min
    schedule.every(5).minutes.do(check_price_alerts)      # Check price alerts every 5 min
    schedule.every().day.at("09:00").do(send_daily_report) # Daily report at 9 AM

    print("✅ Bot running!")
    print(f"📊 BTCvision visitors: {last_visitor_count_btc}")
    print(f"📊 SolanaVision visitors: {last_visitor_count_sol}")

    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()
