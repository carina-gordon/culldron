# Insight Extractor

A service that analyzes RSS feeds to extract and cluster thesis statements from blog posts, identifying recurring themes and maintaining a timeline of related content.

## Features

- RSS feed ingestion (on-demand or scheduled)
- Automatic thesis extraction using NLP
- Theme clustering and deduplication
- Timeline view of related posts
- RESTful API endpoints

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and configure your settings
3. Run with Docker Compose:
```bash
docker compose up
```

## API Endpoints

- `POST /ingest` - Submit a new RSS feed URL for processing
- `GET /themes` - List all themes with post counts
- `GET /themes/{id}` - View timeline of posts for a specific theme

## Technical Stack

- Python 3.11
- FastAPI
- SQLite (via SQLModel)
- SentenceTransformers (all-MiniLM-L6-v2)
- Docker

## Design Decisions

- Using SentenceTransformers for efficient sentence embeddings
- Cosine similarity threshold of 0.8 for theme clustering
- SQLite for simplicity and portability
- APScheduler for feed polling

## Future Work

- Authentication and rate limiting
- Pagination for large result sets
- More sophisticated NLP techniques
- Support for additional feed formats
- Real-time notifications for new themes 