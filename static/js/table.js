// Table renderer. Pure view layer: given the current state it paints the
// scoreboard, opponent seats (counts only), the deck/center piles, and the
// player's own face-up hand. No game actions live here (those arrive Phase 2).
(function () {
  const CARD_PATH = "/static/img/cards/";

  function cardImg(card, className) {
    const img = document.createElement("img");
    img.className = "card " + (className || "");
    img.src = CARD_PATH + card.id + ".svg";
    img.alt = card.code + " " + card.suit;
    img.draggable = false;
    return img;
  }

  function backImg(className) {
    const img = document.createElement("img");
    img.className = "card " + (className || "");
    img.src = CARD_PATH + "back.svg";
    img.alt = "card";
    img.draggable = false;
    return img;
  }

  function badge(text, kind) {
    const b = document.createElement("span");
    b.className = "badge " + (kind || "");
    b.textContent = text;
    return b;
  }

  function renderScoreboard(state) {
    const list = document.getElementById("score-list");
    list.innerHTML = "";
    state.players.forEach((p) => {
      const li = document.createElement("li");
      if (p.user_id === state.currentTurn) li.classList.add("turn");
      if (p.eliminated) li.classList.add("out");

      const left = document.createElement("span");
      left.className = "sb-name";
      const dot = document.createElement("span");
      dot.className = "dot" + (p.connected ? " on" : "");
      left.appendChild(dot);
      left.appendChild(document.createTextNode(p.name));
      if (p.user_id === state.you) left.appendChild(badge("You", "you"));
      if (p.user_id === state.hostId) left.appendChild(badge("Host", "host"));

      const score = document.createElement("span");
      score.className = "sb-score";
      score.textContent = p.score;

      li.appendChild(left);
      li.appendChild(score);
      list.appendChild(li);
    });
  }

  function renderOpponents(state) {
    const wrap = document.getElementById("opponents");
    wrap.innerHTML = "";

    // Opponents in seating order, starting after "you" for a stable layout.
    const order = state.turnOrder && state.turnOrder.length
      ? state.turnOrder
      : state.players.map((p) => p.user_id);
    const byId = {};
    state.players.forEach((p) => (byId[p.user_id] = p));

    order
      .filter((uid) => uid !== state.you && byId[uid])
      .forEach((uid) => {
        const p = byId[uid];
        const seat = document.createElement("div");
        seat.className = "seat";
        if (p.user_id === state.currentTurn) seat.classList.add("active");
        if (!p.connected) seat.classList.add("offline");
        if (p.eliminated) seat.classList.add("out");

        const stack = document.createElement("div");
        stack.className = "mini-stack";
        if (p.is_safe) {
          stack.appendChild(badge("SAFE 0", "safe"));
        } else {
          stack.appendChild(backImg("mini"));
          const count = document.createElement("span");
          count.className = "count";
          count.textContent = "\u00d7" + p.card_count; // ×N
          stack.appendChild(count);
        }

        const meta = document.createElement("div");
        meta.className = "seat-meta";
        const name = document.createElement("span");
        name.className = "seat-name";
        name.textContent = p.name;
        const score = document.createElement("span");
        score.className = "seat-score";
        score.textContent = p.score + " pts";
        meta.appendChild(name);
        meta.appendChild(score);

        seat.appendChild(stack);
        seat.appendChild(meta);
        wrap.appendChild(seat);
      });
  }

  function renderCenter(state) {
    document.getElementById("deck-count").textContent = state.deckCount;

    const deck = document.getElementById("deck");
    const myDraw = state.you === state.currentTurn && state.awaitingDraw;
    deck.classList.toggle("clickable", !!myDraw);

    const discard = document.getElementById("discard");
    const empty = document.getElementById("discard-empty");
    // Clear previously rendered center cards (keep label + empty marker).
    discard.querySelectorAll(".card").forEach((el) => el.remove());

    const center = state.center || [];
    empty.style.display = center.length ? "none" : "block";
    center.forEach((card, i) => {
      const img = cardImg(card, "center-card");
      img.style.marginLeft = i === 0 ? "0" : "-34px";
      discard.appendChild(img);
    });
  }

  function renderMySeat(state) {
    const seat = document.getElementById("myseat");
    seat.className = "myseat";
    if (state.you === state.currentTurn) seat.classList.add("active");
    seat.innerHTML = "";

    const me = state.players.find((p) => p.user_id === state.you);
    const name = document.createElement("span");
    name.className = "seat-name";
    name.textContent = (me ? me.name : "You") + " (you)";
    const tag = document.createElement("span");
    tag.className = "turn-tag";
    tag.textContent = state.you === state.currentTurn ? "Your turn" : "Waiting";
    seat.appendChild(name);
    seat.appendChild(tag);
  }

  // Stable display order for a hand: by rank, then by suit.
  const SUIT_ORDER = { S: 0, H: 1, D: 2, C: 3 };
  function sortedHand(cards) {
    return (cards || []).slice().sort((a, b) => {
      if (a.rank !== b.rank) return a.rank - b.rank;
      return (SUIT_ORDER[a.suit] || 0) - (SUIT_ORDER[b.suit] || 0);
    });
  }

  function renderHand(state) {
    const hand = document.getElementById("hand");
    hand.innerHTML = "";
    sortedHand(state.hand).forEach((card) => {
      const slot = document.createElement("div");
      slot.className = "card-slot";
      slot.dataset.id = card.id;
      slot.appendChild(cardImg(card, "hand-card"));
      const tick = document.createElement("span");
      tick.className = "tick";
      tick.textContent = "\u2713";
      slot.appendChild(tick);
      hand.appendChild(slot);
    });
    if (window.Selection) window.Selection.refresh();
  }

  window.Table = {
    render(state) {
      document.getElementById("round-chip").style.display = "inline-block";
      document.getElementById("round-chip").textContent = "Round " + (state.roundNumber || 1);
      renderScoreboard(state);
      renderOpponents(state);
      renderCenter(state);
      renderMySeat(state);
      renderHand(state);
    },
  };
})();
