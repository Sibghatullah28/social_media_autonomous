
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

load_dotenv()
HF_Token = os.getenv("HF_TOKEN")

if not HF_Token:
    print("⚠️ WARNING: 'HF_TOKEN' environment variable mein nahi mila! Apni .env file check karein.")

client = InferenceClient(
    provider="fal-ai",
    api_key=HF_Token,
)
class ImageRequest(BaseModel):
    prompt: str

@app.post("/generate-image")
async def generate_image(request: ImageRequest):
    try:
        # Hugging Face se FLUX.1-dev model ke zariye image generate karwana
        image = client.text_to_image(
            request.prompt,
            model="black-forest-labs/FLUX.1-dev",
        )
        
        # Image ko Bytes mein convert karna taake n8n isay as a file receive kar sake
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        # Direct raw image binary wapis bhejna
        return Response(content=img_byte_arr, media_type="image/png")
          

    except Exception as e:
        # Saaf error message bhejne ke liye
        error_msg = getattr(e, 'response', None) or str(e)
        if hasattr(error_msg, 'text'):  # Agar response object ho to uska text uthein
            error_msg = error_msg.text
        raise HTTPException(status_code=500, detail=f"Hugging Face Error: {error_msg}")

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

