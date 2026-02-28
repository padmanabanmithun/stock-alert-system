import yfinance as yf
import pytz
import datetime
import json
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

    return portfolio + wishlist


def check_stocks():
    stocks = load_stocks()
    alerted_today = set()

    for stock in stocks:
        ticker = yf.Ticker(stock)
        data = ticker.history(period="2d")
        info = ticker.info

        if len(data) < 2:
            continue

        previous_close = data["Close"].iloc[-2]
        current_price = data["Close"].iloc[-1]
        fifty_two_low = info.get("fiftyTwoWeekLow")

        drop_percent = ((previous_close - current_price) / previous_close) * 100

        if drop_percent >= 5 and stock not in alerted_today:
            subject = f"🚨 5% Crash Alert: {stock}"
            body = f"{stock} dropped {drop_percent:.2f}%.\nCurrent: {current_price}"
            send_email(subject, body)
            alerted_today.add(stock)

        if fifty_two_low and current_price <= fifty_two_low and stock not in alerted_today:
            subject = f"📉 52W Low Alert: {stock}"
            body = f"{stock} hit 52-week low.\nCurrent: {current_price}"
            send_email(subject, body)
            alerted_today.add(stock)


if __name__ == "__main__":
    if is_market_open():
        check_stocks()