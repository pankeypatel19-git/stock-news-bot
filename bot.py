import requests
import telegram
import schedule
import time
from bs4 import BeautifulSoup

TOKEN = "8350282877:AAFtkC2x_otxzzGPj4v7fKGYn6T05nU6Zxo"
CHAT_ID = "7664038478"

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

# ⏰ Runs every day at 08:00 AM
schedule.every().day.at("08:00").do(send_news)

print("Bot running... Waiting for 08:00 AM")

while True:
    schedule.run_pending()
    time.sleep(30)
