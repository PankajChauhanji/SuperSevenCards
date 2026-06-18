"""Generate the card image set as SVG files.

Produces 52 faces (e.g. 7H.svg, AS.svg, 10C.svg, KD.svg) plus back.svg into
static/img/cards/. Faces are a clean minimal design: rank+suit in opposite
corners and a large central suit glyph. The back uses the table's pine/gold
palette so it sits naturally on the felt.

Run from the project root:  python tools/generate_cards.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "static", "img", "cards")

SUITS = {
    "S": ("\u2660", "#1c2b27"),  # ♠
    "H": ("\u2665", "#cf3b2e"),  # ♥
    "D": ("\u2666", "#cf3b2e"),  # ♦
    "C": ("\u2663", "#1c2b27"),  # ♣
}
RANKS = {1: "A", 11: "J", 12: "Q", 13: "K"}
for n in range(2, 11):
    RANKS[n] = str(n)

FACE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 252" width="180" height="252">
  <rect x="3" y="3" width="174" height="246" rx="16" fill="#fdfbf5" stroke="#d8cfb8" stroke-width="2"/>
  <g fill="{color}" font-family="Georgia, 'Times New Roman', serif" font-weight="700">
    <g>
      <text x="24" y="44" font-size="{rank_size}" text-anchor="middle">{rank}</text>
      <text x="24" y="72" font-size="24" text-anchor="middle">{suit}</text>
    </g>
    <g transform="rotate(180 90 126)">
      <text x="24" y="44" font-size="{rank_size}" text-anchor="middle">{rank}</text>
      <text x="24" y="72" font-size="24" text-anchor="middle">{suit}</text>
    </g>
    <text x="90" y="138" font-size="104" text-anchor="middle" dominant-baseline="central">{suit}</text>
  </g>
</svg>
"""

BACK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 252" width="180" height="252">
  <rect x="3" y="3" width="174" height="246" rx="16" fill="#173029" stroke="#0e201c" stroke-width="2"/>
  <rect x="14" y="14" width="152" height="224" rx="10" fill="none" stroke="#e6b23c" stroke-width="2" opacity="0.85"/>
  <g stroke="#e6b23c" stroke-width="1" opacity="0.18">
    {lattice}
  </g>
  <circle cx="90" cy="126" r="46" fill="#0e201c" opacity="0.55"/>
  <text x="90" y="126" font-size="74" font-family="'Space Grotesk', Georgia, serif" font-weight="700"
        fill="#e6b23c" text-anchor="middle" dominant-baseline="central">7</text>
  <g fill="#e6b23c" font-family="Georgia, serif" font-size="16" opacity="0.9" text-anchor="middle">
    <text x="90" y="58" dominant-baseline="central">\u2660 \u2665 \u2666 \u2663</text>
    <text x="90" y="196" dominant-baseline="central">\u2663 \u2666 \u2665 \u2660</text>
  </g>
</svg>
"""


def lattice_lines():
    lines = []
    for x in range(-180, 200, 22):
        lines.append(f'<line x1="{x}" y1="14" x2="{x + 224}" y2="238"/>')
        lines.append(f'<line x1="{x + 224}" y1="14" x2="{x}" y2="238"/>')
    return "\n    ".join(lines)


def main():
    os.makedirs(OUT, exist_ok=True)
    count = 0
    for suit, (glyph, color) in SUITS.items():
        for rank, label in RANKS.items():
            rank_size = 28 if len(label) > 1 else 34
            svg = FACE.format(color=color, rank=label, suit=glyph, rank_size=rank_size)
            with open(os.path.join(OUT, f"{label}{suit}.svg"), "w", encoding="utf-8") as f:
                f.write(svg)
            count += 1
    with open(os.path.join(OUT, "back.svg"), "w", encoding="utf-8") as f:
        f.write(BACK.format(lattice=lattice_lines()))
    print(f"Wrote {count} faces + back.svg to {os.path.normpath(OUT)}")


if __name__ == "__main__":
    main()
