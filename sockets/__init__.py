"""Socket handler registration.

Each concern lives in its own module (connection / lobby / ... gameplay later)
so the event contract stays easy to audit. `register_handlers` wires them all
to the SocketIO instance against a shared RoomManager.
"""
from sockets import connection, lobby


def register_handlers(socketio, manager):
    connection.register(socketio, manager)
    lobby.register(socketio, manager)
