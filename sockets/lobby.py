"""Lobby handlers.

Flow (keeps one socket per client, no flicker, no accidental room deletion):
  index page  --create_room--> register room + host, reply {code}, then navigate
  index page  --join_room---->  validate + register player, reply {code}, navigate
  game page   --enter_room--->  bind this socket, mark connected, broadcast roster
  host        --start_game-->   validate, flip state, broadcast game_started

Only enter_room binds the sid and joins the Socket.IO room, so navigating away
from the index page never marks anyone disconnected.
"""
from flask import request
from flask_socketio import join_room as sio_join, emit

from config import DEFAULT_SETTINGS, SETTINGS_BOUNDS, MIN_PLAYERS
from game.room import STATE_LOBBY, STATE_ROUND_END, STATE_GAME_END
from sockets.common import bind_sid, error

NAME_MAX = 20


def _clean_name(raw) -> str:
    return (raw or "").strip()[:NAME_MAX]


def _clean_settings(raw) -> dict:
    settings = dict(DEFAULT_SETTINGS)
    if isinstance(raw, dict):
        for key in settings:
            if key in raw:
                try:
                    settings[key] = int(raw[key])
                except (TypeError, ValueError):
                    pass
    for key, (lo, hi) in SETTINGS_BOUNDS.items():
        settings[key] = max(lo, min(hi, settings[key]))
    return settings


def register(socketio, manager):

    @socketio.on("create_room")
    def on_create(data):
        data = data or {}
        name = _clean_name(data.get("name"))
        user_id = data.get("user_id")
        if not user_id:
            return error("Missing identity.")
        if not name:
            return error("Pick a name first.")
        settings = _clean_settings(data.get("settings"))
        room = manager.create_room(user_id, name, settings)
        emit("room_created", {"code": room.code})

    @socketio.on("join_room")
    def on_join(data):
        data = data or {}
        code = (data.get("code") or "").strip().upper()
        name = _clean_name(data.get("name"))
        user_id = data.get("user_id")
        if not user_id:
            return error("Missing identity.")
        room = manager.get_room(code)
        if room is None:
            return error("No room with that code.")

        already_in = user_id in room.players
        if not already_in:
            if room.state != STATE_LOBBY:
                return error("That game has already started.")
            if room.is_full():
                return error("That room is full.")
            if not name:
                return error("Pick a name first.")

        room.register_player(user_id, name)
        emit("join_ok", {"code": code})

    @socketio.on("enter_room")
    def on_enter(data):
        """Game page attaches its live socket and gets the room snapshot."""
        data = data or {}
        code = (data.get("code") or "").strip().upper()
        name = _clean_name(data.get("name"))
        user_id = data.get("user_id")
        if not user_id:
            return error("Missing identity.")
        room = manager.get_room(code)
        if room is None:
            return error("This room no longer exists.")

        player = room.attach(user_id, request.sid, name)
        if player is None:
            return error("You are not in this room.")

        sio_join(code)
        bind_sid(request.sid, code, user_id)

        emit(
            "room_joined",
            {
                "code": code,
                "you": user_id,
                "state": room.state,
                "host_id": room.host_id,
                "settings": room.settings,
                "players": room.public_players(),
            },
        )
        emit(
            "player_list",
            {"players": room.public_players(), "host_id": room.host_id},
            to=code,
        )

        # Reconnecting mid-game: resend the appropriate view.
        if room.in_round():
            emit("round_start", room.public_round_state())
            emit("your_hand", {"cards": room.hand_for(user_id)})
        elif room.state == STATE_ROUND_END and getattr(room, "_last_result", None):
            emit("round_end", room.round_end_payload(room._last_result))
        elif room.state == STATE_GAME_END:
            emit("game_end", room.game_end_payload())

    @socketio.on("start_game")
    def on_start(data):
        data = data or {}
        code = (data.get("code") or "").strip().upper()
        user_id = data.get("user_id")
        room = manager.get_room(code)
        if room is None:
            return error("This room no longer exists.")
        if not room.is_host(user_id):
            return error("Only the host can start the game.")
        if room.state != STATE_LOBBY:
            return error("The game has already started.")
        if len(room.connected_players()) < MIN_PLAYERS:
            return error(f"Need at least {MIN_PLAYERS} players to start.")

        # Deal the first round and tell everyone.
        room.start_round()
        emit("round_start", room.public_round_state(), to=code)
        # Each player privately receives only their own hand — never others'.
        for player in room.connected_players():
            emit("your_hand", {"cards": room.hand_for(player.user_id)}, to=player.sid)

    @socketio.on("rematch")
    def on_rematch(data):
        data = data or {}
        code = (data.get("code") or "").strip().upper()
        user_id = data.get("user_id")
        room = manager.get_room(code)
        if room is None:
            return error("This room no longer exists.")
        if not room.is_host(user_id):
            return error("Only the host can start a rematch.")
        if room.state not in (STATE_ROUND_END, STATE_GAME_END):
            return error("You can only rematch once a game has finished.")

        room.reset_for_rematch()
        emit(
            "room_reset",
            {"players": room.public_players(), "host_id": room.host_id,
             "settings": room.settings},
            to=code,
        )
