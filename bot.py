import requests
import telegram
import time
import os
import pytz
import feedparser
import json
from datetime import datetime

TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TOKEN:
    raise Exception("BOT_TOKEN is not set in environment variables")

bot = telegram.Bot(token=TOKEN)

IST = pytz.timezone("Asia/Kolkata")

# --- NIFTY 200 Sample (Expand later fully) ---
STOCK_MAP = {
    "RELIANCE": ["Reliance Industries", "RIL"],
    "TCS": ["Tata Consultancy Services", "TCS"],
    "HDFCBANK": ["HDFC Bank"],
    "INFY": ["Infosys"],
    "ICICIBANK": ["ICICI Bank"]
}

BUY_KEYWORDS = ["increases stake", "buys", "acquires", "allotment"]
SELL_KEYWORDS = ["reduces stake", "sells", "divests", "offloads"]

RSS_QUERIES = [
    "promoter increases stake India",
    "mutual fund buys stake India",
    "bulk deal NSE",
    "block deal BSE"
]

SEEN_FILE = "seen_links.json"

# --- Load seen links ---
try:
    with open(SEEN_FILE, "r") as f:
        seen_links = set(json.load(f))
except:
    seen_links = set()

daily_events = []

def save_seen_links():
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_links), f)

def classify_news(title):
    title_lower = title.lower()

    action = None
    if any(word in title_lower for word in BUY_KEYWORDS):
        action = "🟢 Buying"
    elif any(word in title_lower for word in SELL_KEYWORDS):
        action = "🔴 Selling"

    for symbol, names in STOCK_MAP.items():
        for name in names:
            if name.lower() in title_lower:
                return symbol, action

    return None, None

def scan_news():
    global daily_events

    for query in RSS_QUERIES:
        url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}"
        feed = feedparser.parse(url)

        for entry in feed.entries:
            if entry.link in seen_links:
                continue

            symbol, action = classify_news(entry.title)

            if symbol and action:
                message = f"{action} Alert\n\nStock: {symbol}\nNews: {entry.title}"
                bot.send_message(chat_id=CHAT_ID, text=message)

                daily_events.append(message)
                seen_links.add(entry.link)
                save_seen_links()

def morning_summary():
    global daily_events

    if not daily_events:
        summary = "📊 Institutional Activity Summary\n\nNo major institutional activity detected."
    else:
        summary = "📊 Institutional Activity Summary\n\n"
        for event in daily_events:
            summary += event + "\n\n"

    bot.send_message(chat_id=CHAT_ID, text=summary)
    daily_events = []

print("Institutional Flow Bot Running (Hybrid Mode)")

last_scan_minute = -1

while True:
    now_utc = datetime.utcnow()
    now_ist = now_utc.replace(tzinfo=pytz.utc).astimezone(IST)

    # --- Every 15 minutes real-time scan ---
    if now_ist.minute % 15 == 0 and now_ist.minute != last_scan_minute:
        scan_news()
        last_scan_minute = now_ist.minute

    # --- 8 AM IST Summary ---
    if now_ist.hour == 8 and now_ist.minute == 0:
        morning_summary()
        time.sleep(60)

    time.sleep(20)
