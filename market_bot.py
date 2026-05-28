import requests
import schedule
import time
import os

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def fetch_gold_price():
    try:
        url = "https://api.metals.live/v1/spot/gold"
        response = requests.get(url, timeout=10)
        data = response.json()
        price = round(data[0]["price"], 2)
        return f"🥇 XAUUSD (Gold) Spot Price\n\nCurrent Price: ${price} per oz\n\n#XAUUSD #Gold #Commodities"
    except Exception as e:
        print(f"Gold price error: {e}")
        return None

def fetch_market_news():
    try:
        # Using RSS2JSON free service to parse RSS
        feeds = [
            ("Nifty/Markets", "https://rss.app/feeds/tODCqlDsJ1kLkqXX.xml"),
        ]
        url = "https://api.rss2json.com/v1/api.json?rss_url=https://www.livemint.com/rss/markets"
        response = requests.get(url, timeout=15)
        data = response.json()
        if data.get("status") == "ok":
            items = data.get("items", [])
            if items:
                item = items[0]
                title = item.get("title", "")
                return f"📊 Market News:\n\n{title}\n\n#Nifty #Markets #NSE"
    except Exception as e:
        print(f"News error: {e}")
    return None

def fetch_nifty_update():
    try:
        url = "https://api.rss2json.com/v1/api.json?rss_url=https://economictimes.indiatimes.com/markets/stocks/rss.cms"
        response = requests.get(url, timeout=15)
        data = response.json()
        if data.get("status") == "ok":
            items = data.get("items", [])
            if items:
                title = items[0].get("title", "")
                return f"📈 Stock Market Update:\n\n{title}\n\n#Nifty #NSE #BSE"
    except Exception as e:
        print(f"Nifty error: {e}")
    return None

JOBS = [fetch_nifty_update, fetch_gold_price, fetch_market_news]

sent_messages = set()

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    response = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})
    print(f"Telegram status: {response.status_code}")
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Error: {response.text[:200]}")

def job():
    print("Fetching market update...")
    index = int(time.time() / 3600) % len(JOBS)
    result = JOBS[index]()
    if result and result not in sent_messages:
        sent_messages.add(result)
        if len(sent_messages) > 50:
            sent_messages.clear()
        send_to_telegram(result)
    else:
        print("No new update found.")

print(f"Token set: {'Yes' if TELEGRAM_TOKEN else 'NO - MISSING!'}")
print(f"Chat ID set: {'Yes' if TELEGRAM_CHAT_ID else 'NO - MISSING!'}")

job()
schedule.every(1).hours.do(job)

print("Bot running! Updates every hour...")
while True:
    schedule.run_pending()
    time.sleep(60)
