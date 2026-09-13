# News Pulse Bot - Vercel Edition (Single User)

This is a lightweight, serverless version of the News Pulse Telegram Bot designed specifically for deployment on **Vercel**. It uses **Vercel Cron** to send you news briefings from all 10 categories directly to your Telegram chat twice a day:
- 🌅 **Morning Briefing:** 9:00 AM IST (03:30 UTC)
- 🌆 **Evening Roundup:** 5:30 PM IST (12:00 UTC)

Powered by **Gemini 3.5 Flash Lite** with real-time Google Search grounding.

---

## 📁 Files Included

- `api/cron.py`: Vercel Serverless Function that fetches news across all 10 categories concurrently and sends them to Telegram.
- `vercel.json`: Cron schedule configuration.
- `requirements.txt`: Python dependencies (`google-genai`, `requests`, `pytz`).
- `.env.example`: Template for required environment variables.

---

## 🚀 How to Deploy on Vercel

### Step 1: Deploy to Vercel
1. Push this folder (`vercel_bot`) or repository to GitHub.
2. Go to [Vercel Dashboard](https://vercel.com/dashboard) and click **Add New... -> Project**.
3. Import your repository (set Root Directory to `vercel_bot` if in a monorepo).

### Step 2: Configure Environment Variables
In your Vercel Project Settings -> **Environment Variables**, add the following:

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Your Google Gemini API key |
| `TELEGRAM_BOT_TOKEN` | Token provided by `@BotFather` |
| `TELEGRAM_CHAT_ID` | Your personal Telegram Chat ID |

### Step 3: Verify Cron & Test
1. Click **Deploy**.
2. Vercel will automatically read `vercel.json` and set up the cron schedules under **Project Settings -> Cron Jobs**.
3. To manually trigger a test briefing at any time, open:
   `https://<your-vercel-domain>.vercel.app/api/cron`

---

## 🧪 Local Testing

You can test `api/cron.py` locally before deploying:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
export GEMINI_API_KEY="your_api_key"
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# 3. Run script
python api/cron.py
```
