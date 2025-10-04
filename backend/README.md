# Zaik Backend

FastAPI backend for the Zaik text adventure game.

## Prerequisites

- [mise](https://mise.jdx.dev/) - Runtime version management
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer (installed automatically by mise)
- [Docker](https://www.docker.com/) - For containerized development and deployment

## Setup

### Option 1: Local Development with mise + uv

1. Install Python version and create virtual environment:
```bash
mise install
```

2. Install dependencies with uv:
```bash
uv pip install -e .
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Docker Development (Recommended)

From the project root directory:

1. Configure environment:
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration
```

2. Start all services:
```bash
docker compose up
```

The backend will be available with hot-reload enabled.

### Option 3: Docker Production Build

Build and run the production image:
```bash
docker build -f backend/Dockerfile -t zaik-backend:latest backend/
docker run -p 8000:8000 zaik-backend:latest
```

## API Access

Once running, the API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
- Health check: http://localhost:8000/api/health

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   └── main.py          # FastAPI application entry point
├── tests/               # Test files
├── pyproject.toml       # Python project configuration (uv)
├── .mise.toml          # mise configuration for Python version
├── Dockerfile          # Production Docker image
├── Dockerfile.dev      # Development Docker image with hot-reload
├── .env.example        # Environment variables template
└── README.md
```

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
ruff format

# Lint code
ruff check
```
