"""Single-source configuration for Super Seven.

Gameplay tunables live here; runtime/deploy options come from environment
variables. Host-selectable settings start from DEFAULT_SETTINGS and may be
overridden per room when the room is created.
"""
import os

# ---- Room / table limits ----
MIN_PLAYERS = 2
MAX_PLAYERS = 6
ROOM_CODE_LENGTH = 4
HAND_SIZE = 7

# ---- Host-selectable game settings (defaults) ----
# A round's scores add to cumulative totals. A player whose cumulative total
# reaches MAX_SCORE is eliminated. Last player standing wins.
DEFAULT_SETTINGS = {
    "max_score": 100,      # cumulative total >= this -> eliminated
    "stop_penalty": 40,    # added to a caught Stop-caller's hand total
    "win_discount": 5,     # strictly-lowest caller scores max(total - this, 0)
    "turn_timer": 40,      # seconds per turn before auto-discard (Phase 4)
    "timeout_limit": 3,    # cumulative timeouts before a player is removed
    "num_decks": 1,        # number of 52-card decks shuffled together
}

# Bounds used to sanitise host-supplied settings.
SETTINGS_BOUNDS = {
    "max_score": (20, 1000),
    "stop_penalty": (0, 200),
    "win_discount": (0, 50),
    "turn_timer": (15, 180),
    "timeout_limit": (1, 10),
    "num_decks": (1, 10),
}

# Seconds a room with zero connected players is kept before being reaped.
EMPTY_ROOM_TTL = 60

# ---- Match-play draw rule ----
# If True, a Match still owes a draw afterwards (legacy behavior, same as a
# Single/Pair). If False, a Match behaves like a no-draw combo (Set/Sequence)
# and the turn advances immediately with no draw required.
# This is a server-only toggle — deliberately NOT part of DEFAULT_SETTINGS, so
# it can't be changed per-room from the lobby settings UI.
MATCH_REQUIRES_DRAW = False

# ---- Runtime / deployment ----
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
PORT = int(os.environ.get("PORT", "5000"))
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
