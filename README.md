# Super Seven

Real-time multiplayer card game (Flask-SocketIO + vanilla JS). Shed your hand,
call **Stop** when you think you're lowest, survive the elimination cap.

**Build status:** Phase 2 — Turn engine. Full turn play: select cards and
Throw, with the server inferring the action (single / set / sequence / match)
and enforcing legality; manual draw by clicking the deck when one is owed; turn
rotation; deck reshuffle when the draw pile empties. A live label shows what the
current selection will do. Endgame (Stop, scoring, elimination) and the turn
timer arrive in Phase 3+.

## Run locally

Requires Python 3.10+ (3.12 recommended).

```bash
python -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000. To test multiplayer solo, open a second window in
**Incognito** so it gets a separate player identity. Create a room, copy the
4-letter code into the other window, and the host can start.

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Flask session secret | dev placeholder |
| `CORS_ORIGINS` | Socket.IO allowed origins | `*` |
| `PORT` | Port to bind | 5000 |
| `FLASK_DEBUG` | Hot reload (`1` to enable) | 0 |

## Deployment

Stateful WebSocket app with in-memory rooms — run **exactly one worker**:

```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
```

`render.yaml` is included for one-click Render Blueprint deploys.

## Card images

Faces are generated SVGs, not a third-party pack. Regenerate any time with:

```bash
python tools/generate_cards.py    # writes static/img/cards/*.svg
```

## Tests

```bash
python test_rules.py            # pure rules engine (no server needed)
python test_phase2_engine.py    # room turn logic, deterministic (no server)
```

With the server running on `PORT=5005`:

```bash
python test_phase0.py           # lobby: create/join/start, reconnect, host migration
python test_phase1.py           # deal correctness, privacy, mid-round reconnect
python test_phase2_socket.py    # play/draw flow and rejections over the wire
```
