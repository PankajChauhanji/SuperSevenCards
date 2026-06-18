"""Room: the single source of truth for one game table.

Phase 0 scope covers the lobby lifecycle only: registering/attaching players,
host tracking and migration, and a placeholder game state. Dealing, turns,
scoring, and the timer arrive in later phases — the fields they need are added
when those phases are built so this file stays honest about what exists.
"""
import time
from typing import Dict, List, Optional

from config import MAX_PLAYERS
from game.player import Player

# Lobby-relevant states for Phase 0. The full state machine
# (DEALING | IN_TURN | AWAITING_DRAW | ROUND_END | GAME_END) lands later.
STATE_LOBBY = "LOBBY"
STATE_IN_GAME = "IN_GAME"  # placeholder until Phase 1 builds the table


class Room:
    def __init__(self, code: str, host_id: str, settings: dict):
        self.code = code
        self.host_id = host_id
        self.settings = settings
        self.players: Dict[str, Player] = {}   # user_id -> Player
        self.state = STATE_LOBBY
        self.round_number = 0
        self.created_at = time.time()

    # ---- registration / attachment ----
    def register_player(self, user_id: str, name: str) -> Player:
        """Add a player without binding a socket (pre-navigation step)."""
        player = self.players.get(user_id)
        if player is None:
            player = Player(user_id=user_id, name=name)
            self.players[user_id] = player
        elif name:
            player.name = name
        return player

    def attach(self, user_id: str, sid: str, name: str = "") -> Optional[Player]:
        """Bind a live socket to an already-registered player."""
        player = self.players.get(user_id)
        if player is None:
            return None
        player.sid = sid
        player.connected = True
        if name:
            player.name = name
        return player

    def detach(self, user_id: str) -> None:
        player = self.players.get(user_id)
        if player is not None:
            player.connected = False
            player.sid = ""

    def remove_player(self, user_id: str) -> None:
        self.players.pop(user_id, None)

    # ---- queries ----
    def is_full(self) -> bool:
        return len(self.players) >= MAX_PLAYERS

    def is_host(self, user_id: str) -> bool:
        return user_id == self.host_id

    def connected_players(self) -> List[Player]:
        return [p for p in self.players.values() if p.connected]

    def any_connected(self) -> bool:
        return any(p.connected for p in self.players.values())

    def public_players(self) -> List[dict]:
        return [p.public_view() for p in self.players.values()]

    # ---- host migration ----
    def migrate_host(self) -> Optional[str]:
        """Promote the next connected player to host. Returns new host id."""
        if self.host_id in self.players and self.players[self.host_id].connected:
            return self.host_id
        for player in self.players.values():
            if player.connected:
                self.host_id = player.user_id
                return self.host_id
        return None
