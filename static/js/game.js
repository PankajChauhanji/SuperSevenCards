// Game page controller. Holds the client's view of the room and routes server
// events to either the lobby or the table renderer. Actions (throw/draw/stop)
// arrive in later phases; Phase 1 deals and renders only.
(function () {
  const { socket, showToast } = window.SS;

  const code = window.SS_ROOM_CODE;
  const youId = window.Identity.userId();

  // Single source of truth for what this client is showing.
  const view = {
    you: youId,
    hostId: null,
    state: "LOBBY",
    players: [],
    currentTurn: null,
    turnOrder: [],
    deckCount: 0,
    center: [],
    hand: [],
    roundNumber: 0,
    awaitingDraw: false,
    lastWasCombo: false,
    firstOrbitComplete: false,
    secondsLeft: null,
    justDrawnId: null,
    settings: null,
  };
  window.SS.view = view; // selection.js reads this live reference

  let prevTurn = null;   // for the your-turn sound cue
  let drawnTimer = null; // clears the just-drawn highlight

  const lobbyView = document.getElementById("lobby-view");
  const tableView = document.getElementById("table-view");
  const codeEl = document.getElementById("room-code");
  const rosterEl = document.getElementById("roster");
  const metaEl = document.getElementById("lobby-meta");
  const startRow = document.getElementById("start-row");

  codeEl.textContent = code;

  // ---- attach / reconnect ----
  function enter() {
    socket.emit("enter_room", { code, name: window.Identity.name(), user_id: youId });
  }
  socket.on("connect", enter);
  if (socket.connected) enter();

  // ---- server events ----
  socket.on("room_joined", (data) => {
    view.hostId = data.host_id;
    view.state = data.state;
    view.players = data.players;
    if (data.settings) view.settings = data.settings;
    sync();
  });

  socket.on("player_list", (data) => {
    view.hostId = data.host_id;
    view.players = data.players;
    sync();
  });

  socket.on("room_reset", (data) => {
    view.state = "LOBBY";
    view.hostId = data.host_id;
    view.players = data.players;
    if (data.settings) view.settings = data.settings;
    view.hand = [];
    view.justDrawnId = null;
    view.secondsLeft = null;
    prevTurn = null;
    document.getElementById("roundend-modal").classList.remove("open");
    syncTimer();
    sync();
    showToast("New game — back to the lobby");
  });

  socket.on("round_start", (data) => {
    view.state = "IN_TURN";
    applyTable(data);
    document.getElementById("roundend-modal").classList.remove("open");
    if (window.Selection) window.Selection.reset();
    sync();
    syncTimer();
  });

  socket.on("table_state", (data) => {
    applyTable(data);
    if (view.state === "IN_TURN") {
      Table.render(view);
      if (window.Selection) window.Selection.refresh();
    }
    syncTimer();
  });

  function applyTable(data) {
    if (data.state) view.state = data.state;
    view.players = data.players;
    view.currentTurn = data.current_turn;
    view.turnOrder = data.turn_order;
    view.deckCount = data.deck_count;
    view.center = data.center;
    view.roundNumber = data.round_number;
    view.awaitingDraw = !!data.awaiting_draw;
    view.lastWasCombo = !!data.last_was_combo;
    view.firstOrbitComplete = !!data.first_orbit_complete;
    if (typeof data.turn_seconds_left === "number") view.secondsLeft = data.turn_seconds_left;

    // Sound cue when the turn becomes mine.
    if (view.state === "IN_TURN" && view.currentTurn === youId && prevTurn !== youId) {
      if (window.SS.sound) window.SS.sound.turnPing();
    }
    prevTurn = view.currentTurn;
  }

  socket.on("your_hand", (data) => {
    view.hand = data.cards || [];
    if (data.drawn) {
      view.justDrawnId = data.drawn;
      clearTimeout(drawnTimer);
      drawnTimer = setTimeout(() => {
        view.justDrawnId = null;
        if (view.state === "IN_TURN") Table.render(view);
      }, 5000);
    } else {
      view.justDrawnId = null;
    }
    if (window.Selection) window.Selection.reset();
    if (view.state === "IN_TURN") {
      Table.render(view);
    }
  });

  socket.on("cards_played", (data) => {
    if (data.by === youId) return; // your own action shows via your_hand
    const p = view.players.find((x) => x.user_id === data.by);
    const who = p ? p.name : "Someone";
    const verb = {
      single: "discarded a card",
      set: "played a set",
      sequence: "played a sequence",
      match: "matched the throw",
    }[data.action_type] || "played";
    showToast(who + " " + verb);
  });

  socket.on("deck_reshuffled", () => showToast("Deck reshuffled"));

  socket.on("player_timed_out", (data) => {
    if (data.removed) return; // an elimination toast follows
    showToast(data.name + " ran out of time");
  });

  socket.on("player_eliminated", (data) => {
    showToast(data.name + " is out of the game");
  });

  socket.on("round_end", (data) => {
    view.state = "ROUND_END";
    view.secondsLeft = null;
    if (data.players) view.players = data.players;
    if (tableView.style.display !== "none") Table.render(view);
    if (window.Selection) window.Selection.refresh();
    syncTimer();
    if (data.game_over) {
      showGameOver(data.winner, gameOverRows(data.results));
    } else {
      showRoundEnd(data);
    }
  });

  socket.on("game_end", (data) => {
    view.state = "GAME_END";
    view.secondsLeft = null;
    if (data.players) view.players = data.players;
    syncTimer();
    showGameOver(data.winner, data.standings);
  });

  // ---- turn timer countdown ----
  function syncTimer() {
    const el = document.getElementById("turn-timer");
    if (view.state !== "IN_TURN" || view.secondsLeft == null) {
      el.style.display = "none";
      return;
    }
    el.style.display = "inline-block";
    el.textContent = "\u23f1 " + Math.max(0, view.secondsLeft) + "s";
    el.classList.toggle("low", view.secondsLeft <= 10);
  }
  setInterval(() => {
    if (view.state === "IN_TURN" && typeof view.secondsLeft === "number" && view.secondsLeft > 0) {
      view.secondsLeft -= 1;
      syncTimer();
    }
  }, 1000);

  // ---- view switching ----
  function sync() {
    const inRound = view.state === "IN_TURN";
    lobbyView.style.display = inRound ? "none" : "block";
    tableView.style.display = inRound ? "flex" : "none";
    if (inRound) {
      Table.render(view);
    } else {
      renderLobby();
    }
  }

  // ---- lobby rendering ----
  const LOBBY_PALETTE = ["#4ea1ff", "#ff9f43", "#a98cf0", "#f06ea9", "#43c6c6", "#d6c04a"];

  function renderLobby() {
    rosterEl.innerHTML = "";
    view.players.forEach((p) => {
      const li = document.createElement("li");
      const who = document.createElement("div");
      who.className = "who";
      const sw = document.createElement("span");
      sw.className = "swatch";
      sw.style.background = LOBBY_PALETTE[(p.color || 0) % LOBBY_PALETTE.length];
      const dot = document.createElement("span");
      dot.className = "dot" + (p.connected ? " on" : "");
      const name = document.createElement("span");
      name.className = "name";
      name.textContent = p.name;
      who.appendChild(sw);
      who.appendChild(dot);
      who.appendChild(name);

      const tags = document.createElement("div");
      if (p.user_id === view.hostId) tags.appendChild(makeBadge("Host", "host"));
      if (p.user_id === youId) tags.appendChild(makeBadge("You", "you"));

      li.appendChild(who);
      li.appendChild(tags);
      rosterEl.appendChild(li);
    });

    renderLobbySettings();

    const n = view.players.length;
    metaEl.textContent = n + (n === 1 ? " player" : " players") + " in the room";

    const isHost = youId === view.hostId;
    startRow.innerHTML = "";
    if (isHost) {
      const btn = document.createElement("button");
      btn.className = "btn-primary";
      btn.textContent = "Start game";
      btn.addEventListener("click", () => {
        socket.emit("start_game", { code, user_id: youId });
      });
      startRow.appendChild(btn);
    } else {
      const p = document.createElement("p");
      p.className = "waiting";
      p.textContent = "Waiting for the host to start\u2026";
      startRow.appendChild(p);
    }
  }

  function renderLobbySettings() {
    const el = document.getElementById("lobby-settings");
    if (!el) return;
    const s = view.settings;
    if (!s) { el.innerHTML = ""; return; }
    const items = [
      ["Out at", s.max_score + " pts"],
      ["Stop penalty", "+" + s.stop_penalty],
      ["Win discount", "\u2212" + s.win_discount],
      ["Turn timer", s.turn_timer + "s"],
      ["Timeouts", s.timeout_limit],
    ];
    el.innerHTML = "<h3>Game settings</h3>";
    const grid = document.createElement("div");
    grid.className = "settings-readout";
    items.forEach(([k, v]) => {
      const row = document.createElement("div");
      row.className = "sr-item";
      row.innerHTML = "<span>" + k + "</span><strong>" + v + "</strong>";
      grid.appendChild(row);
    });
    el.appendChild(grid);
  }

  function makeBadge(text, kind) {
    const b = document.createElement("span");
    b.className = "badge " + kind;
    b.textContent = text;
    b.style.marginLeft = "0.4rem";
    return b;
  }

  // ---- round-end reveal ----
  function showRoundEnd(data) {
    const modal = document.getElementById("roundend-modal");
    const title = document.getElementById("roundend-title");
    const sub = document.getElementById("roundend-sub");
    const body = document.getElementById("roundend-body");

    const byId = {};
    view.players.forEach((p) => (byId[p.user_id] = p));
    const callerName = data.caller ? (byId[data.caller] || {}).name || "Someone" : null;

    if (!data.caller) {
      title.textContent = "Round over";
      sub.textContent = "Everyone emptied their hand.";
    } else if (data.caught) {
      title.textContent = callerName + " got caught";
      sub.textContent = "Someone matched or beat the call — penalty applied.";
    } else {
      title.textContent = callerName + " called it";
      sub.textContent = "Lowest at the table — the call paid off.";
    }

    // Lowest round score first.
    const rows = data.results.slice().sort((a, b) => a.round_score - b.round_score);
    body.innerHTML = "";
    rows.forEach((r) => {
      const row = document.createElement("div");
      row.className = "re-row";
      if (r.user_id === data.caller) row.classList.add("caller");

      const head = document.createElement("div");
      head.className = "re-head";
      const name = document.createElement("span");
      name.className = "re-name";
      name.textContent = r.name;
      if (r.user_id === data.caller) name.appendChild(makeBadge("Caller", "host"));
      if (r.is_safe) name.appendChild(makeBadge("Safe", "safe"));
      const score = document.createElement("span");
      score.className = "re-score";
      score.textContent = "+" + r.round_score + "  \u2192  " + r.total_score;
      head.appendChild(name);
      head.appendChild(score);

      const cards = document.createElement("div");
      cards.className = "re-cards";
      if (r.hand.length === 0) {
        const none = document.createElement("span");
        none.className = "re-empty";
        none.textContent = "empty hand";
        cards.appendChild(none);
      } else {
        r.hand.forEach((c) => {
          const img = document.createElement("img");
          img.className = "card re-card";
          img.src = "/static/img/cards/" + c.id + ".svg";
          img.alt = c.code + c.suit;
          cards.appendChild(img);
        });
        const tot = document.createElement("span");
        tot.className = "re-total";
        tot.textContent = r.hand_total + " pts";
        cards.appendChild(tot);
      }

      row.appendChild(head);
      row.appendChild(cards);
      body.appendChild(row);
    });

    // Footer: host advances the game; others wait.
    const footer = document.getElementById("roundend-footer");
    footer.innerHTML = "";
    if (youId === view.hostId) {
      const btn = document.createElement("button");
      btn.className = "btn-primary";
      btn.textContent = "Next round";
      btn.addEventListener("click", () => {
        btn.disabled = true;
        socket.emit("next_round", { code, user_id: youId });
      });
      footer.appendChild(btn);
    } else {
      const wait = document.createElement("p");
      wait.className = "waiting";
      wait.style.margin = "0";
      wait.textContent = "Waiting for the host to deal the next round\u2026";
      footer.appendChild(wait);
    }

    modal.classList.add("open");
  }

  // Build standings rows from a round_end results array (for a game-over reveal).
  function gameOverRows(resultRows) {
    return resultRows
      .map((r) => ({
        user_id: r.user_id, name: r.name,
        total_score: r.total_score, eliminated: r.eliminated,
      }))
      .sort((a, b) => (a.eliminated - b.eliminated) || (a.total_score - b.total_score));
  }

  function showGameOver(winnerId, rows) {
    const modal = document.getElementById("roundend-modal");
    const title = document.getElementById("roundend-title");
    const sub = document.getElementById("roundend-sub");
    const body = document.getElementById("roundend-body");

    const winnerName = (rows.find((r) => r.user_id === winnerId) || {}).name || "Nobody";
    title.textContent = winnerName + " wins!";
    sub.textContent = winnerId === youId
      ? "You're the last one standing."
      : "Last player standing takes the game.";

    body.innerHTML = "";
    rows.forEach((r, i) => {
      const row = document.createElement("div");
      row.className = "re-row";
      if (r.user_id === winnerId) row.classList.add("caller");
      if (r.eliminated) row.classList.add("out");

      const head = document.createElement("div");
      head.className = "re-head";
      const name = document.createElement("span");
      name.className = "re-name";
      name.textContent = (i + 1) + ". " + r.name;
      if (r.user_id === winnerId) name.appendChild(makeBadge("Winner", "host"));
      if (r.eliminated) name.appendChild(makeBadge("Out", "you"));
      const score = document.createElement("span");
      score.className = "re-score";
      score.textContent = r.total_score + " pts";
      head.appendChild(name);
      head.appendChild(score);
      row.appendChild(head);
      body.appendChild(row);
    });

    const footer = document.getElementById("roundend-footer");
    footer.innerHTML = "";

    if (youId === view.hostId) {
      const again = document.createElement("button");
      again.className = "btn-primary";
      again.textContent = "Play again";
      again.addEventListener("click", () => {
        again.disabled = true;
        socket.emit("rematch", { code, user_id: youId });
      });
      footer.appendChild(again);
    } else {
      const wait = document.createElement("span");
      wait.className = "waiting";
      wait.style.marginRight = "auto";
      wait.textContent = "Waiting for the host to start a rematch\u2026";
      footer.appendChild(wait);
    }

    const home = document.createElement("button");
    home.className = "btn-ghost";
    home.style.width = "auto";
    home.textContent = "Back to home";
    home.addEventListener("click", () => { window.location.href = "/"; });
    footer.appendChild(home);

    modal.classList.add("open");
  }

  // ---- selection / actions ----
  if (window.Selection) {
    window.Selection.init({ socket, code, you: youId });
  }

  // ---- rules modal ----
  const modal = document.getElementById("rules-modal");
  document.getElementById("rules-btn").addEventListener("click", () => modal.classList.add("open"));
  document.getElementById("rules-close").addEventListener("click", () => modal.classList.remove("open"));
  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.remove("open");
  });

  // ---- mute toggle ----
  const muteBtn = document.getElementById("mute-btn");
  if (muteBtn && window.SS.sound) {
    const paint = () => { muteBtn.textContent = window.SS.sound.muted() ? "\uD83D\uDD07" : "\uD83D\uDD0A"; };
    paint();
    muteBtn.addEventListener("click", () => {
      window.SS.sound.toggleMute();
      paint();
    });
  }

  // ---- copy code ----
  const copyBtn = document.getElementById("copy-btn");
  if (copyBtn) {
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(code);
        showToast("Room code copied.");
      } catch (_) {
        showToast("Code: " + code);
      }
    });
  }
})();
