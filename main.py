from fastapi import FastAPI
import feedparser

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
