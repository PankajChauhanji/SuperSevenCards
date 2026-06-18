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
  };

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
    view.players = data.players;
    view.currentTurn = data.current_turn;
    view.turnOrder = data.turn_order;
    view.deckCount = data.deck_count;
    view.center = data.center;
    view.roundNumber = data.round_number;
    sync();
  });

  socket.on("your_hand", (data) => {
    view.hand = data.cards || [];
    if (view.state === "IN_TURN") Table.render(view);
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

  // ---- rules modal ----
  const modal = document.getElementById("rules-modal");
  document.getElementById("rules-btn").addEventListener("click", () => modal.classList.add("open"));
  document.getElementById("rules-close").addEventListener("click", () => modal.classList.remove("open"));
  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.remove("open");
  });

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
