// Game page (Phase 0 = lobby). Attaches to the room, renders the roster, and
// lets the host start. The table itself arrives in Phase 1.
(function () {
  const { socket, showToast } = window.SS;

  const code = window.SS_ROOM_CODE;
  const youId = window.Identity.userId();

  let hostId = null;
  let state = "LOBBY";

  const codeEl = document.getElementById("room-code");
  const rosterEl = document.getElementById("roster");
  const metaEl = document.getElementById("lobby-meta");
  const startRow = document.getElementById("start-row");
  const lobbyView = document.getElementById("lobby-view");
  const placeholderView = document.getElementById("placeholder-view");

  codeEl.textContent = code;

  // Attach this socket to the room (also handles reconnect after refresh).
  function enter() {
    socket.emit("enter_room", { code, name: window.Identity.name(), user_id: youId });
  }
  socket.on("connect", enter);
  if (socket.connected) enter();

  socket.on("room_joined", (data) => {
    hostId = data.host_id;
    state = data.state;
    renderPlayers(data.players);
    syncView();
  });

  socket.on("player_list", (data) => {
    hostId = data.host_id;
    renderPlayers(data.players);
    syncView();
  });

  socket.on("game_started", () => {
    state = "IN_GAME";
    syncView();
  });

  function renderPlayers(players) {
    rosterEl.innerHTML = "";
    players.forEach((p) => {
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
      if (p.user_id === hostId) tags.appendChild(badge("Host", "host"));
      if (p.user_id === youId) tags.appendChild(badge("You", "you"));

      li.appendChild(who);
      li.appendChild(tags);
      rosterEl.appendChild(li);
    });

    const count = players.length;
    metaEl.textContent = count + (count === 1 ? " player" : " players") + " in the room";
  }

  function badge(text, kind) {
    const b = document.createElement("span");
    b.className = "badge " + kind;
    b.textContent = text;
    b.style.marginLeft = "0.4rem";
    return b;
  }

  function syncView() {
    const inGame = state !== "LOBBY";
    lobbyView.style.display = inGame ? "none" : "block";
    placeholderView.style.display = inGame ? "block" : "none";
    if (inGame) return;

    const isHost = youId === hostId;
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
      p.textContent = "Waiting for the host to start…";
      startRow.appendChild(p);
    }
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
