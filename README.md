# Zaik

A modern text-based adventure game inspired by Zork, powered by Large Language Models.

## Overview

Zaik combines classic text adventure gameplay with AI-powered natural language understanding to create dynamic, immersive interactive fiction experiences.

## Architecture

- **Frontend:** React-based terminal interface
- **Backend:** Python with FastAPI
- **Database:** Document database (MongoDB/CouchDB)
- **LLM Integration:** Custom server for AI-powered interactions

## Project Structure

```
zaik/
├── backend/          # Python FastAPI server
├── frontend/         # React application
├── docs/            # Project documentation
└── CLAUDE.md        # Development instructions
```

## Prerequisites

- [Docker](https://www.docker.com/) - For running services and building deployments
- [mise](https://mise.jdx.dev/) - For local development (optional)
- [uv](https://docs.astral.sh/uv/) - Fast Python package management (optional, for local development)

## Quick Start

### Using Docker (Recommended)

Start the entire game stack (frontend + backend) with one command:

```bash
# Start all services in development mode
docker compose up

# Or run in detached mode
docker compose up -d
```

Access the services:
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

Stop services:
```bash
docker compose down
```

### Production Build

For production deployment:

```bash
# Build and run production containers
docker compose -f docker-compose.prod.yml up -d
```

Production URLs:
- **Frontend:** http://localhost:80
- **Backend API:** http://localhost:8000

### Local Development

For local development without Docker:

**Backend:**
```bash
cd backend
mise install
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

See [backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md) for detailed setup instructions.

## Getting Started

See [CLAUDE.md](CLAUDE.md) for detailed development instructions and workflow.

## Development Status

This project is in early development. Check the [Notion board](https://www.notion.so/Zaik-282c637cdfdb8029b1ccd2373c1878d7) for current progress and roadmap.
