import requests
import schedule
import time

GEMINI_API_KEY   = "AIzaSyBLAWxn_3pCAemojs3B-FW5_Vfbz55Y_eg"
TELEGRAM_TOKEN   = "8631241825:AAFDSQcy-xCiRissY5tq2eTOLx8StSirzd4"
TELEGRAM_CHAT_ID = "8396729316"

MARKETS = ["Nifty 50", "Bank Nifty", "XAUUSD Gold", "Sensex"]

def get_market_update():
    market = MARKETS[int(time.time() / 3600) % len(MARKETS)]

    prompt = (
        f"You are a financial news tweet writer for Indian markets. "
        f"Write a tweet update for {market} right now. "
        f"Include current price or % change, key reason, and relevant emoji. "
        f"Keep it UNDER 30 WORDS. End with 2-3 hashtags like #Nifty #Gold #Markets. "
        f"Only write the tweet, nothing else."
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    body = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    response = requests.post(url, json=body)
    data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print("Error getting update:", e)
        return None

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})
    print(f"Sent: {text[:80]}...")

def job():
    print("Fetching market update...")
    tweet = get_market_update()
    if tweet:
        send_to_telegram(tweet)

# Run once immediately, then every hour
job()
schedule.every(1).hours.do(job)

print("Bot is running! Sending market updates every hour...")
while True:
    schedule.run_pending()
    time.sleep(60)
