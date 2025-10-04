"""
Command models for natural language parsing in Zaik.

These models represent structured commands that the game engine can execute,
parsed from natural language player input.
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class CommandType(str, Enum):
    """Types of commands that can be executed in the game."""

    # Movement
    MOVE = "move"

    # Item interaction
    TAKE = "take"
    DROP = "drop"
    EXAMINE = "examine"
    USE = "use"

    # Information
    LOOK = "look"
    INVENTORY = "inventory"

    # Special
    HELP = "help"
    UNKNOWN = "unknown"


class GameCommand(BaseModel):
    """
    Represents a parsed game command.

    This is the structured output from the natural language parser
    that the game engine can execute.
    """

    type: CommandType = Field(
        ...,
        description="The type of command to execute"
    )

    target: Optional[str] = Field(
        None,
        description="Primary target of the command (e.g., direction for move, item name for take)"
    )

    secondary_target: Optional[str] = Field(
        None,
        description="Secondary target for commands like 'use X on Y'"
    )

    raw_input: str = Field(
        ...,
        description="Original player input for logging/debugging"
    )

    confidence: float = Field(
        default=1.0,
        description="Parser confidence in the command (0.0 to 1.0)"
    )

    error_message: Optional[str] = Field(
        None,
        description="Error message if command couldn't be parsed properly"
    )


class CommandResult(BaseModel):
    """
    Result of executing a command.

    Contains the outcome message and any state changes.
    """

    success: bool = Field(
        ...,
        description="Whether the command was executed successfully"
    )

    message: str = Field(
        ...,
        description="Message to display to the player"
    )

    location_changed: bool = Field(
        default=False,
        description="Whether the player's location changed"
    )

    inventory_changed: bool = Field(
        default=False,
        description="Whether the player's inventory changed"
    )
