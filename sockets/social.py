"""Light social handlers — currently just in-game emoji reactions.

The server only relays a whitelisted emoji to everyone at the table; the float
animation lives entirely on the client. Whitelisting keeps the channel from
being used to broadcast arbitrary text.
"""
from flask_socketio import emit

ALLOWED_REACTIONS = {
    "\U0001F602",  # 😂 laugh
    "\U0001F632",  # 😲 surprise
    "\U0001F92F",  # 🤯 mind blown
    "\U0001F62D",  # 😭 cry
    "\U0001F621",  # 😡 anger
    "\U0001F525",  # 🔥 nice move
    "\u26A1",      # ⚡ play faster
    "\U0001F44F",  # 👏 good game
    "\U0001F60E",  # 😎 smooth move
    "\U0001F389",  # 🎉 celebration
}


def register(socketio, manager):

    @socketio.on("reaction")
    def on_reaction(data):
        data = data or {}
        code = (data.get("code") or "").strip().upper()
        user_id = data.get("user_id")
        emoji = data.get("emoji")
        room = manager.get_room(code)
        if room is None or user_id not in room.players:
            return
        if emoji not in ALLOWED_REACTIONS:
            return
        emit(
            "reaction",
            {"user_id": user_id, "name": room.players[user_id].name, "emoji": emoji},
            to=code,
        )
