import feedparser
import logging
from datetime import datetime
from typing import List, Tuple
from sqlmodel import Session, select

from .models import Post, Theme, PostCreate
from .database import engine
from .nlp_processor import NLPProcessor

logger = logging.getLogger(__name__)

class FeedProcessor:
    def __init__(self, nlp_processor: NLPProcessor):
        self.nlp_processor = nlp_processor

    async def process_feed(self, feed_url: str) -> List[Post]:
        """Process a feed URL and return the list of processed posts."""
        logger.info(f"Processing feed: {feed_url}")
        
        # Parse the feed
        feed = feedparser.parse(feed_url)
        if feed.bozo:
            logger.error(f"Error parsing feed {feed_url}: {feed.bozo_exception}")
            raise ValueError(f"Invalid feed format: {feed.bozo_exception}")

        processed_posts = []
        
        with Session(engine) as session:
            # Get existing themes for similarity comparison
            existing_themes = session.exec(
                select(Theme.id, Theme.thesis)
            ).all()

            for entry in feed.entries:
                try:
                    # Check if post already exists
                    existing_post = session.exec(
                        select(Post).where(Post.url == entry.link)
                    ).first()
                    
                    if existing_post:
                        logger.info(f"Post already exists: {entry.link}")
                        continue

                    # Extract content
                    content = entry.get('content', [{'value': ''}])[0]['value']
                    if not content:
                        content = entry.get('summary', '')

                    # Extract thesis
                    thesis_statements = self.nlp_processor.extract_thesis(content)
                    if not thesis_statements:
                        logger.warning(f"No thesis found for post: {entry.link}")
                        continue

                    thesis = ' '.join(thesis_statements)
                    
                    # Check for similar themes
                    is_similar, theme_id = self.nlp_processor.find_similar_theme(
                        thesis, existing_themes
                    )

                    # Create or get theme
                    if is_similar:
                        theme = session.get(Theme, theme_id)
                    else:
                        theme = Theme(thesis=thesis)
                        session.add(theme)
                        session.commit()
                        session.refresh(theme)
                        existing_themes.append((theme.id, theme.thesis))

                    # Create post
                    post = Post(
                        title=entry.title,
                        url=entry.link,
                        content=content,
                        published_at=datetime(*entry.published_parsed[:6]),
                        theme_id=theme.id
                    )
                    session.add(post)
                    session.commit()
                    processed_posts.append(post)
                    
                    logger.info(f"Processed post: {entry.link}")

                except Exception as e:
                    logger.error(f"Error processing entry {entry.link}: {str(e)}")
                    continue

        return processed_posts 