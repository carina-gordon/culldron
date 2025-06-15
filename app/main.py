from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List
import logging

from .models import Theme, Post, ThemeCreate, PostCreate
from .database import engine, create_db_and_tables
from .feed_processor import FeedProcessor
from .nlp_processor import NLPProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Insight Extractor",
    description="Extract and cluster thesis statements from RSS feeds",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
nlp_processor = NLPProcessor()
feed_processor = FeedProcessor(nlp_processor)

@app.on_event("startup")
async def on_startup():
    create_db_and_tables()

@app.post("/ingest")
async def ingest_feed(feed_url: str):
    """Ingest a new RSS feed and process its posts."""
    try:
        posts = await feed_processor.process_feed(feed_url)
        return {"message": f"Successfully processed {len(posts)} posts"}
    except Exception as e:
        logger.error(f"Error processing feed {feed_url}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/themes")
async def list_themes():
    """List all themes with their post counts."""
    with Session(engine) as session:
        themes = session.exec(select(Theme)).all()
        return [
            {
                "id": theme.id,
                "thesis": theme.thesis,
                "post_count": len(theme.posts),
                "created_at": theme.created_at
            }
            for theme in themes
        ]

@app.get("/themes/{theme_id}")
async def get_theme_timeline(theme_id: int):
    """Get a timeline of posts for a specific theme."""
    with Session(engine) as session:
        theme = session.get(Theme, theme_id)
        if not theme:
            raise HTTPException(status_code=404, detail="Theme not found")
        
        posts = sorted(theme.posts, key=lambda x: x.published_at)
        return {
            "theme_id": theme.id,
            "thesis": theme.thesis,
            "posts": [
                {
                    "title": post.title,
                    "url": post.url,
                    "published_at": post.published_at,
                    "ingested_at": post.ingested_at
                }
                for post in posts
            ]
        } 