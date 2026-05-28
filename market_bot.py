import requests
import schedule
import time
import xml.etree.ElementTree as ET

TELEGRAM_TOKEN   = "8631241825:AAH27LMk13fvf5P7iL-FvUT6Txot0-T3pYw"
TELEGRAM_CHAT_ID = "8396729316"

# Free RSS news feeds for Indian markets & Gold
RSS_FEEDS = [
    ("Nifty/Sensex", "https://economictimes.indiatimes.com/markets/stocks/rss.cms"),
    ("XAUUSD/Gold",  "https://economictimes.indiatimes.com/markets/commodities/rss.cms"),
    ("Stock News",   "https://www.moneycontrol.com/rss/marketreports.xml"),
]

sent_headlines = set()

def fetch_latest_headline(feed_name, feed_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(feed_url, headers=headers, timeout=15)
        root = ET.fromstring(response.content)

        for item in root.iter("item"):
            title = item.find("title")
            if title is not None and title.text:
                headline = title.text.strip()
                if headline not in sent_headlines:
                    sent_headlines.add(headline)
                    # Keep set small
                    if len(sent_headlines) > 100:
                        sent_headlines.pop()
                    return f"📊 {feed_name} Update:\n{headline}"
    except Exception as e:
        print(f"Error fetching {feed_name}: {e}")
    return None

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    response = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})
    print(f"Telegram status: {response.status_code}")
    print(f"Sent: {text[:80]}...")

def job():
    print("Fetching market news...")
    # Rotate through feeds each hour
    index = int(time.time() / 3600) % len(RSS_FEEDS)
    feed_name, feed_url = RSS_FEEDS[index]
    headline = fetch_latest_headline(feed_name, feed_url)
    if headline:
        send_to_telegram(headline)
    else:
        print("No new headline found this round.")

# Run once immediately, then every hour
job()
schedule.every(1).hours.do(job)

print("Bot running! Fetching market news every hour...")
while True:
    schedule.run_pending()
    time.sleep(60)
