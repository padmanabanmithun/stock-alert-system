import yfinance as yf
import pytz
import datetime
import json
import os
import pandas as pd
from email_service import send_email

IST = pytz.timezone("Asia/Kolkata")


def is_market_open():
    now = datetime.datetime.now(IST)

    if now.weekday() >= 5:
        return False

    with open("holidays.json", "r") as f:
        holidays = json.load(f)

    today_str = now.strftime("%Y-%m-%d")

    if today_str in holidays:
        return False

    market_open = now.replace(hour=9, minute=15, second=0)
    market_close = now.replace(hour=15, minute=30, second=0)

    return market_open <= now <= market_close


def load_stocks():
    with open("portfolio.txt") as f:
        portfolio = [line.strip() for line in f.readlines()]

    with open("wishlist.txt") as f:
        wishlist = [line.strip() for line in f.readlines()]

    return portfolio, wishlist


def load_alerts():
    if os.path.exists("alerts_sent.json"):
        with open("alerts_sent.json", "r") as f:
            return json.load(f)
    return {}


def save_alerts(data):
    with open("alerts_sent.json", "w") as f:
        json.dump(data, f)


def already_alerted(stock, alerts):
    today = datetime.datetime.now(IST).strftime("%Y-%m-%d")

    if today not in alerts:
        alerts[today] = []

    return stock in alerts[today]


def mark_alert(stock, alerts):
    today = datetime.datetime.now(IST).strftime("%Y-%m-%d")
    alerts[today].append(stock)
    save_alerts(alerts)


def get_ratio_info(stock):

    ticker = yf.Ticker(stock)
    info = ticker.info

    industry = str(info.get("industry", ""))
    industry_main = industry.split("-")[0].strip().lower()

    emoji = "❌"
    ratio_text = ""

    # BANK LOGIC
    if industry_main == "banks":

        ratio = info.get("priceToBook")

        if ratio is not None and ratio < 1:
            emoji = "✅"

        ratio_display = "N/A" if ratio is None else f"{ratio:.2f}"

        ratio_text = f"""
Price to Book: {emoji}
Actual Ratio: {ratio_display}
"""

    # OTHER STOCKS
    else:

        ratio = info.get("trailingPE")

        if ratio is not None and ratio < 20:
            emoji = "✅"

        ratio_display = "N/A" if ratio is None else f"{ratio:.2f}"

        ratio_text = f"""
P/E Ratio: {emoji}
Actual Ratio: {ratio_display}
"""

    return emoji, ratio_text


def check_stocks():

    portfolio, wishlist = load_stocks()
    all_stocks = portfolio + wishlist

    alerts = load_alerts()

    data = yf.download(
        all_stocks,
        period="5d",
        interval="1d",
        group_by="ticker",
        progress=False,
        threads=False
    )

    for stock in all_stocks:

        if already_alerted(stock, alerts):
            continue

        try:
            stock_data = data[stock]
        except Exception:
            continue

        closes = stock_data["Close"].dropna()

        if len(closes) < 2:
            continue

        previous_close = closes.iloc[-2]
        current_price = closes.iloc[-1]

        if pd.isna(previous_close) or pd.isna(current_price):
            continue

        drop_percent = ((previous_close - current_price) / previous_close) * 100

        if drop_percent < 3:
            continue

        # GOLD LOGIC
        if stock == "GOLD1.NS":

            subject = f"🟡 Gold Crashed {drop_percent:.2f}%"

            body = f"""
Asset: Gold ETF ({stock})

Current Price: {current_price:.2f}
Previous Close: {previous_close:.2f}

Gold Crash: {drop_percent:.2f}%
"""

        else:

            emoji, ratio_text = get_ratio_info(stock)

            if stock in portfolio:
                subject = f"{emoji} HOLDING : {stock} crash {drop_percent:.2f}% 🚨"
            else:
                subject = f"{emoji} WISHLIST : {stock} crash {drop_percent:.2f}% 🚨"

            body = f"""
Stock: {stock}

Current Price: {current_price:.2f}
Previous Close: {previous_close:.2f}

Crash: {drop_percent:.2f}%

{ratio_text}
"""

        send_email(subject, body)

        mark_alert(stock, alerts)


if __name__ == "__main__":
    if is_market_open():
        check_stocks()