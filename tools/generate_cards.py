"""Generate the card image set as SVG files.

Produces 52 faces (e.g. 7H.svg, AS.svg, 10C.svg, KD.svg) plus back.svg into
static/img/cards/. Faces are a clean minimal design: rank+suit in opposite
corners and a large central suit glyph (or custom illustrations for face cards J, Q, K and Ace).
The back uses the table's pine/gold palette so it sits naturally on the felt.

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

FACE_A = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 252" width="180" height="252">
  <rect x="3" y="3" width="174" height="246" rx="16" fill="#fdfbf5" stroke="#d8cfb8" stroke-width="2"/>
  <g fill="{color}" font-family="Georgia, 'Times New Roman', serif" font-weight="700">
    <g>
      <text x="24" y="44" font-size="34" text-anchor="middle">A</text>
      <text x="24" y="72" font-size="24" text-anchor="middle">{suit}</text>
    </g>
    <g transform="rotate(180 90 126)">
      <text x="24" y="44" font-size="34" text-anchor="middle">A</text>
      <text x="24" y="72" font-size="24" text-anchor="middle">{suit}</text>
    </g>
  </g>
  <!-- Grand Ornate Ace Design -->
  <g stroke="{color}" fill="none">
    <circle cx="90" cy="138" r="60" stroke-width="1.5" stroke-dasharray="3 3" opacity="0.65"/>
    <circle cx="90" cy="138" r="52" stroke-width="1.0" opacity="0.4"/>
    <path d="M 90,68 L 92,74 L 98,76 L 92,78 L 90,84 L 88,78 L 82,76 L 88,74 Z" fill="{color}" stroke="none"/>
    <path d="M 90,192 L 92,198 L 98,200 L 92,202 L 90,208 L 88,202 L 82,200 L 88,198 Z" fill="{color}" stroke="none"/>
    <path d="M 32,138 L 38,136 L 40,130 L 42,136 L 48,138 L 42,140 L 40,146 L 38,140 Z" fill="{color}" stroke="none"/>
    <path d="M 132,138 L 138,136 L 140,130 L 142,136 L 148,138 L 142,140 L 140,146 L 138,140 Z" fill="{color}" stroke="none"/>
  </g>
  <g fill="{color}" font-family="Georgia, 'Times New Roman', serif" font-weight="700">
    <text x="90" y="138" font-size="94" text-anchor="middle" dominant-baseline="central">{suit}</text>
  </g>
</svg>
"""

FACE_J = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 252" width="180" height="252">
  <rect x="3" y="3" width="174" height="246" rx="16" fill="#fdfbf5" stroke="#d8cfb8" stroke-width="2"/>
  <!-- Corners -->
  <g fill="{color}" font-family="Georgia, 'Times New Roman', serif" font-weight="700">
    <g>
      <text x="24" y="44" font-size="28" text-anchor="middle">J</text>
      <text x="24" y="72" font-size="24" text-anchor="middle">{suit}</text>
    </g>
    <g transform="rotate(180 90 126)">
      <text x="24" y="44" font-size="28" text-anchor="middle">J</text>
      <text x="24" y="72" font-size="24" text-anchor="middle">{suit}</text>
    </g>
  </g>
  <!-- Portrait Frame -->
  <rect x="42" y="42" width="96" height="168" rx="8" fill="none" stroke="{color}" stroke-width="1.5" stroke-dasharray="4 4" opacity="0.5"/>
  <!-- Jack Portrait -->
  <g transform="translate(90, 126)">
    <!-- Top Half -->
    <g>
      <!-- Cap -->
      <path d="M -16,-28 C -16,-46 16,-46 16,-28 Z" fill="{color}"/>
      <path d="M 0,-40 Q 12,-50 20,-43 Q 12,-36 0,-40" fill="{color}"/>
      <!-- Face -->
      <path d="M -14,-28 L 14,-28 L 14,-6 Q 14,8 0,8 Q -14,8 -14,-6 Z" fill="#fdfbf5" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>
      <!-- Eyes & Face details -->
      <circle cx="-5" cy="-12" r="1.5" fill="{color}"/>
      <circle cx="5" cy="-12" r="1.5" fill="{color}"/>
      <path d="M 0,-14 L 0,-9 L 2,-9" stroke="{color}" stroke-width="2" fill="none"/>
      <line x1="-4" y1="-2" x2="4" y2="-2" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
      <!-- Shoulders/Collar -->
      <path d="M -28,35 L -18,8 Q 0,14 18,8 L 28,35 Z" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>
      <path d="M -14,8 L -6,22 L 0,8 L 6,22 L 14,8" stroke="{color}" stroke-width="2" fill="none"/>
      <!-- Halberd/Spear -->
      <line x1="-22" y1="-20" x2="-22" y2="35" stroke="{color}" stroke-width="2"/>
      <path d="M -26,-20 L -22,-30 L -18,-20 Z" fill="{color}"/>
    </g>
    <!-- Bottom Half -->
    <g transform="rotate(180)">
      <!-- Cap -->
      <path d="M -16,-28 C -16,-46 16,-46 16,-28 Z" fill="{color}"/>
      <path d="M 0,-40 Q 12,-50 20,-43 Q 12,-36 0,-40" fill="{color}"/>
      <!-- Face -->
      <path d="M -14,-28 L 14,-28 L 14,-6 Q 14,8 0,8 Q -14,8 -14,-6 Z" fill="#fdfbf5" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>
      <!-- Eyes & Face details -->
      <circle cx="-5" cy="-12" r="1.5" fill="{color}"/>
      <circle cx="5" cy="-12" r="1.5" fill="{color}"/>
      <path d="M 0,-14 L 0,-9 L 2,-9" stroke="{color}" stroke-width="2" fill="none"/>
      <line x1="-4" y1="-2" x2="4" y2="-2" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
      <!-- Shoulders/Collar -->
      <path d="M -28,35 L -18,8 Q 0,14 18,8 L 28,35 Z" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>
      <path d="M -14,8 L -6,22 L 0,8 L 6,22 L 14,8" stroke="{color}" stroke-width="2" fill="none"/>
      <!-- Halberd/Spear -->
      <line x1="-22" y1="-20" x2="-22" y2="35" stroke="{color}" stroke-width="2"/>
      <path d="M -26,-20 L -22,-30 L -18,-20 Z" fill="{color}"/>
    </g>
  </g>
</svg>
"""

FACE_Q = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 252" width="180" height="252">
  <rect x="3" y="3" width="174" height="246" rx="16" fill="#fdfbf5" stroke="#d8cfb8" stroke-width="2"/>
  <!-- Corners -->
  <g fill="{color}" font-family="Georgia, 'Times New Roman', serif" font-weight="700">
    <g>
      <text x="24" y="44" font-size="28" text-anchor="middle">Q</text>
      <text x="24" y="72" font-size="24" text-anchor="middle">{suit}</text>
    </g>
    <g transform="rotate(180 90 126)">
      <text x="24" y="44" font-size="28" text-anchor="middle">Q</text>
      <text x="24" y="72" font-size="24" text-anchor="middle">{suit}</text>
    </g>
  </g>
  <!-- Portrait Frame -->
  <rect x="42" y="42" width="96" height="168" rx="8" fill="none" stroke="{color}" stroke-width="1.5" stroke-dasharray="4 4" opacity="0.5"/>
  <!-- Queen Portrait -->
  <g transform="translate(90, 126)">
    <!-- Top Half -->
    <g>
      <!-- Crown -->
      <path d="M -16,-28 L -16,-40 L -8,-32 L 0,-48 L 8,-32 L 16,-40 L 16,-28 Z" fill="{color}"/>
      <line x1="-12" y1="-28" x2="12" y2="-28" stroke="#fdfbf5" stroke-width="2"/>
      <circle cx="-16" cy="-40" r="2" fill="{color}"/>
      <circle cx="0" cy="-48" r="2" fill="{color}"/>
      <circle cx="16" cy="-40" r="2" fill="{color}"/>
      <!-- Face -->
      <path d="M -12,-28 L 12,-28 L 12,-6 Q 12,8 0,8 Q -12,8 -12,-6 Z" fill="#fdfbf5" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>
      <!-- Hair lines -->
      <path d="M -14,-22 C -20,-10 -20,15 -14,24" fill="none" stroke="{color}" stroke-width="2"/>
      <path d="M 14,-22 C 20,-10 20,15 14,24" fill="none" stroke="{color}" stroke-width="2"/>
      <!-- Eyes & Face details -->
      <circle cx="-5" cy="-12" r="1.5" fill="{color}"/>
      <circle cx="5" cy="-12" r="1.5" fill="{color}"/>
      <path d="M 0,-14 L 0,-9 L 2,-9" stroke="{color}" stroke-width="2" fill="none"/>
      <path d="M -4,-2 Q 0,1 4,-2" stroke="{color}" stroke-width="2" fill="none"/>
      <!-- Shoulders/Collar -->
      <path d="M -26,35 L -16,8 Q 0,12 16,8 L 26,35 Z" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>
      <path d="M -8,10 Q 0,16 8,10" stroke="{color}" stroke-width="1.5" fill="none"/>
      <circle cx="0" cy="14" r="2.5" fill="{color}"/>
      <!-- Flower -->
      <path d="M 22,-5 Q 22,15 22,35" stroke="{color}" stroke-width="2" fill="none"/>
      <circle cx="22" cy="-9" r="3.5" fill="{color}"/>
    </g>
    <!-- Bottom Half -->
    <g transform="rotate(180)">
      <!-- Crown -->
      <path d="M -16,-28 L -16,-40 L -8,-32 L 0,-48 L 8,-32 L 16,-40 L 16,-28 Z" fill="{color}"/>
      <line x1="-12" y1="-28" x2="12" y2="-28" stroke="#fdfbf5" stroke-width="2"/>
      <circle cx="-16" cy="-40" r="2" fill="{color}"/>
      <circle cx="0" cy="-48" r="2" fill="{color}"/>
      <circle cx="16" cy="-40" r="2" fill="{color}"/>
      <!-- Face -->
      <path d="M -12,-28 L 12,-28 L 12,-6 Q 12,8 0,8 Q -12,8 -12,-6 Z" fill="#fdfbf5" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>
      <!-- Hair lines -->
      <path d="M -14,-22 C -20,-10 -20,15 -14,24" fill="none" stroke="{color}" stroke-width="2"/>
      <path d="M 14,-22 C 20,-10 20,15 14,24" fill="none" stroke="{color}" stroke-width="2"/>
      <!-- Eyes & Face details -->
      <circle cx="-5" cy="-12" r="1.5" fill="{color}"/>
      <circle cx="5" cy="-12" r="1.5" fill="{color}"/>
      <path d="M 0,-14 L 0,-9 L 2,-9" stroke="{color}" stroke-width="2" fill="none"/>
      <path d="M -4,-2 Q 0,1 4,-2" stroke="{color}" stroke-width="2" fill="none"/>
      <!-- Shoulders/Collar -->
      <path d="M -26,35 L -16,8 Q 0,12 16,8 L 26,35 Z" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>
      <path d="M -8,10 Q 0,16 8,10" stroke="{color}" stroke-width="1.5" fill="none"/>
      <circle cx="0" cy="14" r="2.5" fill="{color}"/>
      <!-- Flower -->
      <path d="M 22,-5 Q 22,15 22,35" stroke="{color}" stroke-width="2" fill="none"/>
      <circle cx="22" cy="-9" r="3.5" fill="{color}"/>
    </g>
  </g>
</svg>
"""

FACE_K = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 252" width="180" height="252">
  <rect x="3" y="3" width="174" height="246" rx="16" fill="#fdfbf5" stroke="#d8cfb8" stroke-width="2"/>
  <!-- Corners -->
  <g fill="{color}" font-family="Georgia, 'Times New Roman', serif" font-weight="700">
    <g>
      <text x="24" y="44" font-size="28" text-anchor="middle">K</text>
      <text x="24" y="72" font-size="24" text-anchor="middle">{suit}</text>
    </g>
    <g transform="rotate(180 90 126)">
      <text x="24" y="44" font-size="28" text-anchor="middle">K</text>
      <text x="24" y="72" font-size="24" text-anchor="middle">{suit}</text>
    </g>
  </g>
  <!-- Portrait Frame -->
  <rect x="42" y="42" width="96" height="168" rx="8" fill="none" stroke="{color}" stroke-width="1.5" stroke-dasharray="4 4" opacity="0.5"/>
  <!-- King Portrait -->
  <g transform="translate(90, 126)">
    <!-- Top Half -->
    <g>
      <!-- Crown -->
      <path d="M -20,-30 L -20,-45 L -10,-38 L 0,-52 L 10,-38 L 20,-45 L 20,-30 Z" fill="{color}"/>
      <line x1="-15" y1="-30" x2="15" y2="-30" stroke="#fdfbf5" stroke-width="2"/>
      <circle cx="-20" cy="-45" r="2.5" fill="{color}"/>
      <circle cx="0" cy="-52" r="2.5" fill="{color}"/>
      <circle cx="20" cy="-45" r="2.5" fill="{color}"/>
      <!-- Face -->
      <path d="M -15,-30 L 15,-30 L 15,-5 Q 15,10 0,10 Q -15,10 -15,-5 Z" fill="#fdfbf5" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>
      <!-- Beard & Hair lines -->
      <path d="M -15,-20 Q -22,-10 -15,5 Q 0,22 15,5 Q 22,-10 15,-20" fill="none" stroke="{color}" stroke-width="2"/>
      <path d="M -15,0 L -12,12 L 0,18 L 12,12 L 15,0 Q 8,5 0,5 Q -8,5 -15,0 Z" fill="{color}"/>
      <path d="M -10,-3 Q 0,2 10,-3" stroke="{color}" stroke-width="2" fill="none"/>
      <!-- Eyes & Nose -->
      <line x1="-7" y1="-14" x2="-3" y2="-14" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="3" y1="-14" x2="7" y2="-14" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>
      <path d="M 0,-16 L 0,-10 L 3,-10" stroke="{color}" stroke-width="2.5" fill="none"/>
      <!-- Shoulders/Collar -->
      <path d="M -30,35 L -18,10 Q 0,15 18,10 L 30,35 Z" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>
      <path d="M -12,10 L 0,25 L 12,10" stroke="{color}" stroke-width="2" fill="none"/>
      <!-- Scepter -->
      <line x1="24" y1="-10" x2="24" y2="35" stroke="{color}" stroke-width="2"/>
      <circle cx="24" cy="-14" r="4" fill="{color}"/>
    </g>
    <!-- Bottom Half -->
    <g transform="rotate(180)">
      <!-- Crown -->
      <path d="M -20,-30 L -20,-45 L -10,-38 L 0,-52 L 10,-38 L 20,-45 L 20,-30 Z" fill="{color}"/>
      <line x1="-15" y1="-30" x2="15" y2="-30" stroke="#fdfbf5" stroke-width="2"/>
      <circle cx="-20" cy="-45" r="2.5" fill="{color}"/>
      <circle cx="0" cy="-52" r="2.5" fill="{color}"/>
      <circle cx="20" cy="-45" r="2.5" fill="{color}"/>
      <!-- Face -->
      <path d="M -15,-30 L 15,-30 L 15,-5 Q 15,10 0,10 Q -15,10 -15,-5 Z" fill="#fdfbf5" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>
      <!-- Beard & Hair lines -->
      <path d="M -15,-20 Q -22,-10 -15,5 Q 0,22 15,5 Q 22,-10 15,-20" fill="none" stroke="{color}" stroke-width="2"/>
      <path d="M -15,0 L -12,12 L 0,18 L 12,12 L 15,0 Q 8,5 0,5 Q -8,5 -15,0 Z" fill="{color}"/>
      <path d="M -10,-3 Q 0,2 10,-3" stroke="{color}" stroke-width="2" fill="none"/>
      <!-- Eyes & Nose -->
      <line x1="-7" y1="-14" x2="-3" y2="-14" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="3" y1="-14" x2="7" y2="-14" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>
      <path d="M 0,-16 L 0,-10 L 3,-10" stroke="{color}" stroke-width="2.5" fill="none"/>
      <!-- Shoulders/Collar -->
      <path d="M -30,35 L -18,10 Q 0,15 18,10 L 30,35 Z" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>
      <path d="M -12,10 L 0,25 L 12,10" stroke="{color}" stroke-width="2" fill="none"/>
      <!-- Scepter -->
      <line x1="24" y1="-10" x2="24" y2="35" stroke="{color}" stroke-width="2"/>
      <circle cx="24" cy="-14" r="4" fill="{color}"/>
    </g>
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
            if label == "A":
                svg = FACE_A.format(color=color, suit=glyph)
            elif label == "J":
                svg = FACE_J.format(color=color, suit=glyph)
            elif label == "Q":
                svg = FACE_Q.format(color=color, suit=glyph)
            elif label == "K":
                svg = FACE_K.format(color=color, suit=glyph)
            else:
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
