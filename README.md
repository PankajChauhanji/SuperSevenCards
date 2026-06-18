# Super Seven

Real-time multiplayer card game (Flask-SocketIO + vanilla JS). Shed your hand,
call **Stop** when you think you're lowest, survive the elimination cap.

**Build status:** Phase 1 — Deal & Render. Rooms/lobby plus a dealt round:
each player sees their own hand face-up, opponents as face-down counts, the
deck and (empty) center, and a green boundary on the active player. Card faces
are generated SVGs (see `tools/generate_cards.py`). Turn actions — throwing,
drawing, Stop — arrive in Phase 2+.

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

With the server running on `PORT=5005`:

```bash
python test_phase0.py    # lobby: create/join/start, reconnect, host migration
python test_phase1.py    # deal correctness, privacy, mid-round reconnect
```
