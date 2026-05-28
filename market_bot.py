import requests
import schedule
import time
import os
import re
import xml.etree.ElementTree as ET

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GROQ_API_KEY     = os.environ.get("GROQ_API_KEY", "")

# These RSS feeds work without any middleman service
FEEDS = [
    ("📈 Stock Market", "https://feeds.feedburner.com/ndtvprofit-latest"),
    ("🥇 Gold & Markets", "https://feeds.feedburner.com/ndtvprofit-latest"),
    ("📊 Business News", "https://www.business-standard.com/rss/markets-106.rss"),
]

sent_headlines = set()

def clean_html(text):
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = re.sub(r'&[a-z]+;', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:600]

def fetch_headline_direct(feed_url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0 Safari/537.36",
            "Accept": "application/rss+xml, application/xml, text/xml, */*"
        }
        response = requests.get(feed_url, headers=headers, timeout=15)
        print(f"RSS HTTP status: {response.status_code}, size: {len(response.content)} bytes")

        root = ET.fromstring(response.content)

        # Try both RSS and Atom formats
        items = list(root.iter("item")) or list(root.iter("entry"))
        print(f"Found {len(items)} news items")

        for item in items:
            # Get title
            title_el = item.find("title")
            title = title_el.text.strip() if title_el is not None and title_el.text else ""

            # Get description/summary
            desc_el = item.find("description") or item.find("summary")
            desc = clean_html(desc_el.text if desc_el is not None else "")

            if title and title not in sent_headlines:
                sent_headlines.add(title)
                if len(sent_headlines) > 100:
                    sent_headlines.clear()
                return title, desc

    except Exception as e:
        print(f"RSS fetch error: {e}")
    return None, None

def write_tweet_with_groq(headline, description):
    try:
        # Use description if it has meaningful content, else use headline
        context = description if len(description) > 50 else headline
        print(f"Sending to Groq: {context[:150]}")

        prompt = (
            f"You are a financial tweet writer for Indian stock markets.\n"
            f"Here is the news: {context}\n\n"
            f"Write ONE engaging tweet under 30 words. Rules:\n"
            f"- Include the key fact, number or insight\n"
            f"- Add 1-2 relevant emojis\n"
            f"- End with 2-3 hashtags like #Nifty #Gold #Markets #NSE\n"
            f"- Make it sound like a real trader posted it\n"
            f"Output ONLY the tweet. No intro, no explanation."
        )

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        body = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": "You write short financial tweets under 30 words. Output only the tweet text."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 120,
            "temperature": 0.8
        }

        response = requests.post(url, headers=headers, json=body, timeout=15)
        print(f"Groq HTTP: {response.status_code}")
        data = response.json()

        if "choices" in data:
            tweet = data["choices"][0]["message"]["content"].strip()
            print(f"✅ Groq tweet: {tweet}")
            return tweet
        else:
            print(f"Groq issue: {data}")
            return None

    except Exception as e:
        print(f"Groq exception: {e}")
        return None

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    response = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})
    print(f"Telegram: {response.status_code}")
    if response.status_code == 200:
        print("✅ Sent to Telegram!")
    else:
        print(f"❌ Error: {response.text[:200]}")

def job():
    print("--- Fetching market update ---")
    index = int(time.time() / 3600) % len(FEEDS)
    feed_name, feed_url = FEEDS[index]
    print(f"Feed: {feed_name} -> {feed_url}")

    headline, description = fetch_headline_direct(feed_url)

    if not headline:
        print("No headline found this round.")
        return

    print(f"Headline: {headline[:100]}")
    tweet = write_tweet_with_groq(headline, description)

    if tweet:
        send_to_telegram(f"{feed_name}\n\n{tweet}")
    else:
        send_to_telegram(f"{feed_name}\n\n{headline}\n\n#Nifty #Markets #NSE")

print(f"Token:   {'✅' if TELEGRAM_TOKEN else '❌ MISSING'}")
print(f"Chat ID: {'✅' if TELEGRAM_CHAT_ID else '❌ MISSING'}")
print(f"Groq:    {'✅' if GROQ_API_KEY else '❌ MISSING'}")

job()
schedule.every(1).hours.do(job)
print("Bot running! AI tweet updates every hour...")
while True:
    schedule.run_pending()
    time.sleep(60)
