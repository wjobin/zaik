"""
Game session data model for Zaik.

This model represents player-specific game state, separate from the immutable
adventure content. Each player's playthrough of an adventure has its own GameSession.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Set
from datetime import datetime


class GameSession(BaseModel):
    """
    Represents a player's game session (save file).

    This tracks all player-specific state including location, inventory,
    visited locations, and game flags. Multiple players can play the same
    adventure simultaneously, each with their own session.
    """

    id: str = Field(
        ...,
        description="Unique session identifier (UUID)"
    )
    adventure_id: str = Field(
        ...,
        description="ID of the adventure being played"
    )
    player_name: Optional[str] = Field(
        None,
        description="Optional player name for this session"
    )

    # Location state
    current_location_id: str = Field(
        ...,
        description="Location ID where the player currently is"
    )
    visited_locations: Set[str] = Field(
        default_factory=set,
        description="Set of location IDs the player has visited"
    )

    # Inventory
    inventory: List[str] = Field(
        default_factory=list,
        description="List of item IDs in player's inventory"
    )

    # Location-specific state
    location_states: Dict[str, Dict[str, bool]] = Field(
        default_factory=dict,
        description=(
            "Per-location state flags. "
            "Example: {'forest_clearing': {'item_taken_machete': True, 'puzzle_solved': False}}"
        )
    )

    # Global game state
    global_flags: Dict[str, bool] = Field(
        default_factory=dict,
        description=(
            "Global game state flags for story progression. "
            "Example: {'temple_door_unlocked': True, 'met_wizard': False}"
        )
    )

    # Session metadata
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When this session was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="When this session was last updated"
    )
    last_played_at: datetime = Field(
        default_factory=datetime.now,
        description="When this session was last played"
    )

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
            set: lambda v: list(v),  # Serialize sets as lists for JSON
        }
    }
