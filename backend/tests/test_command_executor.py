"""
Tests for Command Executor Service
"""

import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from app.services.command_executor import CommandExecutor
from app.services.game_state import GameStateManager
from app.models.commands import GameCommand, CommandType
from app.models.adventure import Adventure, Location, Exit, Item


@pytest.fixture
def db():
    """Create an in-memory TinyDB instance for testing"""
    return TinyDB(storage=MemoryStorage)


@pytest.fixture
def sample_adventure(db):
    """Create a sample adventure in the database"""
    adventure = {
        "id": "test_adventure",
        "name": "Test Adventure",
        "description": "A test adventure",
        "starting_location_id": "room1",
        "locations": {
            "room1": {
                "id": "room1",
                "name": "First Room",
                "description": "A simple test room",
                "exits": {
                    "north": {
                        "direction": "north",
                        "location_id": "room2",
                        "description": "A door to the north",
                        "locked": False
                    },
                    "east": {
                        "direction": "east",
                        "location_id": "locked_room",
                        "description": "A locked door",
                        "locked": True,
                        "required_item": "key"
                    }
                },
                "items": [
                    {
                        "id": "sword",
                        "name": "iron sword",
                        "description": "A rusty iron sword",
                        "takeable": True,
                        "visible": True
                    },
                    {
                        "id": "table",
                        "name": "wooden table",
                        "description": "A heavy wooden table",
                        "takeable": False,
                        "visible": True
                    }
                ]
            },
            "room2": {
                "id": "room2",
                "name": "Second Room",
                "description": "Another test room",
                "exits": {
                    "south": {
                        "direction": "south",
                        "location_id": "room1",
                        "description": "Back to the first room",
                        "locked": False
                    }
                },
                "items": [
                    {
                        "id": "key",
                        "name": "brass key",
                        "description": "A shiny brass key",
                        "takeable": True,
                        "visible": True
                    }
                ]
            },
            "locked_room": {
                "id": "locked_room",
                "name": "Locked Room",
                "description": "A room behind a locked door",
                "exits": {},
                "items": []
            }
        }
    }

    adventures_table = db.table('adventures')
    adventures_table.insert(adventure)
    return adventure


@pytest.fixture
def game_state_manager(db):
    """Create a GameStateManager"""
    return GameStateManager(db)


@pytest.fixture
def executor(db):
    """Create a CommandExecutor"""
    return CommandExecutor(db)


@pytest.fixture
def test_session(game_state_manager, sample_adventure):
    """Create a test game session"""
    return game_state_manager.create_session(
        adventure_id="test_adventure",
        starting_location_id="room1",
        player_name="TestPlayer"
    )


# ===== Look Command Tests =====

def test_execute_look(executor, test_session):
    """Test executing a look command"""
    command = GameCommand(
        type=CommandType.LOOK,
        raw_input="look"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is True
    assert "First Room" in result.message
    assert "A simple test room" in result.message
    assert "north" in result.message
    assert result.location_changed is False


# ===== Inventory Command Tests =====

def test_execute_inventory_empty(executor, test_session):
    """Test executing inventory command with empty inventory"""
    command = GameCommand(
        type=CommandType.INVENTORY,
        raw_input="inventory"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is True
    assert "not carrying anything" in result.message.lower() or "aren't carrying" in result.message.lower()


def test_execute_inventory_with_items(executor, test_session, game_state_manager):
    """Test executing inventory command with items"""
    # Add items to inventory
    game_state_manager.add_item(test_session.id, "sword")
    game_state_manager.add_item(test_session.id, "key")

    command = GameCommand(
        type=CommandType.INVENTORY,
        raw_input="inventory"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is True
    assert "sword" in result.message
    assert "key" in result.message


# ===== Movement Command Tests =====

def test_execute_move_valid(executor, test_session):
    """Test moving to a valid location"""
    command = GameCommand(
        type=CommandType.MOVE,
        target="north",
        raw_input="go north"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is True
    assert result.location_changed is True
    assert "Second Room" in result.message


def test_execute_move_invalid_direction(executor, test_session):
    """Test moving in an invalid direction"""
    command = GameCommand(
        type=CommandType.MOVE,
        target="west",
        raw_input="go west"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is False
    assert result.location_changed is False
    assert "can't go that way" in result.message.lower()


def test_execute_move_no_target(executor, test_session):
    """Test movement command without target"""
    command = GameCommand(
        type=CommandType.MOVE,
        target=None,
        raw_input="go"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is False
    assert "which direction" in result.message.lower()


def test_execute_move_locked_exit(executor, test_session):
    """Test moving through a locked exit"""
    command = GameCommand(
        type=CommandType.MOVE,
        target="east",
        raw_input="go east"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is False
    assert result.location_changed is False
    assert "locked" in result.message.lower()


# ===== Take Command Tests =====

def test_execute_take_valid_item(executor, test_session, game_state_manager):
    """Test taking a valid takeable item"""
    command = GameCommand(
        type=CommandType.TAKE,
        target="sword",
        raw_input="take sword"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is True
    assert result.inventory_changed is True
    assert "take" in result.message.lower() or "picked up" in result.message.lower()

    # Verify item is in inventory
    session = game_state_manager.get_session(test_session.id)
    assert "sword" in session.inventory


def test_execute_take_untakeable_item(executor, test_session):
    """Test taking an item that cannot be taken"""
    command = GameCommand(
        type=CommandType.TAKE,
        target="table",
        raw_input="take table"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is False
    assert "can't take" in result.message.lower()


def test_execute_take_nonexistent_item(executor, test_session):
    """Test taking an item that doesn't exist"""
    command = GameCommand(
        type=CommandType.TAKE,
        target="banana",
        raw_input="take banana"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is False
    assert "don't see" in result.message.lower()


def test_execute_take_already_in_inventory(executor, test_session, game_state_manager):
    """Test taking an item already in inventory"""
    # Add item to inventory first
    game_state_manager.add_item(test_session.id, "sword")

    command = GameCommand(
        type=CommandType.TAKE,
        target="sword",
        raw_input="take sword"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is False
    assert "already have" in result.message.lower()


def test_execute_take_no_target(executor, test_session):
    """Test take command without target"""
    command = GameCommand(
        type=CommandType.TAKE,
        target=None,
        raw_input="take"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is False
    assert "what do you want to take" in result.message.lower() or "can see" in result.message.lower()


# ===== Drop Command Tests =====

def test_execute_drop_valid_item(executor, test_session, game_state_manager):
    """Test dropping an item from inventory"""
    # Add item to inventory first
    game_state_manager.add_item(test_session.id, "sword")

    command = GameCommand(
        type=CommandType.DROP,
        target="sword",
        raw_input="drop sword"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is True
    assert result.inventory_changed is True
    assert "drop" in result.message.lower()

    # Verify item is no longer in inventory
    session = game_state_manager.get_session(test_session.id)
    assert "sword" not in session.inventory


def test_execute_drop_item_not_in_inventory(executor, test_session):
    """Test dropping an item not in inventory"""
    command = GameCommand(
        type=CommandType.DROP,
        target="sword",
        raw_input="drop sword"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is False
    assert "don't have" in result.message.lower()


def test_execute_drop_no_target_empty_inventory(executor, test_session):
    """Test drop command without target and empty inventory"""
    command = GameCommand(
        type=CommandType.DROP,
        target=None,
        raw_input="drop"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is False
    assert "not carrying" in result.message.lower()


# ===== Examine Command Tests =====

def test_execute_examine_visible_item(executor, test_session):
    """Test examining a visible item in location"""
    command = GameCommand(
        type=CommandType.EXAMINE,
        target="sword",
        raw_input="examine sword"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is True
    assert "rusty iron sword" in result.message.lower()


def test_execute_examine_inventory_item(executor, test_session, game_state_manager):
    """Test examining an item in inventory"""
    game_state_manager.add_item(test_session.id, "key")

    command = GameCommand(
        type=CommandType.EXAMINE,
        target="key",
        raw_input="examine key"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is True
    assert "key" in result.message.lower()


def test_examine_nonexistent_item(executor, test_session):
    """Test examining an item that doesn't exist"""
    command = GameCommand(
        type=CommandType.EXAMINE,
        target="banana",
        raw_input="examine banana"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is False
    assert "don't see" in result.message.lower()


def test_execute_examine_no_target(executor, test_session):
    """Test examine command without target"""
    command = GameCommand(
        type=CommandType.EXAMINE,
        target=None,
        raw_input="examine"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is False
    assert "what do you want to examine" in result.message.lower()


# ===== Use Command Tests =====

def test_execute_use_item(executor, test_session, game_state_manager):
    """Test using an item"""
    game_state_manager.add_item(test_session.id, "key")

    command = GameCommand(
        type=CommandType.USE,
        target="key",
        raw_input="use key"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is True
    assert "use" in result.message.lower()


def test_execute_use_item_on_target(executor, test_session, game_state_manager):
    """Test using an item on another target"""
    game_state_manager.add_item(test_session.id, "key")

    command = GameCommand(
        type=CommandType.USE,
        target="key",
        secondary_target="door",
        raw_input="use key on door"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is True
    assert "key" in result.message.lower()
    assert "door" in result.message.lower()


def test_execute_use_item_not_in_inventory(executor, test_session):
    """Test using an item not in inventory"""
    command = GameCommand(
        type=CommandType.USE,
        target="key",
        raw_input="use key"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is False
    assert "don't have" in result.message.lower()


# ===== Help Command Tests =====

def test_execute_help(executor, test_session):
    """Test executing help command"""
    command = GameCommand(
        type=CommandType.HELP,
        raw_input="help"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is True
    assert "command" in result.message.lower()
    assert "movement" in result.message.lower() or "move" in result.message.lower()


# ===== Unknown Command Tests =====

def test_execute_unknown(executor, test_session):
    """Test executing unknown command"""
    command = GameCommand(
        type=CommandType.UNKNOWN,
        raw_input="xyzzy",
        error_message="I don't understand 'xyzzy'"
    )

    result = executor.execute(command, test_session.id)

    assert result.success is False
    assert "don't understand" in result.message.lower()


# ===== Error Handling Tests =====

def test_execute_with_invalid_session(executor):
    """Test executing command with non-existent session"""
    command = GameCommand(
        type=CommandType.LOOK,
        raw_input="look"
    )

    result = executor.execute(command, "invalid_session_id")

    assert result.success is False
    assert "not found" in result.message.lower()


# ===== Integration Tests =====

def test_full_gameplay_scenario(executor, test_session, game_state_manager):
    """Test a complete gameplay scenario"""
    # Look around
    result = executor.execute(
        GameCommand(type=CommandType.LOOK, raw_input="look"),
        test_session.id
    )
    assert result.success is True
    assert "First Room" in result.message

    # Take sword
    result = executor.execute(
        GameCommand(type=CommandType.TAKE, target="sword", raw_input="take sword"),
        test_session.id
    )
    assert result.success is True

    # Check inventory
    result = executor.execute(
        GameCommand(type=CommandType.INVENTORY, raw_input="inventory"),
        test_session.id
    )
    assert result.success is True
    assert "sword" in result.message

    # Move north
    result = executor.execute(
        GameCommand(type=CommandType.MOVE, target="north", raw_input="go north"),
        test_session.id
    )
    assert result.success is True
    assert "Second Room" in result.message

    # Verify we're in the new location
    session = game_state_manager.get_session(test_session.id)
    assert session.current_location_id == "room2"
    assert "room1" in session.visited_locations
    assert "room2" in session.visited_locations
