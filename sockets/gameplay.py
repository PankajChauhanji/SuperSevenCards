"""Gameplay handlers: throwing cards and drawing.

All authority lives here and in the room — the client only sends a selection of
card ids; the server decides whether it is legal, what action it is, and what
happens next. After every change the room broadcasts an authoritative
`table_state` snapshot (counts only) plus a private `your_hand` to whoever's
hand changed, so clients never drift from server truth.

call_stop and the turn timer arrive in later phases.
"""
from flask_socketio import emit

from game.room import STATE_IN_TURN
from game.rules import infer_action
from sockets.common import error


def register(socketio, manager):

    def _resolve(data):
        """Common guard: returns (room, user_id) or (None, None) after erroring."""
        data = data or {}
        code = (data.get("code") or "").strip().upper()
        user_id = data.get("user_id")
        room = manager.get_room(code)
        if room is None:
            error("This room no longer exists.")
            return None, None
        if room.state != STATE_IN_TURN:
            error("The game is not in play.")
            return None, None
        if room.current_turn_id() != user_id:
            error("It's not your turn.")
            return None, None
        return room, user_id

    @socketio.on("play_cards")
    def on_play(data):
        room, user_id = _resolve(data)
        if room is None:
            return
        if room.awaiting_draw:
            return error("Draw a card before playing again.")

        card_ids = (data or {}).get("card_ids") or []
        cards = room.card_objects(user_id, card_ids)
        if cards is None:
            return error("Those cards aren't in your hand.")

        action = infer_action(
            [c.rank for c in cards],
            room.last_was_combo,
            room.center_rank_set(),
        )
        if action is None:
            return error("That's not a legal play.")

        owes_draw = room.apply_throw(user_id, cards, action)

        # Notify the table what was played (faces are public — they're on the table).
        emit(
            "cards_played",
            {
                "by": user_id,
                "action_type": action,
                "played": [c.to_dict() for c in cards],
                "owes_draw": owes_draw,
            },
            to=room.code,
        )
        # The thrower's hand changed — send it privately.
        emit("your_hand", {"cards": room.hand_for(user_id)})
        # Authoritative snapshot for everyone.
        emit("table_state", room.public_round_state(), to=room.code)

    @socketio.on("draw_card")
    def on_draw(data):
        room, user_id = _resolve(data)
        if room is None:
            return
        if not room.awaiting_draw:
            return error("There's no draw to take right now.")

        reshuffled = room.draw_one(user_id)

        emit("your_hand", {"cards": room.hand_for(user_id)})
        if reshuffled:
            emit("deck_reshuffled", {}, to=room.code)
        emit("table_state", room.public_round_state(), to=room.code)
