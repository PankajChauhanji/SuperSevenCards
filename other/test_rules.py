"""Exhaustive unit tests for game/rules.py — no server needed."""
from game.rules import (
    is_set, is_sequence, is_match, infer_action,
    ACTION_SINGLE, ACTION_SET, ACTION_SEQUENCE, ACTION_MATCH,
)

results = []
def check(ok, msg):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + msg)


# ---- is_set ----
check(is_set([8, 8, 8]), "three of a kind is a set")
check(is_set([13, 13, 13, 13]), "four of a kind is a set")
check(not is_set([8, 8]), "a pair is not a set (needs 3+)")
check(not is_set([8, 8, 8, 8, 8]), "five of a kind is not a set (max 4)")
check(not is_set([8, 8, 9]), "two-plus-one is not a set")

# ---- is_sequence ----
check(is_sequence([4, 5, 6]), "4-5-6 is a sequence")
check(is_sequence([10, 11, 12]), "10-J-Q is a sequence")
check(is_sequence([11, 12, 13]), "J-Q-K is a sequence")
check(is_sequence([1, 2, 3]), "A-2-3 is a sequence (Ace low)")
check(is_sequence([1, 2, 3, 4, 5]), "long runs are sequences")
check(not is_sequence([1, 12, 13]), "Q-K-A is NOT a sequence (no wrap)")
check(not is_sequence([4, 6, 7]), "gapped run is not a sequence")
check(not is_sequence([4, 5]), "two cards cannot be a sequence")
check(not is_sequence([5, 5, 6]), "duplicate rank breaks a sequence")
check(is_sequence([6, 4, 5]), "order does not matter (unsorted input)")

# ---- is_match ----
check(is_match([3], {2, 3, 4}), "single rank present in combo matches")
check(is_match([3, 3, 4], {2, 3, 4}), "multiples of present ranks match")
check(not is_match([5], {2, 3, 4}), "absent rank does not match")
check(not is_match([], {2, 3, 4}), "empty selection is not a match")

# ---- infer_action: basics ----
check(infer_action([7], False) == ACTION_SINGLE, "1 card -> single")
check(infer_action([7, 7, 7], False) == ACTION_SET, "3 same -> set")
check(infer_action([5, 6, 7], False) == ACTION_SEQUENCE, "run -> sequence")
check(infer_action([2, 3], False) is None, "random pair with no combo -> illegal")
check(infer_action([], False) is None, "empty -> illegal")

# ---- infer_action: match requires a previous combo ----
check(infer_action([3, 3], True, {2, 3, 4}) == ACTION_MATCH,
      "pair of present ranks after a combo -> match")
check(infer_action([3, 3], False, {2, 3, 4}) is None,
      "same pair with no previous combo -> illegal (no chaining off a single)")
check(infer_action([3, 4], True, {2, 3, 4}) == ACTION_MATCH,
      "two distinct present ranks -> match (not a sequence: only 2 cards)")
check(infer_action([8, 9], True, {2, 3, 4}) is None,
      "absent ranks after a combo -> illegal")

# ---- infer_action: PRIORITY (combo beats match) ----
# Three 3s when the previous combo was 2-3-4: qualifies as both set and match.
# Must resolve to SET (no draw), the player's preferred outcome.
check(infer_action([3, 3, 3], True, {2, 3, 4}) == ACTION_SET,
      "set takes priority over match (no-draw preferred)")
# 2-3-4 thrown again when prev combo was 2-3-4: both sequence and match -> sequence.
check(infer_action([2, 3, 4], True, {2, 3, 4}) == ACTION_SEQUENCE,
      "sequence takes priority over match")

print("\n%d/%d unit checks passed" % (sum(results), len(results)))
exit(0 if all(results) else 1)
