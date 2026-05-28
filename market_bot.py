import requests
import schedule
import time
import os

TELEGRAM_TOKEN    = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID  = os.environ.get("TELEGRAM_CHAT_ID", "")
GROQ_API_KEY      = os.environ.get("GROQ_API_KEY", "")
NEWSDATA_API_KEY  = os.environ.get("NEWSDATA_API_KEY", "")

TOPICS = [
    ("📈 Nifty/Stock Market", "Nifty OR Sensex OR NSE"),
    ("🥇 Gold & XAUUSD",      "gold price OR XAUUSD OR MCX gold"),
    ("📊 Indian Markets",     "Bank Nifty OR Indian stock market"),
]

sent_headlines = set()

def fetch_news(query):
    try:
        url = "https://newsdata.io/api/1/news"
        params = {
            "apikey": NEWSDATA_API_KEY,
            "q": query,
            "country": "in",
            "language": "en",
            "category": "business"
        }
        response = requests.get(url, params=params, timeout=15)
        print(f"NewsData HTTP: {response.status_code}")
        data = response.json()

        if data.get("status") == "success":
            results = data.get("results", [])
            print(f"Found {len(results)} articles")
            for item in results:
                title = item.get("title", "").strip()
                desc  = item.get("description", "") or ""
                desc  = desc.strip()[:500]
                if title and title not in sent_headlines:
                    sent_headlines.add(title)
                    if len(sent_headlines) > 100:
                        sent_headlines.clear()
                    return title, desc
        else:
            print(f"NewsData error: {data}")
    except Exception as e:
        print(f"NewsData exception: {e}")
    return None, None

def write_tweet_with_groq(headline, description):
    try:
        context = description if len(description) > 50 else headline
        print(f"Groq input: {context[:150]}")

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        body = {
            "model": "llama3-8b-8192",
            "messages": [
                {
                    "role": "system",
                    "content": "You write punchy financial tweets under 30 words for Indian markets. Output ONLY the tweet text with emojis and hashtags. Nothing else."
                },
                {
                    "role": "user",
                    "content": f"Write a tweet about this news: {context}"
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
            print(f"✅ Tweet: {tweet}")
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
    index = int(time.time() / 3600) % len(TOPICS)
    topic_name, query = TOPICS[index]
    print(f"Topic: {topic_name} | Query: {query}")

    headline, description = fetch_news(query)

    if not headline:
        print("No news found this round.")
        return

    print(f"Headline: {headline[:100]}")
    tweet = write_tweet_with_groq(headline, description)

    if tweet:
        send_to_telegram(f"{topic_name}\n\n{tweet}")
    else:
        send_to_telegram(f"{topic_name}\n\n{headline}\n\n#Nifty #Markets #NSE")

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
