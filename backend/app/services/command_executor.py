"""
Command Executor Service for Zaik.

Executes parsed game commands and updates game state accordingly.
"""

from typing import Optional
from tinydb import TinyDB, Query

from ..models.commands import GameCommand, CommandType, CommandResult
from ..models.adventure import Adventure, Location, Item
from ..models.game_session import GameSession
from .game_state import GameStateManager


class CommandExecutor:
    """
    Executes structured game commands and updates game state.

    Validates commands against game rules and provides appropriate
    feedback messages to the player.
    """

    def __init__(self, db: TinyDB):
        """
        Initialize the command executor.

        Args:
            db: TinyDB instance for accessing game data
        """
        self.db = db
        self.state_manager = GameStateManager(db)

    def _get_adventure(self, adventure_id: str) -> Optional[Adventure]:
        """Get adventure data from database."""
        adventures_table = self.db.table('adventures')
        Adventure_Query = Query()
        adventure_data = adventures_table.get(Adventure_Query.id == adventure_id)
        if adventure_data:
            return Adventure(**adventure_data)
        return None

    def _get_location(self, adventure: Adventure, location_id: str) -> Optional[Location]:
        """Get location from adventure."""
        location_data = adventure.locations.get(location_id)
        if location_data:
            return Location(**location_data) if isinstance(location_data, dict) else location_data
        return None

    def _find_item_in_location(self, location: Location, item_name: str) -> Optional[Item]:
        """
        Find an item in the location by name (fuzzy matching).

        Args:
            location: Location to search
            item_name: Item name to find

        Returns:
            Item if found, None otherwise
        """
        item_name_lower = item_name.lower()
        for item in location.items:
            if item.visible and (
                item.name.lower() == item_name_lower or
                item_name_lower in item.name.lower() or
                item.id.lower() == item_name_lower
            ):
                return item
        return None

    def execute(
        self,
        command: GameCommand,
        session_id: str
    ) -> CommandResult:
        """
        Execute a parsed command.

        Args:
            command: Parsed game command
            session_id: Game session ID

        Returns:
            CommandResult with outcome and message
        """
        # Get session
        session = self.state_manager.get_session(session_id)
        if not session:
            return CommandResult(
                success=False,
                message="Session not found"
            )

        # Get adventure and location
        adventure = self._get_adventure(session.adventure_id)
        if not adventure:
            return CommandResult(
                success=False,
                message="Adventure data not found"
            )

        location = self._get_location(adventure, session.current_location_id)
        if not location:
            return CommandResult(
                success=False,
                message="Current location not found"
            )

        # Route to appropriate handler
        handlers = {
            CommandType.MOVE: self._execute_move,
            CommandType.TAKE: self._execute_take,
            CommandType.DROP: self._execute_drop,
            CommandType.EXAMINE: self._execute_examine,
            CommandType.USE: self._execute_use,
            CommandType.LOOK: self._execute_look,
            CommandType.INVENTORY: self._execute_inventory,
            CommandType.HELP: self._execute_help,
            CommandType.UNKNOWN: self._execute_unknown,
        }

        handler = handlers.get(command.type)
        if handler:
            return handler(command, session, adventure, location)

        return CommandResult(
            success=False,
            message=f"Command type '{command.type}' not implemented"
        )

    def _execute_move(
        self,
        command: GameCommand,
        session: GameSession,
        adventure: Adventure,
        location: Location
    ) -> CommandResult:
        """Execute a movement command."""
        if not command.target:
            exits = ", ".join(location.exits.keys())
            return CommandResult(
                success=False,
                message=f"Which direction? Available exits: {exits}"
            )

        # Check if exit exists
        exit_data = location.exits.get(command.target)
        if not exit_data:
            exits = ", ".join(location.exits.keys())
            return CommandResult(
                success=False,
                message=f"You can't go that way. Available exits: {exits}"
            )

        # Check if exit is locked
        if exit_data.locked:
            if exit_data.required_item:
                return CommandResult(
                    success=False,
                    message=f"The {command.target} exit is locked. You need {exit_data.required_item}."
                )
            return CommandResult(
                success=False,
                message=f"The {command.target} exit is locked."
            )

        # Move player
        target_location_id = exit_data.location_id
        self.state_manager.move_to_location(session.id, target_location_id)

        # Get new location for description
        new_location = self._get_location(adventure, target_location_id)
        if new_location:
            message = f"{new_location.name}\n\n{new_location.description}"

            # Add exits info
            if new_location.exits:
                exits = ", ".join(new_location.exits.keys())
                message += f"\n\nVisible exits: {exits}"

            # Add items info
            visible_items = [item.name for item in new_location.items if item.visible]
            if visible_items:
                message += f"\n\nYou can see: {', '.join(visible_items)}"
        else:
            message = f"You go {command.target}."

        return CommandResult(
            success=True,
            message=message,
            location_changed=True
        )

    def _execute_take(
        self,
        command: GameCommand,
        session: GameSession,
        adventure: Adventure,
        location: Location
    ) -> CommandResult:
        """Execute a take/get command."""
        if not command.target:
            visible_items = [item.name for item in location.items if item.visible]
            if visible_items:
                return CommandResult(
                    success=False,
                    message=f"What do you want to take? You can see: {', '.join(visible_items)}"
                )
            return CommandResult(
                success=False,
                message="There's nothing here to take."
            )

        # Find the item
        item = self._find_item_in_location(location, command.target)
        if not item:
            return CommandResult(
                success=False,
                message=f"You don't see '{command.target}' here."
            )

        # Check if takeable
        if not item.takeable:
            return CommandResult(
                success=False,
                message=f"You can't take the {item.name}."
            )

        # Check if already in inventory
        if item.id in session.inventory:
            return CommandResult(
                success=False,
                message=f"You already have the {item.name}."
            )

        # Add to inventory
        self.state_manager.add_item(session.id, item.id)

        # Set location flag that item was taken
        self.state_manager.set_location_flag(
            session.id,
            location.id,
            f"item_taken_{item.id}",
            True
        )

        return CommandResult(
            success=True,
            message=f"You take the {item.name}.",
            inventory_changed=True
        )

    def _execute_drop(
        self,
        command: GameCommand,
        session: GameSession,
        adventure: Adventure,
        location: Location
    ) -> CommandResult:
        """Execute a drop command."""
        if not command.target:
            if session.inventory:
                items = ", ".join(session.inventory)
                return CommandResult(
                    success=False,
                    message=f"What do you want to drop? You're carrying: {items}"
                )
            return CommandResult(
                success=False,
                message="You're not carrying anything."
            )

        # Check if in inventory (fuzzy match)
        item_id = None
        for inv_item_id in session.inventory:
            if command.target.lower() in inv_item_id.lower():
                item_id = inv_item_id
                break

        if not item_id:
            return CommandResult(
                success=False,
                message=f"You don't have '{command.target}'."
            )

        # Remove from inventory
        self.state_manager.remove_item(session.id, item_id)

        return CommandResult(
            success=True,
            message=f"You drop the {item_id}.",
            inventory_changed=True
        )

    def _execute_examine(
        self,
        command: GameCommand,
        session: GameSession,
        adventure: Adventure,
        location: Location
    ) -> CommandResult:
        """Execute an examine command."""
        if not command.target:
            return CommandResult(
                success=False,
                message="What do you want to examine?"
            )

        # Check location items
        item = self._find_item_in_location(location, command.target)
        if item:
            return CommandResult(
                success=True,
                message=f"{item.name}: {item.description}"
            )

        # Check inventory
        for item_id in session.inventory:
            if command.target.lower() in item_id.lower():
                # TODO: Get item description from adventure data
                return CommandResult(
                    success=True,
                    message=f"You examine the {item_id}."
                )

        return CommandResult(
            success=False,
            message=f"You don't see '{command.target}' here."
        )

    def _execute_use(
        self,
        command: GameCommand,
        session: GameSession,
        adventure: Adventure,
        location: Location
    ) -> CommandResult:
        """Execute a use command."""
        if not command.target:
            return CommandResult(
                success=False,
                message="What do you want to use?"
            )

        # Check if item is in inventory
        if command.target not in session.inventory:
            return CommandResult(
                success=False,
                message=f"You don't have '{command.target}'."
            )

        # TODO: Implement item usage logic
        # For now, just acknowledge the command
        if command.secondary_target:
            return CommandResult(
                success=True,
                message=f"You try to use the {command.target} on the {command.secondary_target}, but nothing happens."
            )

        return CommandResult(
            success=True,
            message=f"You use the {command.target}."
        )

    def _execute_look(
        self,
        command: GameCommand,
        session: GameSession,
        adventure: Adventure,
        location: Location
    ) -> CommandResult:
        """Execute a look command."""
        message = f"{location.name}\n\n{location.description}"

        # Add exits
        if location.exits:
            exits = ", ".join(location.exits.keys())
            message += f"\n\nVisible exits: {exits}"

        # Add visible items
        visible_items = [item.name for item in location.items if item.visible]
        if visible_items:
            message += f"\n\nYou can see: {', '.join(visible_items)}"

        return CommandResult(
            success=True,
            message=message
        )

    def _execute_inventory(
        self,
        command: GameCommand,
        session: GameSession,
        adventure: Adventure,
        location: Location
    ) -> CommandResult:
        """Execute an inventory command."""
        if not session.inventory:
            return CommandResult(
                success=True,
                message="You aren't carrying anything."
            )

        items = ", ".join(session.inventory)
        return CommandResult(
            success=True,
            message=f"You are carrying: {items}"
        )

    def _execute_help(
        self,
        command: GameCommand,
        session: GameSession,
        adventure: Adventure,
        location: Location
    ) -> CommandResult:
        """Execute a help command."""
        help_text = """Available commands:
- Movement: go [direction], north, south, east, west, up, down
- Items: take [item], drop [item], examine [item], use [item]
- Information: look, inventory (or i)
- Other: help

You can use natural language! Try things like:
- "pick up the candle"
- "walk to the graveyard"
- "check my inventory"
"""
        return CommandResult(
            success=True,
            message=help_text
        )

    def _execute_unknown(
        self,
        command: GameCommand,
        session: GameSession,
        adventure: Adventure,
        location: Location
    ) -> CommandResult:
        """Handle unknown command."""
        message = command.error_message or f"I don't understand '{command.raw_input}'. Type 'help' for assistance."
        return CommandResult(
            success=False,
            message=message
        )
