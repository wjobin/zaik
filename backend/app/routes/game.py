"""
Game API routes for Zaik.

Provides endpoints for:
- Creating new game sessions
- Sending player commands
- Getting current game state
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..db import get_db
from ..services.game_state import GameStateManager


router = APIRouter(prefix="/api/game", tags=["game"])


# ===== Request/Response Models =====

class NewGameRequest(BaseModel):
    """Request to create a new game session."""
    adventure_id: str = "default"
    player_name: Optional[str] = None


class CommandRequest(BaseModel):
    """Request to send a command in a game session."""
    command: str


class GameStateResponse(BaseModel):
    """Current game state response."""
    session_id: str
    current_location_id: str
    inventory: list[str]
    visited_locations: list[str]
    message: str


class CommandResponse(BaseModel):
    """Response to a command."""
    success: bool
    message: str
    state: GameStateResponse


# ===== Helper Functions =====

def _get_game_state_manager() -> GameStateManager:
    """Get GameStateManager instance."""
    db = get_db()
    return GameStateManager(db)


def _format_game_state(session_id: str) -> GameStateResponse:
    """Format current game state as response."""
    manager = _get_game_state_manager()
    session = manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get location description from adventure data
    db = get_db()
    from tinydb import Query
    Adventure = Query()
    adventures_table = db.table('adventures')
    adventure = adventures_table.get(Adventure.id == session.adventure_id)

    if not adventure:
        message = f"You are at location: {session.current_location_id}"
    else:
        location = adventure['locations'].get(session.current_location_id)
        if location:
            message = f"{location['name']}\n\n{location['description']}"
        else:
            message = f"You are at location: {session.current_location_id}"

    return GameStateResponse(
        session_id=session.id,
        current_location_id=session.current_location_id,
        inventory=session.inventory,
        visited_locations=list(session.visited_locations),
        message=message
    )


# ===== Endpoints =====

@router.post("/new", response_model=GameStateResponse)
async def new_game(request: NewGameRequest):
    """
    Create a new game session.

    Creates a new game session for the specified adventure and returns
    the initial game state.
    """
    manager = _get_game_state_manager()
    db = get_db()

    # Look up the adventure
    from tinydb import Query
    Adventure = Query()
    adventures_table = db.table('adventures')
    adventure = adventures_table.get(Adventure.id == request.adventure_id)

    if not adventure:
        raise HTTPException(status_code=404, detail=f"Adventure '{request.adventure_id}' not found")

    starting_location = adventure['starting_location_id']

    session = manager.create_session(
        adventure_id=request.adventure_id,
        starting_location_id=starting_location,
        player_name=request.player_name
    )

    return _format_game_state(session.id)


@router.post("/{session_id}/command", response_model=CommandResponse)
async def send_command(session_id: str, request: CommandRequest):
    """
    Send a command to the game.

    Processes a player command and returns the result along with
    the updated game state.
    """
    manager = _get_game_state_manager()

    # Verify session exists
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # TODO: Implement actual command processing with LLM
    # For now, return a simple echo response
    message = f"You said: {request.command}"

    # Handle basic test commands
    command_lower = request.command.lower()
    if command_lower in ["inventory", "i"]:
        if session.inventory:
            message = f"You are carrying: {', '.join(session.inventory)}"
        else:
            message = "You are not carrying anything."
    elif command_lower in ["look", "l"]:
        message = f"You are at {session.current_location_id}. (Detailed description coming soon)"

    return CommandResponse(
        success=True,
        message=message,
        state=_format_game_state(session_id)
    )


@router.get("/{session_id}/state", response_model=GameStateResponse)
async def get_state(session_id: str):
    """
    Get the current game state.

    Returns the current state of the game session without
    processing any commands.
    """
    return _format_game_state(session_id)


@router.delete("/{session_id}")
async def delete_game(session_id: str):
    """
    Delete a game session.

    Permanently removes a game session from the database.
    """
    manager = _get_game_state_manager()

    # Verify session exists before deleting
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    manager.delete_session(session_id)
    return {"message": "Session deleted successfully"}
