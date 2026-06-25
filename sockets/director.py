"""The turn-timer director — the only background routine in the app.

Once a second it scans active rooms for a turn that has run past its deadline
and resolves it: auto-play a discard (or auto-draw if one was owed), and remove
a player who hits the timeout limit. It then broadcasts the consequences. This
is what keeps an AFK player from freezing the table.

Run as an eventlet background task started in app.py.
"""
from game.room import STATE_IN_TURN, STATE_GAME_END


def register(socketio, manager):
    def loop():
        while True:
            socketio.sleep(1)
            try:
                _tick(socketio, manager)
            except Exception:
                # A background loop must never die on a transient error.
                pass

    socketio.start_background_task(loop)


def _tick(socketio, manager):
    for code, room in list(manager.rooms.items()):
        if room.state != STATE_IN_TURN:
            continue
        cur = room.current_turn_id()
        if cur is None:
            continue

        # 1) Post-discard pick timer: auto-draw after the fixed 3s, NO penalty.
        #    While a draw is owed, the turn timer does not also fire.
        if room.awaiting_draw:
            if room.pick_timed_out():
                sid = room.players[cur].sid
                name = room.players[cur].name
                result = room.draw_one(cur)
                drawn_id = result["card"].id if result["card"] else None
                socketio.emit("auto_picked", {"user_id": cur, "name": name}, to=code)
                if result["reshuffled"]:
                    socketio.emit("deck_reshuffled", {}, to=code)
                if sid:
                    socketio.emit("your_hand",
                                  {"cards": room.hand_for(cur), "drawn": drawn_id}, to=sid)
                socketio.emit("table_state", room.public_round_state(), to=code)
            continue

        # 2) Turn timer: penalised auto-play / removal (only when no draw owed).
        if not room.is_timed_out():
            continue

        name = room.players[cur].name
        sid = room.players[cur].sid
        info = room.force_timeout(cur)

        socketio.emit(
            "player_timed_out",
            {"user_id": cur, "name": name,
             "timeout_count": info["timeout_count"], "removed": info["removed"]},
            to=code,
        )
        if info["removed"]:
            socketio.emit(
                "player_eliminated",
                {"user_id": cur, "name": name, "reason": "timeouts"},
                to=code,
            )

        # A mid-round removal can end the whole game.
        if room.state == STATE_GAME_END:
            socketio.emit("game_end", room.game_end_payload(), to=code)
            continue

        # If the auto-play left nobody able to act, the round ends now.
        if room.active_count() == 0:
            result = room.end_round(None)
            socketio.emit("round_end", room.round_end_payload(result), to=code)
            continue

        # Normal case: the turn moved on. Update the timed-out player's hand
        # (if still connected) and broadcast the new table state.
        if sid:
            socketio.emit("your_hand",
                          {"cards": room.hand_for(cur), "drawn": info.get("drawn")},
                          to=sid)
        socketio.emit("table_state", room.public_round_state(), to=code)
