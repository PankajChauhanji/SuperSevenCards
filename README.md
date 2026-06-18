# Super Seven

Real-time multiplayer card game (Flask-SocketIO + vanilla JS). Shed your hand,
call **Stop** when you think you're lowest, survive the elimination cap.

**Build status:** Phase 0 — Skeleton + Lobby. Create/join rooms, live roster,
host-only start, reconnection via stable client identity. The table (dealing,
drawing, discarding, scoring) lands in later phases.

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

## Tests

```bash
python test_phase0.py    # needs the server running on PORT=5005
```
