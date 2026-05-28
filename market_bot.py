import requests
import schedule
import time
import xml.etree.ElementTree as ET
import os

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

RSS_FEEDS = [
    ("Nifty/Sensex", "https://economictimes.indiatimes.com/markets/stocks/rss.cms"),
    ("Gold/Commodities", "https://economictimes.indiatimes.com/markets/commodities/rss.cms"),
    ("Market News", "https://economictimes.indiatimes.com/markets/rss.cms"),
]

sent_headlines = set()

def fetch_latest_headline(feed_name, feed_url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(feed_url, headers=headers, timeout=15)
        response.encoding = "utf-8"
        root = ET.fromstring(response.content)
        for item in root.iter("item"):
            title = item.find("title")
            if title is not None and title.text:
                headline = title.text.strip()
                if headline not in sent_headlines:
                    sent_headlines.add(headline)
                    if len(sent_headlines) > 100:
                        sent_headlines.clear()
                    return f"📊 {feed_name} News:\n\n{headline}\n\n#Nifty #Markets #NSE"
    except Exception as e:
        print(f"Error fetching {feed_name}: {e}")
    return None

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    response = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})
    print(f"Telegram status: {response.status_code} - {response.text[:150]}")

def job():
    print("Fetching market news...")
    index = int(time.time() / 3600) % len(RSS_FEEDS)
    feed_name, feed_url = RSS_FEEDS[index]
    print(f"Using feed: {feed_name} -> {feed_url}")
    headline = fetch_latest_headline(feed_name, feed_url)
    if headline:
        print(f"Sending: {headline[:80]}")
        send_to_telegram(headline)
    else:
        print("No new headline found.")

print(f"Token set: {'Yes' if TELEGRAM_TOKEN else 'NO - MISSING!'}")
print(f"Chat ID set: {'Yes' if TELEGRAM_CHAT_ID else 'NO - MISSING!'}")

job()
schedule.every(1).hours.do(job)

print("Bot running! Fetching market news every hour...")
while True:
    schedule.run_pending()
    time.sleep(60)
