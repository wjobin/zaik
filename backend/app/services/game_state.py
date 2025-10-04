"""
Game State Manager service for Zaik.

Manages game session state with TinyDB persistence, providing operations for
managing player sessions, inventory, locations, and game flags.
"""

from typing import List, Optional
from datetime import datetime
from uuid import uuid4
from tinydb import TinyDB, Query

from ..models import GameSession


class GameStateManager:
    """
    Manages game session state with TinyDB persistence.

    Handles all operations related to player game sessions including
    creating/loading sessions, moving between locations, managing inventory,
    and tracking game state flags.
    """

    def __init__(self, db: TinyDB):
        """
        Initialize the game state manager.

        Args:
            db: TinyDB instance for persistence
        """
        self.sessions = db.table('game_sessions')
        self._query = Query()

    # ===== Session Management =====

    def create_session(
        self,
        adventure_id: str,
        starting_location_id: str,
        player_name: Optional[str] = None
    ) -> GameSession:
        """
        Create a new game session.

        Args:
            adventure_id: ID of the adventure to play
            starting_location_id: Location where player starts
            player_name: Optional player name for this session

        Returns:
            Newly created GameSession
        """
        session = GameSession(
            id=str(uuid4()),
            adventure_id=adventure_id,
            current_location_id=starting_location_id,
            player_name=player_name,
            visited_locations={starting_location_id}  # Start location is visited
        )
        self.save_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[GameSession]:
        """
        Retrieve a game session by ID.

        Args:
            session_id: ID of the session to retrieve

        Returns:
            GameSession if found, None otherwise
        """
        result = self.sessions.get(self._query.id == session_id)
        if result:
            return GameSession(**result)
        return None

    def save_session(self, session: GameSession) -> None:
        """
        Save or update a game session.

        Args:
            session: GameSession to save
        """
        session.updated_at = datetime.now()
        session.last_played_at = datetime.now()

        # Convert session to dict for TinyDB storage
        session_dict = session.model_dump()
        # Convert set to list for JSON serialization
        session_dict['visited_locations'] = list(session_dict['visited_locations'])
        # Convert datetime objects to ISO strings for JSON serialization
        session_dict['created_at'] = session_dict['created_at'].isoformat()
        session_dict['updated_at'] = session_dict['updated_at'].isoformat()
        session_dict['last_played_at'] = session_dict['last_played_at'].isoformat()

        # Upsert: update if exists, insert if new
        self.sessions.upsert(session_dict, self._query.id == session.id)

    def delete_session(self, session_id: str) -> None:
        """
        Delete a game session.

        Args:
            session_id: ID of the session to delete
        """
        self.sessions.remove(self._query.id == session_id)

    def list_sessions(self, adventure_id: Optional[str] = None) -> List[GameSession]:
        """
        List all game sessions, optionally filtered by adventure.

        Args:
            adventure_id: If provided, only return sessions for this adventure

        Returns:
            List of GameSession objects
        """
        if adventure_id:
            results = self.sessions.search(self._query.adventure_id == adventure_id)
        else:
            results = self.sessions.all()

        return [GameSession(**result) for result in results]

    # ===== Location Operations =====

    def move_to_location(self, session_id: str, location_id: str) -> GameSession:
        """
        Move player to a new location.

        Args:
            session_id: ID of the session
            location_id: ID of the target location

        Returns:
            Updated GameSession

        Raises:
            ValueError: If session not found
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.current_location_id = location_id
        session.visited_locations.add(location_id)
        self.save_session(session)
        return session

    def get_current_location(self, session_id: str) -> str:
        """
        Get the player's current location ID.

        Args:
            session_id: ID of the session

        Returns:
            Current location ID

        Raises:
            ValueError: If session not found
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        return session.current_location_id

    def has_visited_location(self, session_id: str, location_id: str) -> bool:
        """
        Check if player has visited a location.

        Args:
            session_id: ID of the session
            location_id: ID of the location to check

        Returns:
            True if location has been visited, False otherwise

        Raises:
            ValueError: If session not found
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        return location_id in session.visited_locations

    # ===== Inventory Operations =====

    def add_item(self, session_id: str, item_id: str) -> GameSession:
        """
        Add an item to player's inventory.

        Args:
            session_id: ID of the session
            item_id: ID of the item to add

        Returns:
            Updated GameSession

        Raises:
            ValueError: If session not found
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if item_id not in session.inventory:
            session.inventory.append(item_id)
        self.save_session(session)
        return session

    def remove_item(self, session_id: str, item_id: str) -> GameSession:
        """
        Remove an item from player's inventory.

        Args:
            session_id: ID of the session
            item_id: ID of the item to remove

        Returns:
            Updated GameSession

        Raises:
            ValueError: If session not found or item not in inventory
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if item_id not in session.inventory:
            raise ValueError(f"Item {item_id} not in inventory")

        session.inventory.remove(item_id)
        self.save_session(session)
        return session

    def has_item(self, session_id: str, item_id: str) -> bool:
        """
        Check if player has an item in inventory.

        Args:
            session_id: ID of the session
            item_id: ID of the item to check

        Returns:
            True if item is in inventory, False otherwise

        Raises:
            ValueError: If session not found
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        return item_id in session.inventory

    def get_inventory(self, session_id: str) -> List[str]:
        """
        Get player's current inventory.

        Args:
            session_id: ID of the session

        Returns:
            List of item IDs in inventory

        Raises:
            ValueError: If session not found
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        return session.inventory.copy()

    # ===== State Flag Operations =====

    def set_location_flag(
        self,
        session_id: str,
        location_id: str,
        flag_name: str,
        value: bool
    ) -> GameSession:
        """
        Set a location-specific state flag.

        Args:
            session_id: ID of the session
            location_id: ID of the location
            flag_name: Name of the flag to set
            value: Boolean value for the flag

        Returns:
            Updated GameSession

        Raises:
            ValueError: If session not found
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if location_id not in session.location_states:
            session.location_states[location_id] = {}

        session.location_states[location_id][flag_name] = value
        self.save_session(session)
        return session

    def get_location_flag(
        self,
        session_id: str,
        location_id: str,
        flag_name: str
    ) -> bool:
        """
        Get a location-specific state flag.

        Args:
            session_id: ID of the session
            location_id: ID of the location
            flag_name: Name of the flag to get

        Returns:
            Flag value (defaults to False if not set)

        Raises:
            ValueError: If session not found
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        return session.location_states.get(location_id, {}).get(flag_name, False)

    def set_global_flag(
        self,
        session_id: str,
        flag_name: str,
        value: bool
    ) -> GameSession:
        """
        Set a global game state flag.

        Args:
            session_id: ID of the session
            flag_name: Name of the flag to set
            value: Boolean value for the flag

        Returns:
            Updated GameSession

        Raises:
            ValueError: If session not found
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.global_flags[flag_name] = value
        self.save_session(session)
        return session

    def get_global_flag(self, session_id: str, flag_name: str) -> bool:
        """
        Get a global game state flag.

        Args:
            session_id: ID of the session
            flag_name: Name of the flag to get

        Returns:
            Flag value (defaults to False if not set)

        Raises:
            ValueError: If session not found
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        return session.global_flags.get(flag_name, False)
