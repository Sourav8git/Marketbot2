import requests
import schedule
import time
import os
import re

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GROQ_API_KEY     = os.environ.get("GROQ_API_KEY", "")

FEEDS = [
    ("📈 Nifty/Stock Market", "https://www.livemint.com/rss/markets"),
    ("🥇 Gold & Commodities",  "https://www.livemint.com/rss/money"),
    ("📊 Business News",       "https://www.livemint.com/rss/industry"),
]

sent_headlines = set()

def clean_html(text):
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:500]

def fetch_headline(feed_url):
    try:
        api_url = f"https://api.rss2json.com/v1/api.json?rss_url={feed_url}"
        response = requests.get(api_url, timeout=15)
        data = response.json()
        if data.get("status") == "ok":
            for item in data.get("items", []):
                title = item.get("title", "").strip()
                desc  = clean_html(item.get("description", ""))
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
        context = description if description and len(description) > 20 else headline
        prompt = (
            f"You are a financial tweet writer for Indian markets.\n"
            f"News: {context}\n\n"
            f"Write ONE tweet under 30 words. Include:\n"
            f"- The key fact or insight from the news\n"
            f"- 1-2 relevant emojis\n"
            f"- 2-3 hashtags at the end like #Nifty #Gold #Markets\n"
            f"Only write the tweet text. Nothing else. No explanations."
        )

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        body = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": "You are a financial tweet writer. Only output the tweet text, nothing else."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 120,
            "temperature": 0.7
        }

        response = requests.post(url, headers=headers, json=body, timeout=15)
        print(f"Groq HTTP status: {response.status_code}")
        data = response.json()
        print(f"Groq raw response: {str(data)[:300]}")

        if "choices" in data and len(data["choices"]) > 0:
            tweet = data["choices"][0]["message"]["content"].strip()
            print(f"✅ Groq tweet: {tweet}")
            return tweet
        else:
            print(f"❌ Groq unexpected response: {data}")
            return None

    except Exception as e:
        print(f"Groq exception: {e}")
        return None

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    response = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})
    print(f"Telegram status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Message sent to Telegram!")
    else:
        print(f"❌ Telegram error: {response.text[:200]}")

def job():
    print("--- Fetching market update ---")
    index = int(time.time() / 3600) % len(FEEDS)
    feed_name, feed_url = FEEDS[index]
    print(f"Feed: {feed_name}")

    headline, description = fetch_headline(feed_url)
    if not headline:
        print("No new headline found.")
        return

    print(f"Headline: {headline[:100]}")
    print(f"Description length: {len(description)} chars")

    tweet = write_tweet_with_groq(headline, description)

    if tweet:
        final_message = f"{feed_name}\n\n{tweet}"
    else:
        # Fallback if Groq fails
        final_message = f"{feed_name}\n\n{headline}\n\n#Nifty #Markets #NSE"

    send_to_telegram(final_message)

print(f"Token set:   {'Yes' if TELEGRAM_TOKEN else 'NO - MISSING!'}")
print(f"Chat ID set: {'Yes' if TELEGRAM_CHAT_ID else 'NO - MISSING!'}")
print(f"Groq set:    {'Yes' if GROQ_API_KEY else 'NO - MISSING!'}")

job()
schedule.every(1).hours.do(job)
print("Bot running! AI-powered tweet updates every hour...")
while True:
    schedule.run_pending()
    time.sleep(60)
