import requests
import telegram
import time
from bs4 import BeautifulSoup
import os
import pytz
from datetime import datetime


TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

print("DEBUG TOKEN:", TOKEN)
print("DEBUG CHAT_ID:", CHAT_ID)

if not TOKEN:
    raise Exception("BOT_TOKEN is not set in environment variables")

bot = telegram.Bot(token=TOKEN)

def get_moneycontrol_headlines():
    url = "https://www.moneycontrol.com/news/business/"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    headlines = []
    for item in soup.select("li.clearfix")[:5]:
        title = item.find("h2")
        if title:
            headlines.append(title.text.strip())

    return headlines

def morning_brief():
    headlines = get_moneycontrol_headlines()

    message = "📈 Morning Market Brief – India\n\n"

    for h in headlines:
        message += f"• {h}\n\n"

    message += "\nHave a disciplined trading day."

    return message

def send_news():
    news = morning_brief()
    bot.send_message(chat_id=CHAT_ID, text=news)

IST = pytz.timezone("Asia/Kolkata")

print("Bot running... Waiting for 08:00 AM IST")

while True:
    now_utc = datetime.utcnow()
    now_ist = now_utc.replace(tzinfo=pytz.utc).astimezone(IST)

    if now_ist.hour == 8 and now_ist.minute == 0:
        print("Sending morning update at 8:00 AM IST...")
        send_news()
        time.sleep(60)

    time.sleep(20)