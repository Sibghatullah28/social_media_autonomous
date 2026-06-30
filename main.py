
import io

from fastapi import FastAPI, HTTPException
import feedparser
from fastapi.responses import Response
from pydantic import BaseModel
from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv

app = FastAPI(
    title="Trend Service",
    version="1.0.0",
    description="AI Trend Collection Service"
)

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

class PostRequest(BaseModel):
    text: str                   
    platform: str = "x"          

class PostResponse(BaseModel):
    success: bool
    message: str
    posted_url: str = None
    text: str


@app.get("/verify-x")
async def verify_x_credentials():
    """Pehle credentials check karne ke liye"""
    try:
        client = tweepy.Client(
            bearer_token=os.getenv("X_BEARER_TOKEN"),
            consumer_key=os.getenv("X_CONSUMER_KEY"),
            consumer_secret=os.getenv("X_CONSUMER_SECRET"),
            access_token=os.getenv("X_ACCESS_TOKEN"),
            access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET"),
        )
        
        me = client.get_me()
        return {
            "status": "success",
            "message": "✅ X Credentials Verified!",
            "username": me.data.username
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Verification Failed: {str(e)}")



@app.post("/publish", response_model=PostResponse)
async def publish_to_x(request: PostRequest, background_tasks: BackgroundTasks):
    """Text ko direct X pe post karega"""
    
    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Post text cannot be empty")
    
    if len(request.text) > 280:
        raise HTTPException(status_code=400, detail="Post text is too long (max 280 characters)")

    # Background mein post karo taake response jaldi mile
    background_tasks.add_task(publish_text_to_x, request.text)
    
    return PostResponse(
        success=True,
        message="Post is being published to X...",
        text=request.text
    )


# ================== BACKGROUND FUNCTION ==================
async def publish_text_to_x(text: str):
    """Actual X pe post karne wala function"""
    try:
        client = tweepy.Client(
            bearer_token=os.getenv("X_BEARER_TOKEN"),
            consumer_key=os.getenv("X_CONSUMER_KEY"),
            consumer_secret=os.getenv("X_CONSUMER_SECRET"),
            access_token=os.getenv("X_ACCESS_TOKEN"),
            access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET"),
        )
        
        response = client.create_tweet(text=text.strip())
        
        post_id = response.data['id']
        posted_url = f"https://x.com/i/web/status/{post_id}"
        
        print(f"✅ Posted successfully: {posted_url}")
        return {"success": True, "posted_url": posted_url}
        
    except Exception as e:
        print(f"❌ Posting failed: {e}")
        return {"success": False, "error": str(e)}

