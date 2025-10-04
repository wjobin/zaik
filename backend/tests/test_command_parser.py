"""
Tests for Command Parser Service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.command_parser import CommandParser
from app.models.commands import GameCommand, CommandType
from app.models.adventure import Location, Exit, Item


@pytest.fixture
def sample_location():
    """Create a sample location for testing"""
    return Location(
        id="test_room",
        name="Test Room",
        description="A test room for parsing commands",
        exits={
            "north": Exit(direction="north", location_id="north_room", description="A door to the north"),
            "south": Exit(direction="south", location_id="south_room", description="A door to the south")
        },
        items=[
            Item(id="sword", name="iron sword", description="A rusty iron sword", takeable=True, visible=True),
            Item(id="table", name="wooden table", description="A sturdy wooden table", takeable=False, visible=True),
        ]
    )


@pytest.fixture
def sample_inventory():
    """Create a sample inventory for testing"""
    return ["key", "torch"]


@pytest.fixture
def parser_no_llm():
    """Create a CommandParser without LLM (uses fallback only)"""
    return CommandParser(llm_service=None)


@pytest.fixture
def parser_with_mock_llm():
    """Create a CommandParser with mocked LLM service"""
    mock_llm = MagicMock()
    mock_llm.config.is_configured.return_value = True
    return CommandParser(llm_service=mock_llm)


# ===== Pattern Matching (Fallback) Tests =====

@pytest.mark.asyncio
async def test_parse_inventory_command(parser_no_llm, sample_location, sample_inventory):
    """Test parsing inventory commands"""
    commands = ["inventory", "i", "inv"]

    for cmd in commands:
        result = await parser_no_llm.parse_command(cmd, sample_location, sample_inventory)
        assert result.type == CommandType.INVENTORY
        assert result.confidence == 1.0


@pytest.mark.asyncio
async def test_parse_look_command(parser_no_llm, sample_location, sample_inventory):
    """Test parsing look commands"""
    commands = ["look", "l", "look around"]

    for cmd in commands:
        result = await parser_no_llm.parse_command(cmd, sample_location, sample_inventory)
        assert result.type == CommandType.LOOK
        assert result.confidence == 1.0


@pytest.mark.asyncio
async def test_parse_help_command(parser_no_llm, sample_location, sample_inventory):
    """Test parsing help commands"""
    commands = ["help", "?"]

    for cmd in commands:
        result = await parser_no_llm.parse_command(cmd, sample_location, sample_inventory)
        assert result.type == CommandType.HELP
        assert result.confidence == 1.0


@pytest.mark.asyncio
async def test_parse_movement_commands(parser_no_llm, sample_location, sample_inventory):
    """Test parsing movement commands"""
    test_cases = [
        ("go north", "north"),
        ("walk north", "north"),
        ("move to south", "south"),
        ("head south", "south"),
        ("north", "north"),
        ("n", None),  # 'n' is not in exits
    ]

    for cmd, expected_target in test_cases:
        result = await parser_no_llm.parse_command(cmd, sample_location, sample_inventory)
        if expected_target:
            assert result.type == CommandType.MOVE
            assert result.target == expected_target
        else:
            # If not a valid exit, should be unknown
            assert result.type == CommandType.UNKNOWN


@pytest.mark.asyncio
async def test_parse_take_commands(parser_no_llm, sample_location, sample_inventory):
    """Test parsing take/get commands"""
    test_cases = [
        "take the sword",
        "get sword",
        "pick up the sword",
        "grab sword",
        "pickup sword"
    ]

    for cmd in test_cases:
        result = await parser_no_llm.parse_command(cmd, sample_location, sample_inventory)
        assert result.type == CommandType.TAKE
        assert "sword" in result.target or result.target == "sword"


@pytest.mark.asyncio
async def test_parse_drop_commands(parser_no_llm, sample_location, sample_inventory):
    """Test parsing drop commands"""
    test_cases = [
        "drop the key",
        "discard torch",
        "leave key"
    ]

    for cmd in test_cases:
        result = await parser_no_llm.parse_command(cmd, sample_location, sample_inventory)
        assert result.type == CommandType.DROP
        assert result.target in ["key", "torch", "the key"]


@pytest.mark.asyncio
async def test_parse_examine_commands(parser_no_llm, sample_location, sample_inventory):
    """Test parsing examine commands"""
    test_cases = [
        ("examine sword", "sword"),
        ("inspect the table", "table"),
        ("look at sword", "sword"),
        ("check table", "table"),
        ("x sword", "sword")
    ]

    for cmd, expected_target in test_cases:
        result = await parser_no_llm.parse_command(cmd, sample_location, sample_inventory)
        assert result.type == CommandType.EXAMINE
        assert expected_target in result.target


@pytest.mark.asyncio
async def test_parse_use_commands(parser_no_llm, sample_location, sample_inventory):
    """Test parsing use commands"""
    # Use single item
    result = await parser_no_llm.parse_command("use key", sample_location, sample_inventory)
    assert result.type == CommandType.USE
    assert result.target == "key"
    assert result.secondary_target is None

    # Use item on something
    result = await parser_no_llm.parse_command("use key on door", sample_location, sample_inventory)
    assert result.type == CommandType.USE
    assert result.target == "key"
    assert result.secondary_target == "door"


@pytest.mark.asyncio
async def test_parse_unknown_command(parser_no_llm, sample_location, sample_inventory):
    """Test parsing unknown/invalid commands"""
    commands = [
        "asdf jkl",
        "xyzzy",
        "blah blah blah"
    ]

    for cmd in commands:
        result = await parser_no_llm.parse_command(cmd, sample_location, sample_inventory)
        assert result.type == CommandType.UNKNOWN
        assert result.confidence == 0.0
        assert result.error_message is not None


# ===== Context Building Tests =====

def test_build_context_prompt(parser_no_llm, sample_location, sample_inventory):
    """Test building context prompt for LLM"""
    context = parser_no_llm._build_context_prompt(sample_location, sample_inventory)

    # Should include location name
    assert "Test Room" in context

    # Should include exits
    assert "north" in context
    assert "south" in context

    # Should include visible items
    assert "iron sword" in context
    assert "wooden table" in context

    # Should include inventory
    assert "key" in context
    assert "torch" in context


def test_build_context_prompt_empty(parser_no_llm):
    """Test building context prompt with no exits/items/inventory"""
    empty_location = Location(
        id="empty",
        name="Empty Room",
        description="An empty room",
        exits={},
        items=[]
    )

    context = parser_no_llm._build_context_prompt(empty_location, [])

    assert "Empty Room" in context
    assert "none" in context.lower() or "empty" in context.lower()


# ===== LLM Integration Tests =====

@pytest.mark.asyncio
async def test_parse_with_llm_success(parser_with_mock_llm, sample_location, sample_inventory):
    """Test parsing with LLM when it returns valid JSON"""
    # Mock LLM to return valid command JSON
    parser_with_mock_llm.llm_service.generate_text = AsyncMock(
        return_value='{"type": "move", "target": "north", "confidence": 0.95}'
    )

    result = await parser_with_mock_llm.parse_command(
        "go to the northern door",
        sample_location,
        sample_inventory
    )

    assert result.type == CommandType.MOVE
    assert result.target == "north"
    assert result.confidence == 0.95


@pytest.mark.asyncio
async def test_parse_with_llm_json_with_extra_text(parser_with_mock_llm, sample_location, sample_inventory):
    """Test parsing when LLM returns JSON with extra text"""
    # Mock LLM to return JSON with preamble/postamble
    parser_with_mock_llm.llm_service.generate_text = AsyncMock(
        return_value='Sure, here is the parsed command: {"type": "take", "target": "sword", "confidence": 0.9}'
    )

    result = await parser_with_mock_llm.parse_command(
        "pick up the sword",
        sample_location,
        sample_inventory
    )

    assert result.type == CommandType.TAKE
    assert result.target == "sword"


@pytest.mark.asyncio
async def test_parse_with_llm_fallback_on_error(parser_with_mock_llm, sample_location, sample_inventory):
    """Test that parser falls back to patterns when LLM fails"""
    # Mock LLM to raise an error
    parser_with_mock_llm.llm_service.generate_text = AsyncMock(
        side_effect=Exception("LLM service error")
    )

    # Should fall back to pattern matching
    result = await parser_with_mock_llm.parse_command(
        "inventory",
        sample_location,
        sample_inventory
    )

    assert result.type == CommandType.INVENTORY
    assert result.confidence == 1.0


@pytest.mark.asyncio
async def test_parse_with_llm_fallback_on_invalid_json(parser_with_mock_llm, sample_location, sample_inventory):
    """Test that parser falls back when LLM returns invalid JSON"""
    # Mock LLM to return invalid JSON
    parser_with_mock_llm.llm_service.generate_text = AsyncMock(
        return_value='This is not valid JSON at all'
    )

    # Should fall back to pattern matching
    result = await parser_with_mock_llm.parse_command(
        "look",
        sample_location,
        sample_inventory
    )

    assert result.type == CommandType.LOOK


# ===== System Prompt Tests =====

def test_get_system_prompt(parser_no_llm):
    """Test generation of system prompt for LLM"""
    context = "Test context"
    prompt = parser_no_llm._get_system_prompt(context)

    # Should include context
    assert "Test context" in prompt

    # Should include command types
    assert "move" in prompt
    assert "take" in prompt
    assert "examine" in prompt

    # Should include examples
    assert "go north" in prompt

    # Should specify JSON format
    assert "JSON" in prompt or "json" in prompt


# ===== Edge Cases =====

@pytest.mark.asyncio
async def test_parse_empty_command(parser_no_llm, sample_location, sample_inventory):
    """Test parsing empty command"""
    result = await parser_no_llm.parse_command("", sample_location, sample_inventory)
    assert result.type == CommandType.UNKNOWN


@pytest.mark.asyncio
async def test_parse_whitespace_command(parser_no_llm, sample_location, sample_inventory):
    """Test parsing whitespace-only command"""
    result = await parser_no_llm.parse_command("   ", sample_location, sample_inventory)
    assert result.type == CommandType.UNKNOWN


@pytest.mark.asyncio
async def test_parse_case_insensitive(parser_no_llm, sample_location, sample_inventory):
    """Test that parsing is case-insensitive"""
    commands = [
        ("INVENTORY", CommandType.INVENTORY),
        ("Look", CommandType.LOOK),
        ("Go North", CommandType.MOVE),
        ("TAKE SWORD", CommandType.TAKE)
    ]

    for cmd, expected_type in commands:
        result = await parser_no_llm.parse_command(cmd, sample_location, sample_inventory)
        assert result.type == expected_type
