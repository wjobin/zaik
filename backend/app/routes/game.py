"""
Game API routes for Zaik.

Provides endpoints for:
- Creating new game sessions
- Sending player commands
- Getting current game state
- Serving location images
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional

from ..db import get_db
from ..services.game_state import GameStateManager
from ..services.command_parser import CommandParser
from ..services.command_executor import CommandExecutor
from ..services.image_service import get_image_service
from ..llm import get_llm_service
from ..models.adventure import Adventure, Location


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
    image_url: Optional[str] = None


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

    image_url = None
    if not adventure:
        message = f"You are at location: {session.current_location_id}"
    else:
        location = adventure['locations'].get(session.current_location_id)
        if location:
            message = f"{location['name']}\n\n{location['description']}"
            # Check if image exists for this location
            if session.current_location_id in session.location_images:
                image_filename = session.location_images[session.current_location_id]
                image_url = f"/api/game/images/{image_filename}"
        else:
            message = f"You are at location: {session.current_location_id}"

    return GameStateResponse(
        session_id=session.id,
        current_location_id=session.current_location_id,
        inventory=session.inventory,
        visited_locations=list(session.visited_locations),
        message=message,
        image_url=image_url
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
    Adventure_Query = Query()
    adventures_table = db.table('adventures')
    adventure_data = adventures_table.get(Adventure_Query.id == request.adventure_id)

    if not adventure_data:
        raise HTTPException(status_code=404, detail=f"Adventure '{request.adventure_id}' not found")

    starting_location_id = adventure_data['starting_location_id']

    session = manager.create_session(
        adventure_id=request.adventure_id,
        starting_location_id=starting_location_id,
        player_name=request.player_name
    )

    # Generate image for starting location
    try:
        adventure = Adventure(**adventure_data)
        location_data = adventure.locations.get(starting_location_id)
        if location_data:
            location = Location(**location_data) if isinstance(location_data, dict) else location_data
            image_service = get_image_service()
            image_filename = await image_service.generate_location_image(session.id, location)

            # Update session with image filename
            session.location_images[starting_location_id] = image_filename
            manager.save_session(session)
    except Exception as e:
        # Log but don't fail if image generation fails
        import logging
        logging.error(f"Failed to generate starting location image: {e}")

    return _format_game_state(session.id)


@router.post("/{session_id}/command", response_model=CommandResponse)
async def send_command(session_id: str, request: CommandRequest):
    """
    Send a command to the game.

    Processes a player command and returns the result along with
    the updated game state.
    """
    manager = _get_game_state_manager()
    db = get_db()

    # Verify session exists
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get adventure and current location for context
    from tinydb import Query
    Adventure_Query = Query()
    adventures_table = db.table('adventures')
    adventure_data = adventures_table.get(Adventure_Query.id == session.adventure_id)

    if not adventure_data:
        raise HTTPException(status_code=404, detail="Adventure not found")

    adventure = Adventure(**adventure_data)
    location_data = adventure.locations.get(session.current_location_id)
    if not location_data:
        raise HTTPException(status_code=404, detail="Current location not found")

    location = Location(**location_data) if isinstance(location_data, dict) else location_data

    # Parse the command
    llm_service = get_llm_service()
    parser = CommandParser(llm_service)
    parsed_command = await parser.parse_command(
        player_input=request.command,
        location=location,
        inventory=session.inventory
    )

    # Store old location for comparison
    old_location_id = session.current_location_id

    # Execute the command
    executor = CommandExecutor(db)
    result = executor.execute(parsed_command, session_id)

    # If command was successful and player moved, generate image for new location
    updated_session = manager.get_session(session_id)
    if updated_session and result.success and updated_session.current_location_id != old_location_id:
        try:
            new_location_data = adventure.locations.get(updated_session.current_location_id)
            if new_location_data:
                new_location = Location(**new_location_data) if isinstance(new_location_data, dict) else new_location_data
                image_service = get_image_service()
                image_filename = await image_service.generate_location_image(updated_session.id, new_location)

                # Update session with new image
                updated_session.location_images[updated_session.current_location_id] = image_filename
                manager.save_session(updated_session)
        except Exception as e:
            # Log but don't fail if image generation fails
            import logging
            logging.error(f"Failed to generate location image: {e}")

    return CommandResponse(
        success=result.success,
        message=result.message,
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


@router.get("/images/{image_filename}")
async def get_image(image_filename: str):
    """
    Serve a location image.

    Returns the image file for display in the game.
    """
    image_service = get_image_service()
    image_data = image_service.read_image(image_filename)

    if not image_data:
        raise HTTPException(status_code=404, detail="Image not found")

    return Response(content=image_data, media_type="image/png")
