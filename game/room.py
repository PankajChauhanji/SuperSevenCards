"""Room: the single source of truth for one game table.

Phase 0 scope covers the lobby lifecycle only: registering/attaching players,
host tracking and migration, and a placeholder game state. Dealing, turns,
scoring, and the timer arrive in later phases — the fields they need are added
when those phases are built so this file stays honest about what exists.
"""
import time
from typing import Dict, List, Optional

from config import MAX_PLAYERS, HAND_SIZE
from game.player import Player
from game.cards import shuffled_deck

# Game states. Turn actions (AWAITING_DRAW) and end states (ROUND_END | GAME_END)
# are wired in later phases; Phase 1 deals into IN_TURN and renders.
STATE_LOBBY = "LOBBY"
STATE_IN_TURN = "IN_TURN"


class Room:
    def __init__(self, code: str, host_id: str, settings: dict):
        self.code = code
        self.host_id = host_id
        self.settings = settings
        self.players: Dict[str, Player] = {}   # user_id -> Player
        self.state = STATE_LOBBY
        self.round_number = 0
        self.created_at = time.time()

        # Round state (populated by start_round)
        self.draw_pile: List = []
        self.discard_pile: List = []      # all thrown cards, for reshuffle
        self.center_throw: List = []      # the visible last throw
        self.last_was_combo = False       # gates Action D (Match) in Phase 2
        self.turn_order: List[str] = []   # active user_ids, seating order
        self.turn_index = 0

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

    # ---- round lifecycle ----
    def start_round(self) -> None:
        """Deal a fresh round. Active = connected and not eliminated."""
        active = [
            uid for uid, p in self.players.items()
            if p.connected and not p.eliminated
        ]
        deck = shuffled_deck()

        # Reset per-round player state.
        for player in self.players.values():
            player.hand = []
            player.is_safe = False
            player.round_score = 0

        for uid in active:
            self.players[uid].hand = [deck.pop() for _ in range(HAND_SIZE)]

        self.draw_pile = deck
        self.discard_pile = []
        self.center_throw = []
        self.last_was_combo = False
        self.turn_order = active
        self.turn_index = 0
        self.round_number += 1
        self.state = STATE_IN_TURN

    def current_turn_id(self) -> Optional[str]:
        if not self.turn_order:
            return None
        return self.turn_order[self.turn_index % len(self.turn_order)]

    def public_round_state(self) -> dict:
        """Common, privacy-safe snapshot shared by every player (no hands)."""
        return {
            "round_number": self.round_number,
            "current_turn": self.current_turn_id(),
            "turn_order": list(self.turn_order),
            "deck_count": len(self.draw_pile),
            "center": [c.to_dict() for c in self.center_throw],
            "last_was_combo": self.last_was_combo,
            "players": self.public_players(),
        }

    def hand_for(self, user_id: str) -> List[dict]:
        """A single player's own cards — sent only to that player."""
        player = self.players.get(user_id)
        return [c.to_dict() for c in player.hand] if player else []

    def in_round(self) -> bool:
        return self.state == STATE_IN_TURN

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
