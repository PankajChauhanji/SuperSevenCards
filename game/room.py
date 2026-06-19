"""Room: the single source of truth for one game table.

Phase 0 scope covers the lobby lifecycle only: registering/attaching players,
host tracking and migration, and a placeholder game state. Dealing, turns,
scoring, and the timer arrive in later phases — the fields they need are added
when those phases are built so this file stays honest about what exists.
"""
import time
import random
from typing import Dict, List, Optional

from config import MAX_PLAYERS, HAND_SIZE
from game.player import Player
from game.cards import shuffled_deck
from game.rules import DRAW_ACTIONS, COMBO_ACTIONS

# Game states. Turn actions (AWAITING_DRAW) and end states (ROUND_END | GAME_END)
# are wired in later phases; Phase 1 deals into IN_TURN and renders.
STATE_LOBBY = "LOBBY"
STATE_IN_TURN = "IN_TURN"
STATE_ROUND_END = "ROUND_END"


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
        self.awaiting_draw = False        # current player owes a draw
        self.turns_completed = 0          # completed turns this round
        self.initial_active = 0           # players dealt in this round
        self.first_orbit_complete = False # gates calling Stop
        self.last_caller = None           # who called Stop last round
        self.last_caught = False

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
        self.awaiting_draw = False
        self.turns_completed = 0
        self.initial_active = len(active)
        self.first_orbit_complete = False
        self.last_caller = None
        self.last_caught = False
        self.round_number += 1
        self.state = STATE_IN_TURN

    def current_turn_id(self) -> Optional[str]:
        if not self.turn_order:
            return None
        return self.turn_order[self.turn_index % len(self.turn_order)]

    def center_rank_set(self) -> set:
        """Rank set of the current matchable combo (empty if last wasn't combo)."""
        if not self.last_was_combo:
            return set()
        return {c.rank for c in self.center_throw}

    def card_objects(self, user_id: str, card_ids: List[str]) -> Optional[List]:
        """Resolve card ids to Card objects in the player's hand.

        Returns None if any id is missing or duplicated (an illegal selection).
        Card ids are unique within a deck, so a valid selection has no repeats.
        """
        player = self.players.get(user_id)
        if player is None or not card_ids:
            return None
        if len(set(card_ids)) != len(card_ids):
            return None
        by_id = {c.id: c for c in player.hand}
        cards = []
        for cid in card_ids:
            card = by_id.get(cid)
            if card is None:
                return None
            cards.append(card)
        return cards

    def apply_throw(self, user_id: str, cards: List, action: str) -> bool:
        """Apply a validated throw. Returns True if the player now owes a draw."""
        player = self.players[user_id]
        thrown_ids = {c.id for c in cards}
        player.hand = [c for c in player.hand if c.id not in thrown_ids]

        # The previous visible throw is now buried in the discard pile.
        self.discard_pile.extend(self.center_throw)
        self.center_throw = list(cards)
        # A match does NOT leave a matchable combo (no chaining).
        self.last_was_combo = action in COMBO_ACTIONS

        owes_draw = action in DRAW_ACTIONS
        if owes_draw:
            self.awaiting_draw = True
            # Turn does not advance until the draw is taken.
        else:
            # Only a no-draw combo can empty a hand -> player is safe.
            if not player.hand:
                player.is_safe = True
            self.awaiting_draw = False
            self.advance_turn()
        return owes_draw

    def draw_one(self, user_id: str) -> bool:
        """Take the owed draw, reshuffling if needed, then advance. True if reshuffled."""
        reshuffled = False
        if not self.draw_pile and self.discard_pile:
            # Reshuffle the buried discards (the visible center stays on the table).
            random.shuffle(self.discard_pile)
            self.draw_pile = self.discard_pile
            self.discard_pile = []
            reshuffled = True
        if self.draw_pile:
            self.players[user_id].hand.append(self.draw_pile.pop())
        # If both piles are empty there is nothing to draw; the turn still passes.
        self.awaiting_draw = False
        self.advance_turn()
        return reshuffled

    def advance_turn(self) -> None:
        """Move to the next player who can act (not safe, not eliminated)."""
        n = len(self.turn_order)
        if n == 0:
            return
        # One turn has just completed.
        self.turns_completed += 1
        if self.turns_completed >= self.initial_active:
            self.first_orbit_complete = True
        for _ in range(n):
            self.turn_index = (self.turn_index + 1) % n
            player = self.players.get(self.turn_order[self.turn_index])
            if player and not player.is_safe and not player.eliminated:
                return
        # No eligible player remains — the caller-less auto-end is handled
        # by the gameplay layer via active_count().

    def active_count(self) -> int:
        """Players still holding cards who can take a turn."""
        return sum(
            1 for uid in self.turn_order
            if not self.players[uid].is_safe and not self.players[uid].eliminated
        )

    def public_round_state(self) -> dict:
        """Common, privacy-safe snapshot shared by every player (no hands)."""
        return {
            "state": self.state,
            "round_number": self.round_number,
            "current_turn": self.current_turn_id(),
            "awaiting_draw": self.awaiting_draw,
            "first_orbit_complete": self.first_orbit_complete,
            "turn_order": list(self.turn_order),
            "deck_count": len(self.draw_pile),
            "center": [c.to_dict() for c in self.center_throw],
            "last_was_combo": self.last_was_combo,
            "players": self.public_players(),
        }

    # ---- round end / scoring ----
    def end_round(self, caller_id: Optional[str]) -> dict:
        """Score the round, apply totals, transition to ROUND_END."""
        from game.scoring import score_round

        participants = [
            (uid, self.players[uid].hand, self.players[uid].is_safe)
            for uid in self.turn_order
        ]
        result = score_round(participants, caller_id, self.settings)
        for uid, pts in result["scores"].items():
            self.players[uid].round_score = pts
            self.players[uid].total_score += pts

        self.last_caller = caller_id
        self.last_caught = result["caught"]
        self.awaiting_draw = False
        self.state = STATE_ROUND_END
        self._last_result = result
        return result

    def round_end_payload(self, result: dict) -> dict:
        """Full reveal — hands are public now that the round is over."""
        rows = []
        for uid in self.turn_order:
            player = self.players[uid]
            rows.append({
                "user_id": uid,
                "name": player.name,
                "hand": [c.to_dict() for c in player.hand],
                "hand_total": result["totals"][uid],
                "round_score": player.round_score,
                "total_score": player.total_score,
                "is_safe": player.is_safe,
            })
        return {
            "caller": self.last_caller,
            "caught": self.last_caught,
            "results": rows,
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
