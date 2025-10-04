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

### Terminology

- Use **"Location"** (not "scene" or "room") for places in the game world
- Use **"Location graph"** to refer to the connected network of locations
- Use **"natural language parsing"** for converting player input to game commands
- Use **"dynamic description generation"** for LLM-enhanced text output

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

- Write unit tests for core game logic
- Test LLM integration with mock responses
- Create integration tests for the full game loop
- Manual playtest each location and interaction

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