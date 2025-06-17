# Insight Extractor

A service that analyzes RSS feeds to extract and cluster thesis statements from blog posts, identifying recurring themes and maintaining a timeline of related content.

## Features

- RSS feed ingestion (on-demand or scheduled)
- Automatic thesis extraction using NLP
- Theme clustering and deduplication
- Timeline view of related posts
- RESTful API endpoints
- OpenAPI documentation
- Docker support

## Setup

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/insight-extractor.git
cd insight-extractor
```

2. Copy `.env.example` to `.env` and configure your settings:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run with Docker Compose:
```bash
docker compose up
```

The API will be available at http://localhost:8000

### Development Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and configure your settings:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize the database:
```bash
curl -X POST http://localhost:8000/init-db
```

5. Run the development server:
```bash
uvicorn app.main:app --reload
```

## API Documentation

- Interactive Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Specification: `openapi.yaml`

## API Endpoints

- `POST /ingest` - Submit a new RSS feed URL for processing
- `GET /themes` - List all themes with post counts
- `GET /themes/{id}` - View timeline of posts for a specific theme
- `GET /posts` - List all posts
- `GET /posts/{id}` - Get details for a specific post
- `GET /posts/search` - Search posts by title or content

## Testing

Run the test suite:
```bash
pytest
```

## Technical Stack

- Python 3.11
- FastAPI
- SQLite (via SQLModel)
- SentenceTransformers (all-MiniLM-L6-v2)
- Docker
- Pytest for testing

## Design Decisions

- Using SentenceTransformers for efficient sentence embeddings
- Cosine similarity threshold of 0.8 for theme clustering
- SQLite for simplicity and portability
- APScheduler for feed polling
- Multi-stage Docker build for smaller image size
- Environment-based configuration

## Future Work

- Authentication and rate limiting
- Pagination for large result sets
- More sophisticated NLP techniques
- Support for additional feed formats
- Real-time notifications for new themes
- WebSocket support for live updates
- Export functionality for themes and posts
- User preferences and saved searches

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 