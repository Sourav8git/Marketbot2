import requests
import schedule
import time
import os

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# All using RSS2JSON - free service, no SSL issues
FEEDS = [
    ("📈 Nifty/Stock Market", "https://www.livemint.com/rss/markets"),
    ("🥇 Gold & Commodities",  "https://www.livemint.com/rss/money"),
    ("📊 Business News",       "https://www.livemint.com/rss/industry"),
]

sent_headlines = set()

def fetch_news(feed_name, feed_url):
    try:
        api_url = f"https://api.rss2json.com/v1/api.json?rss_url={feed_url}"
        response = requests.get(api_url, timeout=15)
        data = response.json()
        print(f"RSS2JSON status: {data.get('status')}")
        if data.get("status") == "ok":
            items = data.get("items", [])
            for item in items:
                title = item.get("title", "").strip()
                if title and title not in sent_headlines:
                    sent_headlines.add(title)
                    if len(sent_headlines) > 100:
                        sent_headlines.clear()
                    return f"{feed_name}:\n\n{title}\n\n#Nifty #Markets #NSE #BSE"
        else:
            print(f"Bad response: {data}")
    except Exception as e:
        print(f"Error: {e}")
    return None

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    response = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})
    print(f"Telegram status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Message sent to Telegram!")
    else:
        print(f"❌ Error: {response.text[:200]}")

def job():
    print("--- Fetching market update ---")
    index = int(time.time() / 3600) % len(FEEDS)
    feed_name, feed_url = FEEDS[index]
    print(f"Feed: {feed_name}")
    result = fetch_news(feed_name, feed_url)
    if result:
        send_to_telegram(result)
    else:
        print("No new update this round.")

print(f"Token set: {'Yes' if TELEGRAM_TOKEN else 'NO - MISSING!'}")
print(f"Chat ID set: {'Yes' if TELEGRAM_CHAT_ID else 'NO - MISSING!'}")

job()
schedule.every(1).hours.do(job)
print("Bot running! Updates every hour...")
while True:
    schedule.run_pending()
    time.sleep(60)
