"""
Adventure and Location data models for Zaik.

These models represent the immutable game content structure (adventures, locations, items).
Player-specific state (current location, inventory, visited flags) is handled separately
in the game state manager.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime


class Exit(BaseModel):
    """Represents a connection from one location to another."""

    direction: str = Field(
        ...,
        description="Direction or exit name (e.g., 'north', 'door', 'stairs')"
    )
    location_id: str = Field(
        ...,
        description="ID of the target location"
    )
    description: Optional[str] = Field(
        None,
        description="Description of the exit (e.g., 'A wooden door')"
    )
    locked: bool = Field(
        default=False,
        description="Whether this exit is locked"
    )
    required_item: Optional[str] = Field(
        None,
        description="Item ID required to unlock this exit"
    )


class Item(BaseModel):
    """Represents an item that can exist in a location or player inventory."""

    id: str = Field(
        ...,
        description="Unique item identifier"
    )
    name: str = Field(
        ...,
        description="Item name shown to player"
    )
    description: str = Field(
        ...,
        description="Item description"
    )
    takeable: bool = Field(
        default=True,
        description="Whether the item can be picked up"
    )
    visible: bool = Field(
        default=True,
        description="Whether the item is visible (some items may be hidden until discovered)"
    )


class Location(BaseModel):
    """
    Represents a location in the game world.

    This is immutable game content - it does not contain player-specific state
    like whether the player has visited or what items they've taken.
    """

    id: str = Field(
        ...,
        description="Unique location identifier within the adventure"
    )
    name: str = Field(
        ...,
        description="Location name shown to player"
    )
    description: str = Field(
        ...,
        description="Base static description of the location"
    )
    exits: Dict[str, Exit] = Field(
        default_factory=dict,
        description="Available exits, keyed by direction/exit name"
    )
    items: List[Item] = Field(
        default_factory=list,
        description="Items initially present in this location"
    )
    mood: Optional[str] = Field(
        None,
        description="Mood/atmosphere for LLM description enhancement (e.g., 'dark', 'cheerful', 'mysterious')"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Location tags for categorization (e.g., 'outdoor', 'combat', 'puzzle')"
    )


class Adventure(BaseModel):
    """
    Represents a complete adventure/story with its location graph.

    An adventure is a self-contained game that can be played by multiple
    players simultaneously, each with their own game state.
    """

    id: str = Field(
        ...,
        description="Unique adventure identifier"
    )
    name: str = Field(
        ...,
        description="Adventure title shown to players"
    )
    description: str = Field(
        ...,
        description="Adventure summary/hook"
    )
    author: Optional[str] = Field(
        None,
        description="Adventure creator"
    )
    version: str = Field(
        default="1.0.0",
        description="Adventure version for tracking updates"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When this adventure was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="When this adventure was last updated"
    )
    starting_location_id: str = Field(
        ...,
        description="Location ID where players begin the adventure"
    )
    locations: Dict[str, Location] = Field(
        ...,
        description="All locations in this adventure, keyed by location ID"
    )
    difficulty: Optional[str] = Field(
        None,
        description="Difficulty level (e.g., 'easy', 'medium', 'hard')"
    )
    estimated_duration: Optional[int] = Field(
        None,
        description="Estimated completion time in minutes"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Adventure tags for categorization (e.g., 'fantasy', 'horror', 'sci-fi')"
    )
