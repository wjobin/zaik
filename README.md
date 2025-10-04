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

```bash
# Start all services
docker compose up
```

The backend API will be available at http://localhost:8000

### Local Development

See [backend/README.md](backend/README.md) for detailed setup instructions using mise + uv.

## Getting Started

See [CLAUDE.md](CLAUDE.md) for detailed development instructions and workflow.

## Development Status

This project is in early development. Check the [Notion board](https://www.notion.so/Zaik-282c637cdfdb8029b1ccd2373c1878d7) for current progress and roadmap.
