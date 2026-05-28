import requests
import schedule
import time
import os

TELEGRAM_TOKEN    = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID  = os.environ.get("TELEGRAM_CHAT_ID", "")
GROQ_API_KEY      = os.environ.get("GROQ_API_KEY", "")
NEWSDATA_API_KEY  = os.environ.get("NEWSDATA_API_KEY", "")

TOPICS = [
    ("📈 Nifty/Stock Market", "Nifty Sensex NSE"),
    ("🥇 Gold & XAUUSD",      "gold price MCX"),
    ("📊 Indian Markets",     "Bank Nifty stocks India"),
]

sent_headlines = set()

def fetch_news(query):
    try:
        url = "https://newsdata.io/api/1/latest"
        params = {
            "apikey": NEWSDATA_API_KEY,
            "q": query,
            "country": "in",
            "language": "en",
            "category": "business",
            "size": 5
        }
        response = requests.get(url, params=params, timeout=20)
        print(f"NewsData HTTP: {response.status_code}")
        if response.status_code != 200:
            return None, None
        data = response.json()
        if data.get("status") == "success":
            results = data.get("results", [])
            print(f"Found {len(results)} articles")
            for item in results:
                title = (item.get("title") or "").strip()
                desc  = (item.get("description") or item.get("content") or "").strip()[:500]
                if title and title not in sent_headlines:
                    sent_headlines.add(title)
                    if len(sent_headlines) > 100:
                        sent_headlines.clear()
                    return title, desc
    except Exception as e:
        print(f"NewsData exception: {e}")
    return None, None

def write_tweet_with_groq(headline, description):
    try:
        context = description if description and len(description) > 50 else headline
        print(f"Groq input: {context[:150]}")

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        body = {
            "model": "llama-3.3-70b-versatile",  # Latest Groq model
            "messages": [
                {
                    "role": "system",
                    "content": "You write punchy financial tweets under 30 words for Indian markets. Output ONLY the tweet. No intro. No explanation. Just the tweet with emojis and hashtags."
                },
                {
                    "role": "user",
                    "content": f"Write a tweet about this market news: {context}"
                }
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
    if response.status_code == 200:
        print("✅ Sent to Telegram!")
    else:
        print(f"❌ Telegram error: {response.text[:200]}")

def job():
    print("--- Fetching market update ---")
    index = int(time.time() / 3600) % len(TOPICS)
    order = [index, (index+1) % 3, (index+2) % 3]

    for i in order:
        topic_name, query = TOPICS[i]
        print(f"Trying: {topic_name}")
        headline, description = fetch_news(query)
        if headline:
            print(f"Headline: {headline[:80]}")
            tweet = write_tweet_with_groq(headline, description)
            if tweet:
                send_to_telegram(f"{topic_name}\n\n{tweet}")
            else:
                send_to_telegram(f"{topic_name}\n\n{headline}\n\n#Nifty #Markets #NSE")
            return
        time.sleep(2)

    print("No news found from any source this round.")

print(f"Token:    {'✅' if TELEGRAM_TOKEN else '❌ MISSING'}")
print(f"Chat ID:  {'✅' if TELEGRAM_CHAT_ID else '❌ MISSING'}")
print(f"Groq:     {'✅' if GROQ_API_KEY else '❌ MISSING'}")
print(f"NewsData: {'✅' if NEWSDATA_API_KEY else '❌ MISSING'}")

job()
schedule.every(1).hours.do(job)
print("Bot running! AI tweet updates every hour...")
while True:
    schedule.run_pending()
    time.sleep(60)
