import os
import feedparser
import httpx
import asyncio
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Trend Service",
    version="1.0.0",
    description="AI Trend + Telegram Posting Service"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================
# TREND API (same as before)
# =========================
@app.get("/trends")
def get_trends():

    feeds = {
        "TechCrunch": "https://techcrunch.com/feed/",
        "The Verge": "https://www.theverge.com/rss/index.xml",
        "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
        "Hacker News": "https://hnrss.org/frontpage"
    }

    trends = []

    for source, url in feeds.items():
        feed = feedparser.parse(url)

        for entry in feed.entries[:5]:
            trends.append({
                "source": source,
                "title": entry.title,
                "link": entry.link,
                "published": entry.get("published", "Unknown")
            })

    return {
        "status": "success",
        "total": len(trends),
        "data": trends
    }


# =========================
# TELEGRAM CONFIG
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")


# =========================
# REQUEST MODEL
# =========================
class PostRequest(BaseModel):
    text: str
    platform: str = "telegram"


class PostResponse(BaseModel):
    success: bool
    message: str
    text: str


# =========================
# TELEGRAM VERIFY (simple test)
# =========================
@app.get("/verify-telegram")
async def verify_telegram():

    if not BOT_TOKEN:
        raise HTTPException(status_code=401, detail="BOT_TOKEN missing in .env")

    async with httpx.AsyncClient() as client:
        res = await client.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe")
        data = res.json()

        if not data.get("ok"):
            raise HTTPException(status_code=401, detail="Invalid Bot Token")

        return {
            "status": "success",
            "bot": data["result"]
        }


# =========================
# POST TO TELEGRAM (FASTAPI)
# =========================
@app.post("/publish", response_model=PostResponse)
async def publish_to_telegram(request: PostRequest, background_tasks: BackgroundTasks):

    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Post text cannot be empty")

    if len(request.text) > 4096:
        raise HTTPException(status_code=400, detail="Telegram message too long")

    background_tasks.add_task(send_to_telegram, request.text)

    return PostResponse(
        success=True,
        message="Post is being published to Telegram...",
        text=request.text
    )


# =========================
# ACTUAL TELEGRAM SENDER
# =========================
async def send_to_telegram(text: str):

    if not BOT_TOKEN or not CHANNEL_ID:
        logger.error("Missing BOT_TOKEN or CHANNEL_ID in .env")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, data={
                "chat_id": CHANNEL_ID,
                "text": text,
                "parse_mode": "HTML"
            })

            data = response.json()

            if not data.get("ok"):
                logger.error(f"Telegram Error: {data}")
                return

            logger.info(f"✅ Posted to Telegram: {data['result']['message_id']}")

        except Exception as e:
            logger.error(f"❌ Telegram posting failed: {str(e)}")