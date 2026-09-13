import os
import json
import logging
import datetime
import pytz
import requests
import concurrent.futures
from http.server import BaseHTTPRequestHandler
from google import genai

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CATEGORIES = {
    1: "Top Stories (Trending / Breaking)",
    2: "World News",
    3: "India (National News)",
    4: "Indian Politics",
    5: "Sports (Cricket and IPL should be on top)",
    6: "Business & Economy",
    7: "Technology",
    8: "Health",
    9: "Science",
    10: "Entertainment & Pop Culture"
}

def fetch_category_news(client, category_id, time_context, current_date_str):
    category_name = CATEGORIES[category_id]
    prompt = f"""
    Today's exact date is {current_date_str}. 
    You MUST use the Google Search tool to fetch the most recent and factual news for this specific date.
    Provide a {time_context}. I need the top 3 headlines and their details in brief for the following category: {category_name}.

    **QUALITY CONTROL AND SOURCE RANKING:**
    Prioritize high-quality, verified sources like Reuters, BBC, The Hindu, Indian Express, and Bloomberg. Avoid random blogs or unverified tabloids.

    Format strictly for Telegram. Use plain text, spacing, and emojis.
    CRITICAL INSTRUCTION FOR LINKS: Do NOT use Markdown link formatting like [URL](URL). You must just output the raw, plain text URL directly after "URL: ".
    Include the source name. 3 sentences max per headline.
    """
    try:
        interaction = client.interactions.create(
            model="gemini-3.5-flash-lite",
            input=prompt,
            tools=[{"type": "google_search"}]
        )
        raw_text = getattr(interaction, "output_text", str(interaction)) or ""
        clean_text = raw_text.replace("**", "").replace("*", "")
        return category_id, f"📌 {category_name.upper()}\n{clean_text}"
    except Exception as e:
        logger.error(f"Error fetching category {category_id} ({category_name}): {e}")
        return category_id, f"📌 {category_name.upper()}\nCould not fetch news at this time."

def send_telegram_message(bot_token, chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True
    }
    response = requests.post(url, json=payload, timeout=10)
    return response.status_code == 200

def run_briefing():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("ADMIN_CHAT_ID")
    api_key = os.getenv("GEMINI_API_KEY")

    if not bot_token or not chat_id:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variables.")

    client = genai.Client(api_key=api_key) if api_key else genai.Client()

    ist_now = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
    current_hour = ist_now.hour
    current_date_str = ist_now.strftime("%A, %B %d, %Y")
    time_context = "morning briefing and overnight developments" if current_hour < 12 else "evening roundup of today's events"

    logger.info(f"Starting news fetch for date: {current_date_str} ({time_context})")

    # Fetch categories concurrently using ThreadPoolExecutor for fast execution
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_cat = {
            executor.submit(fetch_category_news, client, cat_id, time_context, current_date_str): cat_id
            for cat_id in CATEGORIES.keys()
        }
        for future in concurrent.futures.as_completed(future_to_cat):
            cat_id, text = future.result()
            results[cat_id] = text

    parts = [results[cat_id] for cat_id in sorted(CATEGORIES.keys()) if cat_id in results]
    if not parts:
        logger.error("No category results fetched.")
        return False

    header = f"⚡ NEWS PULSE ({'MORNING' if current_hour < 12 else 'EVENING'} BRIEFING)\n🗓️ {current_date_str}\n"
    parts.insert(0, header)

    MAX_LENGTH = 4000
    current_chunk = ""
    separator = "\n\n" + ("=" * 20) + "\n\n"

    for part in parts:
        if not current_chunk:
            current_chunk = part
        elif len(current_chunk) + len(separator) + len(part) > MAX_LENGTH:
            send_telegram_message(bot_token, chat_id, current_chunk)
            current_chunk = part
        else:
            current_chunk += separator + part

    if current_chunk:
        send_telegram_message(bot_token, chat_id, current_chunk)

    logger.info("Briefing completed and delivered to Telegram successfully!")
    return True

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Verify optional Cron Secret header if set
        cron_secret = os.getenv("CRON_SECRET")
        if cron_secret:
            auth_header = self.headers.get("Authorization")
            if auth_header != f"Bearer {cron_secret}":
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode('utf-8'))
                return

        try:
            success = run_briefing()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            msg = "Briefing sent successfully" if success else "Briefing empty or failed"
            self.wfile.write(json.dumps({"status": "ok", "message": msg}).encode('utf-8'))
        except Exception as e:
            logger.error(f"Handler error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def do_POST(self):
        self.do_GET()

if __name__ == "__main__":
    # Local CLI test execution
    print("Testing briefing locally...")
    run_briefing()
