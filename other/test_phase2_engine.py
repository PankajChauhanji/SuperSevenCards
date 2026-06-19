"""Deterministic Phase 2 engine tests, driving Room directly (no sockets)."""
from game.room import Room, STATE_IN_TURN
from game.cards import Card
from game.rules import infer_action, ACTION_SET, ACTION_SEQUENCE, ACTION_MATCH, ACTION_SINGLE

results = []
def check(ok, msg):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + msg)


def make_room(p1_hand, p2_hand, draw_pile=None, center=None, last_combo=False):
    r = Room("TEST", "P1", {})
    r.register_player("P1", "P1")
    r.register_player("P2", "P2")
    r.players["P1"].connected = True
    r.players["P2"].connected = True
    r.players["P1"].hand = list(p1_hand)
    r.players["P2"].hand = list(p2_hand)
    r.draw_pile = list(draw_pile or [])
    r.discard_pile = []
    r.center_throw = list(center or [])
    r.last_was_combo = last_combo
    r.turn_order = ["P1", "P2"]
    r.turn_index = 0
    r.awaiting_draw = False
    r.state = STATE_IN_TURN
    return r


def throw(room, uid, ids):
    cards = room.card_objects(uid, ids)
    assert cards is not None, "card_objects returned None for %s" % ids
    action = infer_action([c.rank for c in cards], room.last_was_combo, room.center_rank_set())
    owes = room.apply_throw(uid, cards, action)
    return action, owes


# ---- single discard then draw ----
r = make_room([Card(9, "C"), Card(2, "H")], [Card(7, "S")], draw_pile=[Card(13, "S")])
action, owes = throw(r, "P1", ["9C"])
check(action == ACTION_SINGLE and owes, "single discard owes a draw")
check(r.awaiting_draw and r.current_turn_id() == "P1", "turn stays on P1 until draw")
check("9C" not in {c.id for c in r.players["P1"].hand}, "thrown card left the hand")
r.draw_one("P1")
check(not r.awaiting_draw and r.current_turn_id() == "P2", "draw clears owe and passes turn")
check(len(r.players["P1"].hand) == 2, "P1 drew back up to 2 cards")

# ---- set: no draw, immediate pass ----
r = make_room([Card(5, "H"), Card(5, "S"), Card(5, "D"), Card(1, "C")], [Card(7, "S")])
action, owes = throw(r, "P1", ["5H", "5S", "5D"])
check(action == ACTION_SET and not owes, "set draws nothing")
check(r.current_turn_id() == "P2", "set passes the turn immediately")
check(r.last_was_combo and r.center_rank_set() == {5}, "set leaves a matchable combo")

# ---- sequence ----
r = make_room([Card(4, "H"), Card(5, "S"), Card(6, "D"), Card(1, "C")], [Card(7, "S")])
action, owes = throw(r, "P1", ["4H", "5S", "6D"])
check(action == ACTION_SEQUENCE and not owes, "sequence draws nothing")
check(r.last_was_combo and r.center_rank_set() == {4, 5, 6}, "sequence is matchable")

# ---- match: after a combo, throw matching ranks; no chaining ----
r = make_room([Card(9, "C")], [Card(3, "S"), Card(3, "D")],
              center=[Card(2, "H"), Card(3, "H"), Card(4, "H")], last_combo=True)
r.turn_index = 1  # P2 to act
action, owes = throw(r, "P2", ["3S", "3D"])
check(action == ACTION_MATCH and owes, "match throws matching ranks and owes a draw")
check(not r.last_was_combo, "a match does NOT leave a matchable combo (no chaining)")
check({c.id for c in r.center_throw} == {"3S", "3D"}, "center now shows the matched cards")

# ---- priority: set beats match ----
r = make_room([Card(3, "H"), Card(3, "S"), Card(3, "D")], [Card(7, "S")],
              center=[Card(2, "H"), Card(3, "C"), Card(4, "H")], last_combo=True)
action, owes = throw(r, "P1", ["3H", "3S", "3D"])
check(action == ACTION_SET and not owes, "three-of-a-kind resolves to set, not match (no draw)")

# ---- reshuffle when draw pile empties ----
r = make_room([Card(9, "C")], [Card(7, "S")], draw_pile=[], center=[])
r.discard_pile = [Card(13, "S"), Card(11, "D")]
r.awaiting_draw = True  # pretend a single was just played
before = len(r.players["P1"].hand)
reshuffled = r.draw_one("P1")
check(reshuffled, "empty draw pile triggers a reshuffle from discards")
check(len(r.players["P1"].hand) == before + 1, "player still draws a card after reshuffle")

# ---- safe: emptying the hand with a combo ----
r = make_room([Card(5, "H"), Card(5, "S"), Card(5, "D")], [Card(7, "S")])
throw(r, "P1", ["5H", "5S", "5D"])
check(r.players["P1"].is_safe, "emptying the hand via a combo marks the player safe")
check(r.current_turn_id() == "P2", "turn passes off the now-safe player")

# ---- illegal selections ----
r = make_room([Card(9, "C"), Card(2, "H")], [Card(7, "S")])
check(r.card_objects("P1", ["KS"]) is None, "selecting a card not in hand is rejected")
check(r.card_objects("P1", ["9C", "9C"]) is None, "duplicate ids are rejected")
check(infer_action([9, 2], False, set()) is None, "a random pair is not a legal play")

print("\n%d/%d engine checks passed" % (sum(results), len(results)))
exit(0 if all(results) else 1)
