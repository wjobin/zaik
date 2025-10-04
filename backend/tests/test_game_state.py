"""
Tests for Game State Manager
"""

import pytest
from datetime import datetime
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from app.services import GameStateManager
from app.models import GameSession


@pytest.fixture
def db():
    """Create an in-memory TinyDB instance for testing"""
    return TinyDB(storage=MemoryStorage)


@pytest.fixture
def game_state_manager(db):
    """Create a GameStateManager with in-memory database"""
    return GameStateManager(db)


@pytest.fixture
def sample_session(game_state_manager):
    """Create a sample game session for testing"""
    return game_state_manager.create_session(
        adventure_id="test_adventure",
        starting_location_id="start_location",
        player_name="TestPlayer"
    )


# ===== Session Management Tests =====

def test_create_session(game_state_manager):
    """Test creating a new game session"""
    session = game_state_manager.create_session(
        adventure_id="adventure_1",
        starting_location_id="location_1",
        player_name="Alice"
    )

    assert session.id is not None
    assert session.adventure_id == "adventure_1"
    assert session.current_location_id == "location_1"
    assert session.player_name == "Alice"
    assert "location_1" in session.visited_locations
    assert len(session.inventory) == 0
    assert len(session.location_states) == 0
    assert len(session.global_flags) == 0


def test_create_session_without_player_name(game_state_manager):
    """Test creating a session without player name"""
    session = game_state_manager.create_session(
        adventure_id="adventure_1",
        starting_location_id="location_1"
    )

    assert session.player_name is None
    assert session.adventure_id == "adventure_1"


def test_get_session(game_state_manager, sample_session):
    """Test retrieving a session by ID"""
    retrieved = game_state_manager.get_session(sample_session.id)

    assert retrieved is not None
    assert retrieved.id == sample_session.id
    assert retrieved.adventure_id == sample_session.adventure_id
    assert retrieved.player_name == sample_session.player_name


def test_get_nonexistent_session(game_state_manager):
    """Test retrieving a session that doesn't exist"""
    result = game_state_manager.get_session("nonexistent_id")
    assert result is None


def test_save_session_updates_timestamps(game_state_manager, sample_session):
    """Test that saving a session updates timestamps"""
    original_updated_at = sample_session.updated_at

    # Wait a tiny bit to ensure timestamp changes
    import time
    time.sleep(0.01)

    game_state_manager.save_session(sample_session)

    retrieved = game_state_manager.get_session(sample_session.id)
    assert retrieved.updated_at > original_updated_at
    assert retrieved.last_played_at > original_updated_at


def test_delete_session(game_state_manager, sample_session):
    """Test deleting a session"""
    session_id = sample_session.id

    # Verify it exists
    assert game_state_manager.get_session(session_id) is not None

    # Delete it
    game_state_manager.delete_session(session_id)

    # Verify it's gone
    assert game_state_manager.get_session(session_id) is None


def test_list_sessions(game_state_manager):
    """Test listing all sessions"""
    # Create multiple sessions
    session1 = game_state_manager.create_session("adventure_1", "loc_1")
    session2 = game_state_manager.create_session("adventure_2", "loc_1")
    session3 = game_state_manager.create_session("adventure_1", "loc_1")

    # List all sessions
    all_sessions = game_state_manager.list_sessions()
    assert len(all_sessions) == 3

    # List sessions for specific adventure
    adventure1_sessions = game_state_manager.list_sessions(adventure_id="adventure_1")
    assert len(adventure1_sessions) == 2
    assert all(s.adventure_id == "adventure_1" for s in adventure1_sessions)


# ===== Location Operations Tests =====

def test_move_to_location(game_state_manager, sample_session):
    """Test moving to a new location"""
    new_location = "new_location"

    updated_session = game_state_manager.move_to_location(
        sample_session.id,
        new_location
    )

    assert updated_session.current_location_id == new_location
    assert new_location in updated_session.visited_locations
    assert "start_location" in updated_session.visited_locations


def test_move_to_location_invalid_session(game_state_manager):
    """Test moving with invalid session ID"""
    with pytest.raises(ValueError, match="Session .* not found"):
        game_state_manager.move_to_location("invalid_id", "some_location")


def test_get_current_location(game_state_manager, sample_session):
    """Test getting current location"""
    location = game_state_manager.get_current_location(sample_session.id)
    assert location == "start_location"


def test_get_current_location_invalid_session(game_state_manager):
    """Test getting current location with invalid session"""
    with pytest.raises(ValueError, match="Session .* not found"):
        game_state_manager.get_current_location("invalid_id")


def test_has_visited_location(game_state_manager, sample_session):
    """Test checking if location has been visited"""
    # Starting location should be visited
    assert game_state_manager.has_visited_location(
        sample_session.id,
        "start_location"
    ) is True

    # New location should not be visited
    assert game_state_manager.has_visited_location(
        sample_session.id,
        "unvisited_location"
    ) is False

    # Move to new location
    game_state_manager.move_to_location(sample_session.id, "unvisited_location")

    # Now it should be visited
    assert game_state_manager.has_visited_location(
        sample_session.id,
        "unvisited_location"
    ) is True


def test_has_visited_location_invalid_session(game_state_manager):
    """Test checking visited location with invalid session"""
    with pytest.raises(ValueError, match="Session .* not found"):
        game_state_manager.has_visited_location("invalid_id", "some_location")


# ===== Inventory Operations Tests =====

def test_add_item(game_state_manager, sample_session):
    """Test adding an item to inventory"""
    updated_session = game_state_manager.add_item(sample_session.id, "sword")

    assert "sword" in updated_session.inventory
    assert len(updated_session.inventory) == 1


def test_add_duplicate_item(game_state_manager, sample_session):
    """Test that adding duplicate item doesn't create duplicates"""
    game_state_manager.add_item(sample_session.id, "sword")
    game_state_manager.add_item(sample_session.id, "sword")

    session = game_state_manager.get_session(sample_session.id)
    assert session.inventory.count("sword") == 1


def test_add_item_invalid_session(game_state_manager):
    """Test adding item with invalid session"""
    with pytest.raises(ValueError, match="Session .* not found"):
        game_state_manager.add_item("invalid_id", "sword")


def test_remove_item(game_state_manager, sample_session):
    """Test removing an item from inventory"""
    # Add item first
    game_state_manager.add_item(sample_session.id, "sword")

    # Remove it
    updated_session = game_state_manager.remove_item(sample_session.id, "sword")

    assert "sword" not in updated_session.inventory
    assert len(updated_session.inventory) == 0


def test_remove_nonexistent_item(game_state_manager, sample_session):
    """Test removing an item that's not in inventory"""
    with pytest.raises(ValueError, match="Item .* not in inventory"):
        game_state_manager.remove_item(sample_session.id, "nonexistent_item")


def test_remove_item_invalid_session(game_state_manager):
    """Test removing item with invalid session"""
    with pytest.raises(ValueError, match="Session .* not found"):
        game_state_manager.remove_item("invalid_id", "sword")


def test_has_item(game_state_manager, sample_session):
    """Test checking if player has an item"""
    # Initially no items
    assert game_state_manager.has_item(sample_session.id, "sword") is False

    # Add item
    game_state_manager.add_item(sample_session.id, "sword")

    # Should have it now
    assert game_state_manager.has_item(sample_session.id, "sword") is True


def test_has_item_invalid_session(game_state_manager):
    """Test checking item with invalid session"""
    with pytest.raises(ValueError, match="Session .* not found"):
        game_state_manager.has_item("invalid_id", "sword")


def test_get_inventory(game_state_manager, sample_session):
    """Test getting complete inventory"""
    # Add multiple items
    game_state_manager.add_item(sample_session.id, "sword")
    game_state_manager.add_item(sample_session.id, "shield")
    game_state_manager.add_item(sample_session.id, "potion")

    inventory = game_state_manager.get_inventory(sample_session.id)

    assert len(inventory) == 3
    assert "sword" in inventory
    assert "shield" in inventory
    assert "potion" in inventory


def test_get_inventory_returns_copy(game_state_manager, sample_session):
    """Test that get_inventory returns a copy, not a reference"""
    game_state_manager.add_item(sample_session.id, "sword")

    inventory = game_state_manager.get_inventory(sample_session.id)
    inventory.append("hacked_item")

    # Original inventory should not be modified
    actual_inventory = game_state_manager.get_inventory(sample_session.id)
    assert "hacked_item" not in actual_inventory


def test_get_inventory_invalid_session(game_state_manager):
    """Test getting inventory with invalid session"""
    with pytest.raises(ValueError, match="Session .* not found"):
        game_state_manager.get_inventory("invalid_id")


# ===== State Flag Operations Tests =====

def test_set_location_flag(game_state_manager, sample_session):
    """Test setting a location-specific flag"""
    updated_session = game_state_manager.set_location_flag(
        sample_session.id,
        "forest",
        "puzzle_solved",
        True
    )

    assert "forest" in updated_session.location_states
    assert updated_session.location_states["forest"]["puzzle_solved"] is True


def test_set_multiple_location_flags(game_state_manager, sample_session):
    """Test setting multiple flags for same location"""
    game_state_manager.set_location_flag(
        sample_session.id, "forest", "puzzle_solved", True
    )
    game_state_manager.set_location_flag(
        sample_session.id, "forest", "treasure_found", False
    )

    session = game_state_manager.get_session(sample_session.id)
    assert session.location_states["forest"]["puzzle_solved"] is True
    assert session.location_states["forest"]["treasure_found"] is False


def test_set_location_flag_invalid_session(game_state_manager):
    """Test setting location flag with invalid session"""
    with pytest.raises(ValueError, match="Session .* not found"):
        game_state_manager.set_location_flag(
            "invalid_id", "forest", "puzzle_solved", True
        )


def test_get_location_flag(game_state_manager, sample_session):
    """Test getting a location-specific flag"""
    # Set a flag
    game_state_manager.set_location_flag(
        sample_session.id, "forest", "puzzle_solved", True
    )

    # Get it back
    value = game_state_manager.get_location_flag(
        sample_session.id, "forest", "puzzle_solved"
    )

    assert value is True


def test_get_location_flag_default_false(game_state_manager, sample_session):
    """Test that getting unset flag returns False"""
    value = game_state_manager.get_location_flag(
        sample_session.id, "forest", "nonexistent_flag"
    )

    assert value is False


def test_get_location_flag_invalid_session(game_state_manager):
    """Test getting location flag with invalid session"""
    with pytest.raises(ValueError, match="Session .* not found"):
        game_state_manager.get_location_flag(
            "invalid_id", "forest", "puzzle_solved"
        )


def test_set_global_flag(game_state_manager, sample_session):
    """Test setting a global game flag"""
    updated_session = game_state_manager.set_global_flag(
        sample_session.id,
        "dragon_defeated",
        True
    )

    assert updated_session.global_flags["dragon_defeated"] is True


def test_set_multiple_global_flags(game_state_manager, sample_session):
    """Test setting multiple global flags"""
    game_state_manager.set_global_flag(
        sample_session.id, "dragon_defeated", True
    )
    game_state_manager.set_global_flag(
        sample_session.id, "quest_started", True
    )
    game_state_manager.set_global_flag(
        sample_session.id, "boss_encountered", False
    )

    session = game_state_manager.get_session(sample_session.id)
    assert session.global_flags["dragon_defeated"] is True
    assert session.global_flags["quest_started"] is True
    assert session.global_flags["boss_encountered"] is False


def test_set_global_flag_invalid_session(game_state_manager):
    """Test setting global flag with invalid session"""
    with pytest.raises(ValueError, match="Session .* not found"):
        game_state_manager.set_global_flag("invalid_id", "flag", True)


def test_get_global_flag(game_state_manager, sample_session):
    """Test getting a global game flag"""
    # Set a flag
    game_state_manager.set_global_flag(
        sample_session.id, "dragon_defeated", True
    )

    # Get it back
    value = game_state_manager.get_global_flag(
        sample_session.id, "dragon_defeated"
    )

    assert value is True


def test_get_global_flag_default_false(game_state_manager, sample_session):
    """Test that getting unset global flag returns False"""
    value = game_state_manager.get_global_flag(
        sample_session.id, "nonexistent_flag"
    )

    assert value is False


def test_get_global_flag_invalid_session(game_state_manager):
    """Test getting global flag with invalid session"""
    with pytest.raises(ValueError, match="Session .* not found"):
        game_state_manager.get_global_flag("invalid_id", "dragon_defeated")


# ===== Integration Tests =====

def test_complete_game_flow(game_state_manager):
    """Test a complete game flow with multiple operations"""
    # Create session
    session = game_state_manager.create_session(
        adventure_id="temple_quest",
        starting_location_id="entrance"
    )

    # Move around
    game_state_manager.move_to_location(session.id, "courtyard")
    game_state_manager.move_to_location(session.id, "treasure_room")

    # Collect items
    game_state_manager.add_item(session.id, "golden_key")
    game_state_manager.add_item(session.id, "ancient_sword")

    # Set some flags
    game_state_manager.set_location_flag(
        session.id, "courtyard", "door_unlocked", True
    )
    game_state_manager.set_global_flag(
        session.id, "temple_explored", True
    )

    # Verify final state
    final_session = game_state_manager.get_session(session.id)

    assert final_session.current_location_id == "treasure_room"
    assert len(final_session.visited_locations) == 3
    assert "entrance" in final_session.visited_locations
    assert "courtyard" in final_session.visited_locations
    assert "treasure_room" in final_session.visited_locations

    assert len(final_session.inventory) == 2
    assert "golden_key" in final_session.inventory
    assert "ancient_sword" in final_session.inventory

    assert final_session.location_states["courtyard"]["door_unlocked"] is True
    assert final_session.global_flags["temple_explored"] is True


def test_session_persistence(db):
    """Test that sessions persist across manager instances"""
    # Create manager and session
    manager1 = GameStateManager(db)
    session = manager1.create_session("adventure_1", "start")
    manager1.add_item(session.id, "sword")
    session_id = session.id

    # Create new manager with same database
    manager2 = GameStateManager(db)
    retrieved_session = manager2.get_session(session_id)

    assert retrieved_session is not None
    assert retrieved_session.id == session_id
    assert "sword" in retrieved_session.inventory
