import requests
import schedule
import time
import json

GEMINI_API_KEY   = "AIzaSyBLAWxn_3pCAemojs3B-FW5_Vfbz55Y_eg"
TELEGRAM_TOKEN   = "8631241825:AAH27LMk13fvf5P7iL-FvUT6Txot0-T3pYw"
TELEGRAM_CHAT_ID = "8396729316"

MARKETS = ["Nifty 50", "Bank Nifty", "XAUUSD Gold", "Sensex"]

def get_market_update():
    market = MARKETS[int(time.time() / 3600) % len(MARKETS)]

    prompt = (
        f"Write a market update tweet for {market} right now. "
        f"Include price or % change, key reason, and emoji. "
        f"Keep it UNDER 30 WORDS. End with 2-3 hashtags. "
        f"Only write the tweet text, nothing else."
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    body = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 100,
            "temperature": 0.7
        }
    }

    try:
        response = requests.post(url, json=body, timeout=30)
        data = response.json()

        print("Gemini response:", json.dumps(data, indent=2)[:500])

        if "candidates" in data and len(data["candidates"]) > 0:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip()
        elif "error" in data:
            print("Gemini error:", data["error"]["message"])
            return None
        else:
            print("Unexpected response:", data)
            return None

    except Exception as e:
        print("Exception:", str(e))
        return None

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    response = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})
    print(f"Telegram response: {response.status_code}")
    print(f"Sent: {text[:80]}...")

def job():
    print("Fetching market update...")
    tweet = get_market_update()
    if tweet:
        send_to_telegram(tweet)
    else:
        print("No update to send this round.")

# Run once immediately, then every hour
job()
schedule.every(1).hours.do(job)

print("Bot is running! Sending market updates every hour...")
while True:
    schedule.run_pending()
    time.sleep(60)
