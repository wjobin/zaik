# Zaik Project - Development Instructions

## Project Overview

**Zaik** is a modern text-based adventure game inspired by Zork, leveraging Large Language Models (LLMs) to create dynamic, natural language interactions. The name "Zaik" combines "Zork" with "AI" to reflect its AI-powered gameplay.

**Notion Resources:**
- **Project Page:** https://www.notion.so/Zaik-282c637cdfdb8029b1ccd2373c1878d7
  - Page ID: `282c637cdfdb8029b1ccd2373c1878d7`
- **Feature Backlog Database:** https://www.notion.so/282c637cdfdb8176a122c63fb188f4b3
  - Database ID: `282c637cdfdb8176a122c63fb188f4b3`

## Architecture

- **Frontend:** React
- **Backend:** Python with FastAPI
- **Database:** Document database (MongoDB/CouchDB - TBD)
- **LLM Integration:** Custom server handling API access and token management
- **Core Concept:** Pre-generated location graph with LLM-enhanced descriptions and natural language parsing

## Working with the Notion Backlog

### Backlog Structure

The project uses a Notion Kanban board with the following columns:
- **Backlog** - Not yet ready to start
- **To Do** - Ready for development
- **In Progress** - Currently being worked on
- **Done** - Completed

### Task Categories
- **Core Mechanics** (Purple) - Game engine, state management, inventory
- **LLM Integration** (Pink) - AI features, parsing, dynamic content
- **UI/UX** (Orange) - Frontend interface and user experience
- **Content** (Green) - Game content, locations, items, puzzles

### Task Priority Levels
- **High** (Red) - Critical path items, blocking dependencies
- **Medium** (Yellow) - Important but not blocking
- **Low** (Blue) - Nice-to-have, polish, optimizations

### Workflow Instructions

When starting a new task:

1. **Check the Notion board** for the next highest-priority task in "To Do"
   - Query the Feature Backlog Database directly using database ID `282c637cdfdb8176a122c63fb188f4b3`
   - Use `mcp__mcp-toolkit-gateway__API-post-database-query` with filters for Status and Priority
2. **Move the task to "In Progress"** when you begin work
   - Use `mcp__mcp-toolkit-gateway__API-patch-page` to update the task status
   - **REQUIRED:** You MUST use Notion MCP tools to update task status. If the tools fail or are unavailable, stop and report the error.
3. **Read the full task description** if available by clicking into the task
   - Use `mcp__mcp-toolkit-gateway__API-retrieve-a-page` to get full task details
4. **Complete the work** following the development principles below
5. **Commit and push your changes** when the work is complete
   - Create a descriptive commit message following the git commit format
   - Push to GitHub using `git push`
6. **Move the task to "Done"** when finished and tested
   - Use `mcp__mcp-toolkit-gateway__API-patch-page` to update status to "Done"
   - **REQUIRED:** You MUST update the Notion task status or fail. Do not proceed without confirming the update succeeded.
7. **Update any related tasks** that may be unblocked

### Development Principles

1. **Iterate in small, testable increments** - Make frequent commits with working code
2. **Keep game logic separate from UI and LLM concerns** - Maintain clean architecture
3. **Use type hints and clear interfaces between components** - Ensure maintainability
4. **Document LLM prompts and expected response formats** - Critical for consistency
5. **ALWAYS write tests for services** - Every service must have corresponding tests in `backend/tests/`
   - Test files should be named `test_<service_name>.py`
   - Include unit tests, edge cases, and integration tests
   - Run tests before committing: `mise exec -- pytest tests/ -v`
6. **ALWAYS use mise and uv for Python tooling** - Never use system-wide Python or pip directly
   - Python operations: `mise exec -- python <command>`
   - Install dependencies: `mise exec -- uv pip install <package>`
   - Run tests: `mise exec -- pytest tests/`
   - This ensures consistent Python version and dependency management

### Terminology

- Use **"Location"** (not "scene" or "room") for places in the game world
- Use **"Location graph"** to refer to the connected network of locations
- Use **"natural language parsing"** for converting player input to game commands
- Use **"dynamic description generation"** for LLM-enhanced text output

### Python Development Environment

**ALWAYS use mise and uv - NEVER use system Python or direct pip!**

This project uses `mise` for version management and `uv` for fast, reliable dependency management.

**Common commands:**
```bash
# Run Python scripts
mise exec -- python script.py

# Install dependencies
mise exec -- uv pip install package-name

# Install dev dependencies
mise exec -- uv pip install pytest pytest-asyncio

# Run tests
mise exec -- pytest tests/ -v

# Run specific test file
mise exec -- pytest tests/test_service.py -v

# Start development server
mise exec -- uvicorn app.main:app --reload --port 8000

# Run migrations
mise exec -- python -m app.cli migrate
```

**Why mise and uv?**
- Ensures consistent Python version across all environments
- `uv` is 10-100x faster than pip
- Avoids conflicts with system Python packages
- Reproducible builds and deployments

**NEVER do this:**
- ❌ `python script.py`
- ❌ `pip install package`
- ❌ `pytest tests/`

**ALWAYS do this:**
- ✅ `mise exec -- python script.py`
- ✅ `mise exec -- uv pip install package`
- ✅ `mise exec -- pytest tests/`

### Key Technical Decisions

#### Backend Structure
- Use FastAPI for REST API endpoints
- Implement clear separation between:
  - Game engine (core logic)
  - State management (persistence)
  - LLM service (AI integration)
  - API layer (HTTP interface)

#### Frontend Structure
- Build as a single-page application
- Implement a terminal-like text interface
- Keep UI state separate from game state
- Use React hooks for state management

#### Database Schema
- Design flexible document schemas for:
  - Locations (with connections, items, descriptions)
  - Game state (player position, inventory, flags)
  - Players/Sessions (for multi-user support later)

#### LLM Integration
- Abstract LLM calls behind a service interface
- Implement proper error handling and fallbacks
- Cache/memoize common responses where appropriate
- Document all prompts and expected response structures
- **Scout LLM API:** The project uses Scout as the LLM provider
  - API Documentation: https://documenter.getpostman.com/view/1922400/2sAYkDPMcb
  - Configuration: Set `SCOUT_API_URL`, `SCOUT_API_ACCESS_TOKEN`, and `SCOUT_MODEL` in `.env`
  - Default model: `gpt-5`

### Getting Started

The recommended sequence for initial tasks:

1. **Setup: Initialize project structure**
2. **Backend: Set up Python project with FastAPI**
3. **Frontend: Initialize React app**
4. **Database: Choose and set up document database**
5. **Core: Define Location data model**
6. **Core: Implement game state manager**

After these foundation tasks, you can work on LLM integration, UI implementation, and content creation in parallel.

### Testing Strategy

**CRITICAL: Tests must be written for ALL services before committing!**

- **Write tests FIRST or IMMEDIATELY after creating services** - No exceptions
- Use pytest with in-memory TinyDB for fast, isolated tests
- Test file location: `backend/tests/test_<service_name>.py`
- Required test coverage:
  - Unit tests for all public methods
  - Edge cases (empty inputs, invalid data, missing resources)
  - Error handling (invalid sessions, nonexistent items, etc.)
  - Integration tests showing full workflows
- Test LLM integration with mock responses using `unittest.mock.AsyncMock`
- Run tests before every commit: `mise exec -- pytest tests/ -v`
- All tests must pass before pushing code

**Example test structure:**
```python
# tests/test_my_service.py
import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

@pytest.fixture
def db():
    return TinyDB(storage=MemoryStorage)

def test_feature_name(db):
    # Arrange, Act, Assert
    pass
```

### Documentation

Keep documentation up-to-date in:
- Code comments for complex logic
- API documentation (OpenAPI/Swagger)
- Architecture decisions in ADR format (if needed)
- LLM prompts in a dedicated prompts directory

### Questions or Blockers?

If you encounter unclear requirements or technical decisions that need to be made:
1. Check the Notion page for additional context
2. Look for similar patterns in existing code
3. Make a reasonable decision and document it
4. Flag it for review if it's a major architectural choice

---

**Remember:** This is an iterative project. Start simple, get it working, then enhance. The goal is to have a playable MVP before adding advanced features.