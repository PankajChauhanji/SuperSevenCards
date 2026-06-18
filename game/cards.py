"""Cards: model, deck construction, point values.

A card's point value equals its rank number directly (Ace=1, 2-10 face value,
Jack=11, Queen=12, King=13), which keeps scoring trivial. The `id` is a compact
rank+suit code (e.g. "7H", "AS", "10C", "KD") and doubles as the SVG image
filename: /static/img/cards/<id>.svg.
"""
import random
from typing import List

SUITS = ("S", "H", "D", "C")
RANKS = list(range(1, 14))          # 1=Ace ... 13=King
RED_SUITS = {"H", "D"}

_RANK_CODE = {1: "A", 11: "J", 12: "Q", 13: "K"}
for _n in range(2, 11):
    _RANK_CODE[_n] = str(_n)


def rank_code(rank: int) -> str:
    return _RANK_CODE[rank]


def card_value(rank: int) -> int:
    # Point value equals the rank number for every card in Super Seven.
    return rank


class Card:
    __slots__ = ("rank", "suit")

    def __init__(self, rank: int, suit: str):
        self.rank = rank
        self.suit = suit

    @property
    def id(self) -> str:
        return f"{rank_code(self.rank)}{self.suit}"

    @property
    def value(self) -> int:
        return card_value(self.rank)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "rank": self.rank,
            "suit": self.suit,
            "code": rank_code(self.rank),
            "value": self.value,
            "red": self.suit in RED_SUITS,
        }

    def __repr__(self) -> str:
        return f"Card({self.id})"


def build_deck() -> List[Card]:
    return [Card(rank, suit) for suit in SUITS for rank in RANKS]


def shuffled_deck() -> List[Card]:
    deck = build_deck()
    random.shuffle(deck)
    return deck
