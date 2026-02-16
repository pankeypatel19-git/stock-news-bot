import requests
import telegram
import time
import os
import pytz
import feedparser
import json
from datetime import datetime, timedelta

# ==============================
# ENVIRONMENT VARIABLES
# ==============================

TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TOKEN:
    raise Exception("BOT_TOKEN is not set in environment variables")

if not CHAT_ID:
    raise Exception("CHAT_ID is not set in environment variables")

bot = telegram.Bot(token=TOKEN)

IST = pytz.timezone("Asia/Kolkata")

# ==============================
# LOAD NIFTY 200 LIST
# ==============================

def load_nifty_200():
    url = "https://archives.nseindia.com/content/indices/ind_nifty200list.csv"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/csv"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()

        lines = r.text.split("\n")
        stock_map = {}

        for line in lines[1:]:
            parts = line.split(",")

            if len(parts) >= 2:
                company_name = parts[0].strip()
                symbol = parts[1].strip()

                if symbol:
                    stock_map[symbol] = [company_name, symbol]

        print(f"Loaded {len(stock_map)} NIFTY 200 stocks.")
        return stock_map

    except Exception as e:
        print("Error loading NIFTY 200:", e)
        return {}

STOCK_MAP = load_nifty_200()

if not STOCK_MAP:
    print("Warning: Could not load NIFTY 200 list.")

# ==============================
# CONFIGURATION
# ==============================

BUY_KEYWORDS = ["increases stake", "buys", "acquires", "allotment"]
SELL_KEYWORDS = ["reduces stake", "sells", "divests", "offloads"]

RSS_QUERIES = [
    "promoter increases stake India",
    "mutual fund buys stake India",
    "bulk deal NSE",
    "block deal BSE"
]

SEEN_FILE = "seen_links.json"

# ==============================
# LOAD SEEN LINKS
# ==============================

try:
    with open(SEEN_FILE, "r") as f:
        seen_links = set(json.load(f))
except:
    seen_links = set()

daily_events = []

def save_seen_links():
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_links), f)

# ==============================
# TIME FILTER (ONLY RECENT NEWS)
# ==============================

def is_recent(entry, hours=6):
    """
    Returns True if article was published within last X hours.
    Default: 6 hours.
    """

    if not hasattr(entry, "published_parsed") or entry.published_parsed is None:
        return False

    try:
        published_time = datetime(*entry.published_parsed[:6])
        published_time = pytz.utc.localize(published_time)

        now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

        return now_utc - published_time <= timedelta(hours=hours)

    except Exception:
        return False

# ==============================
# CLASSIFY NEWS
# ==============================

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

# ==============================
# SCAN RSS NEWS
# ==============================

def scan_news():
    global daily_events

    print("Scanning news...")

    for query in RSS_QUERIES:
        try:
            url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}"
            feed = feedparser.parse(url)

            for entry in feed.entries:

                # Skip old news
                if not is_recent(entry, hours=6):
                    continue

                if entry.link in seen_links:
                    continue

                symbol, action = classify_news(entry.title)

                if symbol:
                    label = action or "⚪ Institutional Update"

                    message = (
                        f"{label} Alert\n\n"
                        f"Stock: {symbol}\n"
                        f"News: {entry.title}"
                    )

                    bot.send_message(chat_id=CHAT_ID, text=message)

                    daily_events.append(message)
                    seen_links.add(entry.link)
                    save_seen_links()

        except Exception as e:
            print("Error scanning RSS:", e)

# ==============================
# MORNING SUMMARY (8 AM IST)
# ==============================

def morning_summary():
    global daily_events

    if not daily_events:
        summary = (
            "📊 Institutional Activity Summary\n\n"
            "No major institutional activity detected."
        )
    else:
        summary = "📊 Institutional Activity Summary\n\n"

        for event in daily_events:
            summary += event + "\n\n"

    bot.send_message(chat_id=CHAT_ID, text=summary)

    daily_events = []

# ==============================
# MAIN LOOP
# ==============================

print("Institutional Flow Bot Running (Hybrid Mode)")

last_scan_minute = -1

while True:
    try:
        now_utc = datetime.utcnow()
        now_ist = now_utc.replace(tzinfo=pytz.utc).astimezone(IST)

        # Every 15 minutes
        if now_ist.minute % 15 == 0 and now_ist.minute != last_scan_minute:
            scan_news()
            last_scan_minute = now_ist.minute

        # 8 AM Summary
        if now_ist.hour == 8 and now_ist.minute == 0:
            morning_summary()
            time.sleep(60)

        time.sleep(20)

    except Exception as e:
        print("Main loop error:", e)
        time.sleep(30)


