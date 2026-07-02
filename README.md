# 🃏 Super Seven

A fast-paced real-time multiplayer card game built with **Flask-SocketIO** and **vanilla JS**. Shed the points in your hand, call **Stop** when you think you're lowest, and survive the elimination cap.

---

### 🚀 Play it Live

[![Live Demo](https://img.shields.io/badge/PLAY_NOW-Live_on_Render-6706ce?style=for-the-badge&logo=render&logoColor=white)](https://super-seven.onrender.com)

> **💡 Feedback welcome!** If you find a bug or have a feature idea, open an **Issue** — the game is actively evolving.

---

## 📸 Gameplay Preview

| Welcome Lobby | Live Game Session |
| :---: | :---: |
| ![Game Lobby](static/img/game_images/super_seven_lobby.png) | ![Game Table](static/img/game_images/super_seven_game_table.png) |

---
## 🎮 How to Play

### Objective
Shed the points in your hand. When you think you have the lowest total, call **Stop**. Cross the score cap and you're eliminated. Last player standing wins.

### Card Values
| Card | Value |
|---|---|
| Ace | 1 |
| 2 – 10 | Face value |
| Jack | 11 |
| Queen | 12 |
| King | 13 |

### On Your Turn — Pick One

- **Discard** — throw one card, then draw one from the deck.
- **Set** — throw 3 or 4 cards of the same rank. No draw needed.
- **Sequence** — throw 3+ cards in a run (suits don't matter). No draw needed.
- **Match** — if the player before you threw a combo, throw any cards whose ranks appear in it. No draw needed (configurable in `config.py` via `MATCH_REQUIRES_DRAW`).

### Going to Zero
Empty your hand completely and your round score locks at **0** — you're safe and sit out the rest of the round.

### Calling Stop
- You can only call Stop at the **start of your turn**, and never during the **first orbit** (until everyone has played at least once).
- If you're **strictly the lowest** — you win the round and receive a score discount.
- If anyone **ties or beats you** — you take a heavy penalty on top of your hand total.

### Elimination
Once your cumulative score crosses the cap, you're out. The last player standing wins the game.

---

## ✨ Features

- **Real-time multiplayer** — WebSocket-powered with Flask-SocketIO, all actions sync instantly across all players
- **Complete game loop** — lobby, dealing, turn play, drawing, Stop with first-orbit gating, round scoring, and multi-round rotation
- **Smart turn engine** — supports single discard, set, sequence, and match plays with full server-side validation
- **Scoring system** — win discount for correct Stop calls, caught penalty for wrong ones, safe/trap rule enforcement
- **Automatic turn timer** — 40-second timer per turn with auto-play; a player is removed after three consecutive timeouts
- **Elimination & tiebreaker** — players eliminated at the score cap; survivor tiebreaker when multiple players hit it simultaneously
- **Reconnection support** — players rejoin seamlessly at any stage using stable client-generated identities
- **Host migration** — if the host disconnects, another player automatically takes over
- **Custom card faces** — all card SVGs are generated in-house, not a third-party pack

---

## 🏗️ Project Structure

```
super_seven_cards/
├── app.py                  # Flask + SocketIO entrypoint
├── config.py               # Environment variables and tunable constants
├── game/                   # Pure domain logic (networking-free)
│   ├── cards.py            # Card definitions and deck management
│   └── player.py           # Player profiles and identity tracking
├── sockets/                # WebSocket event handlers
│   ├── common.py           # Shared payload helpers
│   └── connection.py       # Connect / disconnect handling
├── static/
│   ├── css/style.css       # UI styles
│   ├── js/                 # Modular frontend (game, lobby, socket, table)
│   └── img/cards/          # Generated SVG card faces
├── templates/              # Jinja2 views (index + game)
├── tools/
│   └── generate_cards.py   # SVG card face generator
├── Procfile                # Gunicorn startup command
├── render.yaml             # Render Blueprint deployment spec
└── requirements.txt        # Python dependencies
```

---

## 🛠️ Quick Start (Local)

Requires Python 3.10+ (3.12 recommended).

```bash
# 1. Clone and enter the repo
git clone https://github.com/PankajChauhanji/SuperSevenCards.git
cd SuperSevenCards

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the server
python app.py
```

Open **http://localhost:5000**. To test multiplayer solo, open a second browser window in **Incognito** — it generates a separate player identity. Create a room, share the 4-letter code, and start.

---

## ⚙️ Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Flask session secret — override in production | `dev placeholder` |
| `CORS_ORIGINS` | Socket.IO allowed origins | `*` |
| `PORT` | Port to bind | `5000` |
| `FLASK_DEBUG` | Enable hot reload (`1` to enable) | `0` |

---

## 🌐 Deployment

Super Seven is a stateful WebSocket app with in-memory room state — always run **exactly one worker**:

```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
```

A `render.yaml` blueprint is included for one-click deploys on Render. Railway and Fly.io work equally well.

> ⚠️ **Never use multiple workers.** Room state lives in memory — multiple workers split players across isolated processes and break the game.

---

## 🃏 Regenerating Card SVGs

All card faces are custom generated SVGs — no third-party image packs. Regenerate any time:

```bash
python tools/generate_cards.py    # writes to static/img/cards/*.svg
```

---

## 🧩 Architecture

```
Browser (vanilla JS + Socket.IO client)
              ↕  WebSockets
Flask-SocketIO (single-process, eventlet)
              ↕
In-memory game engine (room / player / rules / scoring)
```

- **Domain layer** (`game/`) is completely decoupled from networking — pure Python logic, easy to unit test
- **Socket layer** (`sockets/`) handles all real-time events and delegates to the domain layer
- **Client identities** are stable and client-generated — survives page refreshes and reconnections mid-game

---

## 🔍 Troubleshooting

**Players end up in empty isolated rooms**
Your server is running more than one worker. Enforce `-w 1` in your Gunicorn command.

**Cold start delay on first load**
Render's free tier sleeps after 15 minutes of inactivity. The first visitor after a sleep window waits ~1 minute for the instance to wake up.

**Gunicorn version issues**
The project pins `gunicorn==23.0.0`. Versions 26+ removed bundled eventlet support and cause startup errors if upgraded blindly.

---

## 📄 License

Copyright (c) 2024 PankajChauhanji. All Rights Reserved.

Viewing of this source code is permitted for reference purposes only. Copying, modification, distribution, or use of this code in any form is strictly prohibited without explicit written permission from the author.