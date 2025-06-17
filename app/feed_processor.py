import feedparser
import logging
import time
from datetime import datetime
from typing import List, Tuple, Dict
from sqlmodel import Session, select
from fastapi import BackgroundTasks
import asyncio

from .models import Post, Theme, PostCreate
from .database import engine
from .nlp_processor import NLPProcessor

logger = logging.getLogger(__name__)

class FeedProcessor:
    def __init__(self, nlp_processor: NLPProcessor):
        self.nlp_processor = nlp_processor
        logger.info("FeedProcessor initialized")

    def _extract_content(self, entry) -> str:
        """Extract content from an RSS entry, handling different feed formats."""
        logger.debug(f"Extracting content from entry: {entry.title if hasattr(entry, 'title') else 'No title'}")
        
        # Try different content fields
        content = None
        
        # Try content field (Atom format)
        if hasattr(entry, 'content'):
            content = entry.content[0].value if entry.content else None
            logger.debug(f"Found content in 'content' field: {content[:100] if content else 'None'}")
            
        # Try description field (RSS format)
        if not content and hasattr(entry, 'description'):
            content = entry.description
            logger.debug(f"Found content in 'description' field: {content[:100] if content else 'None'}")
            
        # Try summary field (common in both formats)
        if not content and hasattr(entry, 'summary'):
            content = entry.summary
            logger.debug(f"Found content in 'summary' field: {content[:100] if content else 'None'}")
            
        # Try title as fallback
        if not content and hasattr(entry, 'title'):
            content = entry.title
            logger.debug(f"Using title as content: {content[:100] if content else 'None'}")
            
        if not content:
            logger.warning(f"No content found for entry: {entry.link if hasattr(entry, 'link') else 'No link'}")
            
        return content or ""

    def _get_published_date(self, entry) -> datetime:
        """Extract published date from an RSS entry, handling different formats."""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6])
            else:
                return datetime.now()
        except Exception as e:
            logger.warning(f"Error parsing date for entry {entry.link}: {str(e)}")
            return datetime.now()

    def process_feed(self, feed_url: str) -> Dict:
        """Process a feed URL and return the results."""
        logger.info(f"Starting feed processing: {feed_url}")
        
        try:
            # Parse the feed
            feed_start = time.time()
            logger.info(f"Attempting to parse feed: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            # Log feed details
            logger.info(f"Feed status: {feed.status if hasattr(feed, 'status') else 'No status'}")
            logger.info(f"Feed version: {feed.version if hasattr(feed, 'version') else 'No version'}")
            logger.info(f"Feed headers: {feed.headers if hasattr(feed, 'headers') else 'No headers'}")
            logger.info(f"Feed bozo: {feed.bozo}")
            if feed.bozo:
                logger.error(f"Feed parsing error: {feed.bozo_exception}")
            
            if feed.bozo:
                logger.error(f"Error parsing feed {feed_url}: {feed.bozo_exception}")
                return {"message": "Error parsing feed", "error": str(feed.bozo_exception)}
                
            feed_time = time.time() - feed_start
            logger.info(f"Feed parsed in {feed_time:.2f} seconds. Found {len(feed.entries)} entries.")
            
            if not feed.entries:
                logger.warning(f"No entries found in feed: {feed_url}")
                return {"message": "No entries found in feed"}

            processed_posts = []
            skipped_posts = 0
            
            with Session(engine) as session:
                # Get existing themes for similarity comparison
                themes_start = time.time()
                existing_themes = session.exec(
                    select(Theme.id, Theme.thesis)
                ).all()
                themes_time = time.time() - themes_start
                logger.info(f"Retrieved {len(existing_themes)} existing themes in {themes_time:.2f} seconds")

                # Get existing post URLs to avoid processing duplicates
                urls_start = time.time()
                existing_urls = set(session.exec(
                    select(Post.url)
                ).all())
                urls_time = time.time() - urls_start
                logger.info(f"Retrieved existing URLs in {urls_time:.2f} seconds")

                for i, entry in enumerate(feed.entries):
                    try:
                        logger.info(f"Processing entry {i+1}/{len(feed.entries)}: {entry.title if hasattr(entry, 'title') else 'No title'}")
                        logger.debug(f"Entry details: {entry}")
                        
                        # Skip if post already exists
                        if entry.link in existing_urls:
                            logger.info(f"Updating existing post: {entry.link}")
                            # Get the existing post
                            existing_post = session.exec(
                                select(Post).where(Post.url == entry.link)
                            ).first()
                            
                            # Update content and metadata
                            content = self._extract_content(entry)
                            if content:
                                existing_post.content = content
                                
                            if hasattr(entry, 'title'):
                                existing_post.title = entry.title
                                
                            existing_post.published_at = self._get_published_date(entry)
                            
                            # Extract and update thesis if content changed
                            if content:
                                thesis_statements = self.nlp_processor.extract_thesis(content)
                                if thesis_statements:
                                    thesis = ' '.join(thesis_statements)
                                    # Check for similar themes
                                    is_similar, theme_id = self.nlp_processor.find_similar_theme(
                                        thesis, existing_themes
                                    )
                                    if is_similar:
                                        existing_post.theme_id = theme_id
                                    else:
                                        theme = Theme(thesis=thesis)
                                        session.add(theme)
                                        session.commit()
                                        session.refresh(theme)
                                        existing_post.theme_id = theme.id
                                        existing_themes.append((theme.id, theme.thesis))
                            
                            session.add(existing_post)
                            session.commit()
                            processed_posts.append(existing_post)
                            continue

                        # Extract content using the new method
                        content = self._extract_content(entry)
                        if not content:
                            logger.warning(f"No content found for post: {entry.link}")
                            continue

                        # Extract thesis
                        thesis_start = time.time()
                        logger.info(f"Extracting thesis for: {entry.title if hasattr(entry, 'title') else 'No title'}")
                        thesis_statements = self.nlp_processor.extract_thesis(content)
                        thesis_time = time.time() - thesis_start
                        
                        if not thesis_statements:
                            logger.warning(f"No thesis found for post: {entry.link}")
                            continue

                        thesis = ' '.join(thesis_statements)
                        logger.info(f"Found thesis: {thesis[:100]}...")
                        
                        # Check for similar themes
                        theme_start = time.time()
                        is_similar, theme_id = self.nlp_processor.find_similar_theme(
                            thesis, existing_themes
                        )
                        theme_time = time.time() - theme_start

                        # Create or get theme
                        if is_similar:
                            theme = session.get(Theme, theme_id)
                            logger.info(f"Using existing theme {theme_id}")
                        else:
                            theme = Theme(thesis=thesis)
                            session.add(theme)
                            session.commit()
                            session.refresh(theme)
                            existing_themes.append((theme.id, theme.thesis))
                            logger.info(f"Created new theme {theme.id}")

                        # Create post with the new date extraction method
                        post = Post(
                            title=entry.title if hasattr(entry, 'title') else 'No title',
                            url=entry.link,
                            content=content,
                            published_at=self._get_published_date(entry),
                            theme_id=theme.id
                        )
                        session.add(post)
                        session.commit()
                        processed_posts.append(post)
                        
                        logger.info(f"Processed post: {entry.link} (thesis: {thesis_time:.2f}s, theme: {theme_time:.2f}s)")

                    except Exception as e:
                        logger.error(f"Error processing entry {entry.link if hasattr(entry, 'link') else 'No link'}: {str(e)}")
                        continue

            total_time = time.time() - feed_start
            logger.info(f"Feed processing completed in {total_time:.2f} seconds")
            logger.info(f"Processed {len(processed_posts)} posts, skipped {skipped_posts} posts")
            
            return {
                "message": f"Successfully processed {len(processed_posts)} posts",
                "processed": len(processed_posts),
                "skipped": skipped_posts,
                "total_time": total_time
            }

        except Exception as e:
            logger.error(f"Error in feed processing: {str(e)}")
            return {"message": "Error processing feed", "error": str(e)} 