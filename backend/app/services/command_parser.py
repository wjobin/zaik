"""
Command Parser Service for Zaik.

Converts natural language player input into structured game commands using LLM.
Includes fallback pattern matching for when LLM is unavailable.
"""

import json
import re
import logging
from typing import Optional, Dict, Any
from ..models.commands import GameCommand, CommandType
from ..models.adventure import Location
from ..llm import ScoutLLMService, LLMMessage

logger = logging.getLogger(__name__)


class CommandParser:
    """
    Parses natural language commands into structured GameCommand objects.

    Uses LLM for flexible natural language understanding with fallback
    to pattern matching when LLM is unavailable.
    """

    def __init__(self, llm_service: Optional[ScoutLLMService] = None):
        """
        Initialize the command parser.

        Args:
            llm_service: Optional LLM service for natural language parsing
        """
        self.llm_service = llm_service

    def _build_context_prompt(
        self,
        location: Location,
        inventory: list[str]
    ) -> str:
        """
        Build context information for the LLM parser.

        Args:
            location: Current location data
            inventory: Player's current inventory

        Returns:
            Context string for the system prompt
        """
        # Extract available exits
        exits = list(location.exits.keys())

        # Extract visible items
        items = [item.name for item in location.items if item.visible]

        context = f"""Current Location: {location.name}

Available Exits: {', '.join(exits) if exits else 'none'}
Visible Items: {', '.join(items) if items else 'none'}
Player Inventory: {', '.join(inventory) if inventory else 'empty'}"""

        return context

    def _get_system_prompt(self, context: str) -> str:
        """
        Generate the system prompt for the LLM parser.

        Args:
            context: Current game context

        Returns:
            System prompt string
        """
        return f"""You are a command parser for a text adventure game. Your job is to convert natural language player input into structured JSON commands.

{context}

Parse the player's input and return ONLY a valid JSON object with this structure:
{{
  "type": "command_type",
  "target": "target_name",
  "secondary_target": null,
  "confidence": 0.95
}}

Valid command types:
- "move": Go to a different location (target = exit direction)
- "take": Pick up an item (target = item name)
- "drop": Drop an item from inventory (target = item name)
- "examine": Look at something closely (target = item or location feature)
- "use": Use an item (target = item, secondary_target = what to use it on)
- "look": Look around current location (no target needed)
- "inventory": Check inventory (no target needed)
- "help": Get help (no target needed)
- "unknown": Could not parse command

Rules:
1. Match targets to available exits, items, or inventory items
2. Be flexible with phrasing ("go north", "walk north", "head north" all = move north)
3. If target is ambiguous, pick the most likely one
4. If command makes no sense, return type "unknown"
5. Set confidence 0.0-1.0 based on how certain you are
6. Return ONLY valid JSON, no extra text

Examples:
"go north" → {{"type": "move", "target": "north", "confidence": 1.0}}
"pick up the candle" → {{"type": "take", "target": "candle", "confidence": 0.95}}
"look around" → {{"type": "look", "confidence": 1.0}}
"examine altar" → {{"type": "examine", "target": "altar", "confidence": 1.0}}
"asdf jkl" → {{"type": "unknown", "confidence": 0.0}}"""

    async def parse_command(
        self,
        player_input: str,
        location: Location,
        inventory: list[str]
    ) -> GameCommand:
        """
        Parse natural language input into a structured command.

        Args:
            player_input: Raw player input string
            location: Current location data for context
            inventory: Player's inventory for context

        Returns:
            Parsed GameCommand
        """
        # Try LLM parsing first if available
        if self.llm_service and self.llm_service.config.is_configured():
            try:
                logger.info(f"Attempting LLM parse for: '{player_input}'")
                return await self._parse_with_llm(player_input, location, inventory)
            except Exception as e:
                logger.error(f"LLM parsing failed: {type(e).__name__}: {e}")
                logger.exception("Full LLM parsing exception:")
                logger.warning("Falling back to pattern matching")

        # Fallback to pattern matching
        logger.info("Using pattern matching for command parsing")
        return self._parse_with_patterns(player_input, location, inventory)

    async def _parse_with_llm(
        self,
        player_input: str,
        location: Location,
        inventory: list[str]
    ) -> GameCommand:
        """
        Parse command using LLM.

        Args:
            player_input: Raw player input
            location: Current location
            inventory: Player inventory

        Returns:
            Parsed GameCommand
        """
        context = self._build_context_prompt(location, inventory)
        system_prompt = self._get_system_prompt(context)

        # Call LLM with low temperature for consistent parsing
        response = await self.llm_service.generate_text(
            prompt=player_input,
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=150
        )

        # Parse JSON response
        try:
            # Extract JSON from response (in case LLM adds extra text)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                parsed = json.loads(response)

            return GameCommand(
                type=CommandType(parsed.get("type", "unknown")),
                target=parsed.get("target"),
                secondary_target=parsed.get("secondary_target"),
                raw_input=player_input,
                confidence=parsed.get("confidence", 0.5)
            )
        except (json.JSONDecodeError, ValueError) as e:
            # If JSON parsing fails, fall back to pattern matching
            print(f"Failed to parse LLM JSON response: {e}")
            return self._parse_with_patterns(player_input, location, inventory)

    def _parse_with_patterns(
        self,
        player_input: str,
        location: Location,
        inventory: list[str]
    ) -> GameCommand:
        """
        Parse command using simple pattern matching (fallback).

        Args:
            player_input: Raw player input
            location: Current location
            inventory: Player inventory

        Returns:
            Parsed GameCommand
        """
        normalized = player_input.lower().strip()

        # Inventory commands
        if normalized in ["inventory", "i", "inv"]:
            return GameCommand(
                type=CommandType.INVENTORY,
                raw_input=player_input,
                confidence=1.0
            )

        # Look commands
        if normalized in ["look", "l", "look around"]:
            return GameCommand(
                type=CommandType.LOOK,
                raw_input=player_input,
                confidence=1.0
            )

        # Help commands
        if normalized in ["help", "?"]:
            return GameCommand(
                type=CommandType.HELP,
                raw_input=player_input,
                confidence=1.0
            )

        # Movement commands
        move_patterns = [
            (r'^(?:go|walk|move|head|run)\s+(?:to\s+)?(?:the\s+)?(\w+)$', 1.0),
            (r'^(?:north|south|east|west|n|s|e|w|up|down|u|d)$', 1.0),
            (r'^(\w+)$', 0.5)  # Single word might be direction
        ]

        for pattern, confidence in move_patterns:
            match = re.match(pattern, normalized)
            if match:
                direction = match.group(1) if match.lastindex else normalized
                # Check if it's a valid exit
                if direction in location.exits:
                    return GameCommand(
                        type=CommandType.MOVE,
                        target=direction,
                        raw_input=player_input,
                        confidence=confidence
                    )

        # Take/get commands
        take_patterns = [
            r'^(?:take|get|pick up|grab|pickup)\s+(?:the\s+)?(.+)$',
            r'^(?:take|get|pick up|grab|pickup)$'
        ]

        for pattern in take_patterns:
            match = re.match(pattern, normalized)
            if match:
                target = match.group(1) if match.lastindex else None
                return GameCommand(
                    type=CommandType.TAKE,
                    target=target,
                    raw_input=player_input,
                    confidence=0.8
                )

        # Drop commands
        drop_patterns = [
            r'^(?:drop|discard|leave)\s+(?:the\s+)?(.+)$'
        ]

        for pattern in drop_patterns:
            match = re.match(pattern, normalized)
            if match:
                target = match.group(1) if match.lastindex else None
                return GameCommand(
                    type=CommandType.DROP,
                    target=target,
                    raw_input=player_input,
                    confidence=0.8
                )

        # Examine commands
        examine_patterns = [
            r'^(?:examine|inspect|look at|check|x)\s+(?:the\s+)?(.+)$'
        ]

        for pattern in examine_patterns:
            match = re.match(pattern, normalized)
            if match:
                target = match.group(1)
                return GameCommand(
                    type=CommandType.EXAMINE,
                    target=target,
                    raw_input=player_input,
                    confidence=0.8
                )

        # Use commands
        use_patterns = [
            r'^(?:use)\s+(?:the\s+)?(.+?)\s+(?:on|with)\s+(?:the\s+)?(.+)$',
            r'^(?:use)\s+(?:the\s+)?(.+)$'
        ]

        for pattern in use_patterns:
            match = re.match(pattern, normalized)
            if match:
                target = match.group(1)
                secondary = match.group(2) if match.lastindex >= 2 else None
                return GameCommand(
                    type=CommandType.USE,
                    target=target,
                    secondary_target=secondary,
                    raw_input=player_input,
                    confidence=0.7
                )

        # Unknown command
        return GameCommand(
            type=CommandType.UNKNOWN,
            raw_input=player_input,
            confidence=0.0,
            error_message=f"I don't understand '{player_input}'. Type 'help' for assistance."
        )
