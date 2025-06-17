from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List, Optional
import logging
import uvicorn
import time

from .models import Theme, Post, ThemeCreate, PostCreate
from .database import engine, create_db_and_tables
from .feed_processor import FeedProcessor
from .nlp_processor import NLPProcessor

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
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
nlp_processor = None
feed_processor = None

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    try:
        logger.info("=== Starting application initialization ===")
        
        logger.info("Step 1: Initializing NLP processor...")
        try:
            global nlp_processor, feed_processor
            nlp_processor = NLPProcessor()  # Model will be loaded on first use
            logger.info("NLP processor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize NLP processor: {str(e)}")
            raise
            
        logger.info("Step 2: Initializing feed processor...")
        try:
            feed_processor = FeedProcessor(nlp_processor)
            logger.info("Feed processor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize feed processor: {str(e)}")
            raise
            
        logger.info("=== Application initialization complete ===")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.post("/init-db")
async def init_db():
    """Initialize the database tables."""
    try:
        logger.info("Creating database tables...")
        create_db_and_tables()
        logger.info("Database tables created successfully")
        return {"message": "Database initialized successfully"}
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint that returns available endpoints."""
    return {
        "message": "Welcome to the RSS Feed Processor API",
        "endpoints": {
            "GET /": "This help message",
            "POST /init-db": "Initialize the database",
            "POST /ingest": "Ingest a new RSS feed",
            "GET /posts": "Get all posts",
            "GET /themes": "Get all themes",
            "GET /posts/{post_id}": "Get a specific post",
            "GET /themes/{theme_id}": "Get a specific theme",
            "GET /posts/theme/{theme_id}": "Get all posts for a theme",
            "GET /posts/search": "Search posts by title or content"
        }
    }

@app.post("/ingest")
def ingest_feed(feed_url: str) -> dict:
    """Ingest a feed URL and process its posts."""
    try:
        logger.info(f"Received request to ingest feed: {feed_url}")
        
        if not feed_processor:
            logger.error("Feed processor not initialized")
            raise HTTPException(status_code=500, detail="Feed processor not initialized")
            
        logger.info(f"Starting feed processing for: {feed_url}")
        start_time = time.time()
        result = feed_processor.process_feed(feed_url)
        total_time = time.time() - start_time
        logger.info(f"Feed processing completed in {total_time:.2f} seconds")
        
        return result
    except Exception as e:
        logger.error(f"Error processing feed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/posts")
def get_posts():
    try:
        with Session(engine) as session:
            posts = session.exec(select(Post)).all()
            return posts
    except Exception as e:
        logger.error(f"Error retrieving posts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/themes")
def get_themes():
    try:
        with Session(engine) as session:
            themes = session.exec(select(Theme)).all()
            return themes
    except Exception as e:
        logger.error(f"Error retrieving themes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        reload=True,
        workers=1
    ) 