# Super Seven

Real-time multiplayer card game (Flask-SocketIO + vanilla JS). Shed your hand,
call **Stop** when you think you're lowest, survive the elimination cap.

**Build status:** Phase 3 — Endgame. Calling Stop (only at the clean start of
your turn, and never during the first orbit), the round-end reveal of every
hand, and full scoring: a strictly-lowest caller scores `max(total - 5, 0)`, a
caught caller takes `hand + 40`, others score their hand, and a safe (0-card)
player scores 0 — so once anyone is safe, Stop is a guaranteed penalty. Totals
accumulate across the round. The multi-round elimination loop and the turn
timer arrive in Phase 4.

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
python test_scoring.py          # round scoring: win / caught / trap (no server)
python test_phase2_engine.py    # room turn logic, deterministic (no server)
python test_phase3_engine.py    # first-orbit gating + round-end (no server)
```

With the server running on `PORT=5005`:

```bash
python test_phase0.py           # lobby: create/join/start, reconnect, host migration
python test_phase1.py           # deal correctness, privacy, mid-round reconnect
python test_phase2_socket.py    # play/draw flow and rejections over the wire
python test_phase3_socket.py    # Stop gating and round-end reveal over the wire
```
