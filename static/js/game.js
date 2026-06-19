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
  };
  window.SS.view = view; // selection.js reads this live reference

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
    sync();
  });

  socket.on("player_list", (data) => {
    view.hostId = data.host_id;
    view.players = data.players;
    sync();
  });

  socket.on("round_start", (data) => {
    view.state = "IN_TURN";
    applyTable(data);
    if (window.Selection) window.Selection.reset();
    sync();
  });

  socket.on("table_state", (data) => {
    applyTable(data);
    if (view.state === "IN_TURN") {
      Table.render(view);
      if (window.Selection) window.Selection.refresh();
    }
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
  }

  socket.on("your_hand", (data) => {
    view.hand = data.cards || [];
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

  socket.on("round_end", (data) => {
    view.state = "ROUND_END";
    if (data.players) view.players = data.players;
    // Keep the table visible underneath; refresh scoreboard totals.
    if (tableView.style.display !== "none") Table.render(view);
    if (window.Selection) window.Selection.refresh();
    showRoundEnd(data);
  });

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
  function renderLobby() {
    rosterEl.innerHTML = "";
    view.players.forEach((p) => {
      const li = document.createElement("li");
      const who = document.createElement("div");
      who.className = "who";
      const dot = document.createElement("span");
      dot.className = "dot" + (p.connected ? " on" : "");
      const name = document.createElement("span");
      name.className = "name";
      name.textContent = p.name;
      who.appendChild(dot);
      who.appendChild(name);

      const tags = document.createElement("div");
      if (p.user_id === view.hostId) tags.appendChild(makeBadge("Host", "host"));
      if (p.user_id === youId) tags.appendChild(makeBadge("You", "you"));

      li.appendChild(who);
      li.appendChild(tags);
      rosterEl.appendChild(li);
    });

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

  // ---- round-end modal ----
  const reModal = document.getElementById("roundend-modal");
  document.getElementById("roundend-close").addEventListener("click", () => reModal.classList.remove("open"));

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
