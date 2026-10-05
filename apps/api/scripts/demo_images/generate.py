"""Render the illustrated product images used by scripts/seed_demo_data.py.

The output (*.webp next to this file) is committed, so seeding needs
neither Pillow nor this script. Re-run it only to change the artwork —
Pillow isn't an API dependency, so use a throwaway container from
apps/api:

    docker run --rm -v "$PWD":/src -w /src python:3.11-slim sh -c \\
      "apt-get update -qq && apt-get install -y -qq fonts-dejavu-core >/dev/null \\
       && pip install -q pillow && python scripts/demo_images/generate.py"

Every image is a square drawn around its centre, so the storefront's
4:3 card crop and 1:1 gallery both keep the subject in frame.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = 1200
# Supersampled, then downscaled, for smooth edges on shapes Pillow
# doesn't antialias itself (polygons, ellipses).
SCALE = 2
OUT_DIR = Path(__file__).resolve().parent
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
MONO_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

# Filled (black) chess glyphs; the outline (white) glyph for each is 6
# code points lower and is drawn on top as the piece's contour.
KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN = "♚", "♛", "♜", "♝", "♞", "♟"

Color = tuple[int, int, int]


def hex_color(value: str) -> Color:
    value = value.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def shade(color: Color, factor: float) -> Color:
    """factor < 1 darkens, > 1 lightens toward white."""
    if factor <= 1:
        return tuple(round(c * factor) for c in color)
    return tuple(round(c + (255 - c) * (factor - 1)) for c in color)


@dataclass
class Palette:
    background: Color
    light_square: Color
    dark_square: Color
    light_piece: Color
    dark_piece: Color
    frame: Color


def palette(
    background: str, light_sq: str, dark_sq: str, light_pc: str, dark_pc: str, frame: str
) -> Palette:
    return Palette(
        *(hex_color(v) for v in (background, light_sq, dark_sq, light_pc, dark_pc, frame))
    )


def solid_mask(mask: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    """The font's filled chess glyphs have see-through details (the
    crown's jewels, the knight's eye). Flood the outside from a corner of
    the glyph's box; anything still empty afterwards is a hole, so fill
    it — the outline glyph drawn on top restores the detail lines."""
    region = mask.crop(box)
    ImageDraw.floodfill(region, (0, 0), 128)
    region = region.point(lambda v: 0 if v == 128 else 255 if v == 0 else v)
    solid = Image.new("L", mask.size, 0)
    solid.paste(region, box[:2])
    return solid


class Canvas:
    def __init__(self, background: Color) -> None:
        self.size = SIZE * SCALE
        self.image = Image.new("RGB", (self.size, self.size), background)
        self._backdrop(background)

    def s(self, value: float) -> int:
        return round(value * SCALE)

    def _backdrop(self, base: Color) -> None:
        # Soft studio light: bright centre falling off to a dark edge.
        glow = Image.new("L", (self.size, self.size), 0)
        ImageDraw.Draw(glow).ellipse(
            (self.s(-150), self.s(-250), self.s(1350), self.s(1050)), fill=255
        )
        glow = glow.filter(ImageFilter.GaussianBlur(self.s(220)))
        lit = Image.new("RGB", (self.size, self.size), shade(base, 1.35))
        dark = Image.new("RGB", (self.size, self.size), shade(base, 0.55))
        self.image = Image.composite(lit, dark, glow)

    def shadow(self, box: tuple[float, float, float, float], strength: int = 150) -> None:
        mask = Image.new("L", (self.size, self.size), 0)
        ImageDraw.Draw(mask).ellipse(tuple(self.s(v) for v in box), fill=strength)
        mask = mask.filter(ImageFilter.GaussianBlur(self.s(18)))
        self.image.paste((0, 0, 0), (0, 0), mask)

    def polygon(
        self,
        points: list[tuple[float, float]],
        fill: Color,
        outline: Color | None = None,
        width: float = 0,
    ) -> None:
        draw = ImageDraw.Draw(self.image)
        scaled = [(self.s(x), self.s(y)) for x, y in points]
        draw.polygon(scaled, fill=fill)
        if outline:
            draw.line([*scaled, scaled[0]], fill=outline, width=self.s(width), joint="curve")

    def piece(self, glyph: str, cx: float, base_y: float, height: float, color: Color) -> None:
        """A chess piece standing with its base at (cx, base_y): the
        filled glyph shaded top-to-bottom, the outline glyph as its
        contour, and a contact shadow underneath."""
        font = ImageFont.truetype(FONT_PATH, self.s(height * 1.18))
        left, top, right, bottom = font.getbbox(glyph)
        width = right - left
        x = self.s(cx) - width / 2 - left
        y = self.s(base_y) - bottom

        self.shadow(
            (cx - width / SCALE * 0.45, base_y - 14, cx + width / SCALE * 0.45, base_y + 12)
        )

        mask = Image.new("L", (self.size, self.size), 0)
        ImageDraw.Draw(mask).text((x, y), glyph, font=font, fill=255)
        mask = solid_mask(
            mask,
            (round(x + left) - 4, round(y + top) - 4, round(x + right) + 4, round(y + bottom) + 4),
        )
        gradient = Image.new("RGB", (1, 256))
        for i in range(256):
            t = i / 255
            gradient.putpixel(
                (0, i), shade(color, 1.45 - 0.75 * t) if t < 0.5 else shade(color, 1.1 - 0.5 * t)
            )
        gradient = gradient.resize((self.size, bottom - top + 1))
        fill = Image.new("RGB", (self.size, self.size), color)
        fill.paste(gradient, (0, round(y + top)))
        self.image = Image.composite(fill, self.image, mask)

        outline = chr(ord(glyph) - 6)
        ImageDraw.Draw(self.image).text((x, y), outline, font=font, fill=shade(color, 0.35))

    def text(
        self, value: str, cx: float, cy: float, size: float, color: Color, mono: bool = False
    ) -> None:
        font = ImageFont.truetype(MONO_FONT_PATH if mono else FONT_PATH, self.s(size))
        ImageDraw.Draw(self.image).text(
            (self.s(cx), self.s(cy)), value, font=font, fill=color, anchor="mm"
        )

    def save(self, name: str) -> None:
        final = self.image.resize((SIZE, SIZE), Image.LANCZOS)
        final.save(OUT_DIR / f"{name}.webp", "WEBP", quality=82, method=6)
        print(f"wrote {name}.webp")


# --- Scene pieces ---------------------------------------------------------

# Perspective board: squares projected from a flat 8x8 grid onto a
# trapezoid receding toward the top of the frame.
BOARD_NEAR_Y, BOARD_FAR_Y = 1010, 560
BOARD_NEAR_HALF, BOARD_FAR_HALF = 500, 330
# How much farther the far edge is than the near edge (1.0 = twice as far).
BOARD_DEPTH = 0.7


def board_point(col: float, row: float) -> tuple[float, float]:
    """(col, row) in 0..8 board units -> canvas coordinates; row 0 is nearest."""
    # True perspective: screen offset scales with 1/distance, so far rows
    # compress more than near ones (and the frame just past row 8 still
    # projects sensibly).
    near, far = 1.0, 1.0 + BOARD_DEPTH
    distance = near + (far - near) * row / 8
    depth = (1 / near - 1 / distance) / (1 / near - 1 / far)
    y = BOARD_NEAR_Y + (BOARD_FAR_Y - BOARD_NEAR_Y) * depth
    half = BOARD_NEAR_HALF + (BOARD_FAR_HALF - BOARD_NEAR_HALF) * depth
    return (600 - half + 2 * half * col / 8, y)


def square_centre(col: int, row: int) -> tuple[float, float, float]:
    """Canvas (x, y) of a square's centre plus a scale for pieces on it."""
    x, y = board_point(col + 0.5, row + 0.5)
    _, near_y = board_point(0, 0)
    _, far_y = board_point(0, 8)
    scale = 1 - 0.36 * (near_y - y) / (near_y - far_y)
    return x, y, scale


def perspective_board(canvas: Canvas, pal: Palette, frame_depth: float = 0.32) -> None:
    corners = [
        board_point(-frame_depth, -frame_depth),
        board_point(8 + frame_depth, -frame_depth),
        board_point(8 + frame_depth, 8 + frame_depth),
        board_point(-frame_depth, 8 + frame_depth),
    ]
    canvas.shadow(
        (corners[0][0] - 10, corners[0][1] - 40, corners[1][0] + 10, corners[0][1] + 60), 170
    )
    # Board edge (thickness) below the near side.
    near_left, near_right = corners[0], corners[1]
    canvas.polygon(
        [
            near_left,
            near_right,
            (near_right[0], near_right[1] + 34),
            (near_left[0], near_left[1] + 34),
        ],
        shade(pal.frame, 0.6),
    )
    canvas.polygon(corners, pal.frame)
    for row in range(8):
        for col in range(8):
            color = pal.light_square if (row + col) % 2 else pal.dark_square
            canvas.polygon(
                [
                    board_point(col, row),
                    board_point(col + 1, row),
                    board_point(col + 1, row + 1),
                    board_point(col, row + 1),
                ],
                color,
            )


def set_scene(pal: Palette, name: str) -> None:
    canvas = Canvas(pal.background)
    perspective_board(canvas, pal)
    # A handful of pieces mid-game, drawn far-to-near so nearer ones overlap.
    placements = [
        (ROOK, 0, 7, pal.dark_piece),
        (KING, 4, 7, pal.dark_piece),
        (PAWN, 2, 6, pal.dark_piece),
        (PAWN, 6, 6, pal.dark_piece),
        (KNIGHT, 5, 5, pal.dark_piece),
        (BISHOP, 2, 3, pal.light_piece),
        (PAWN, 4, 3, pal.light_piece),
        (QUEEN, 3, 1, pal.light_piece),
        (KING, 6, 0, pal.light_piece),
        (PAWN, 1, 1, pal.light_piece),
    ]
    for glyph, col, row, color in sorted(placements, key=lambda p: -p[2]):
        x, y, scale = square_centre(col, row)
        height = (240 if glyph in (KING, QUEEN) else 200 if glyph != PAWN else 150) * scale
        canvas.piece(glyph, x, y + 12 * scale, height, color)
    canvas.save(name)


def pieces_scene(
    pal: Palette, name: str, glyphs: tuple[str, ...] = (ROOK, KNIGHT, KING, QUEEN, BISHOP, PAWN)
) -> None:
    canvas = Canvas(pal.background)
    # A ledge for the pieces to stand on.
    canvas.polygon([(80, 820), (1120, 820), (1180, 960), (20, 960)], shade(pal.frame, 0.9))
    canvas.polygon([(20, 960), (1180, 960), (1180, 1000), (20, 1000)], shade(pal.frame, 0.55))
    # One row, alternating light and dark, tallest pieces in the middle.
    step = 960 / len(glyphs)
    for index, glyph in enumerate(glyphs):
        x = 120 + step * (index + 0.5)
        height = 330 if glyph in (KING, QUEEN) else 280 if glyph != PAWN else 220
        color = pal.light_piece if index % 2 else pal.dark_piece
        canvas.piece(glyph, x, 900, height, color)
    canvas.save(name)


def hero_scene(pal: Palette, name: str, glyph: str = KNIGHT) -> None:
    """A single piece, large — the 'detail shot'."""
    canvas = Canvas(pal.background)
    canvas.polygon([(200, 900), (1000, 900), (1060, 990), (140, 990)], shade(pal.frame, 0.85))
    canvas.piece(glyph, 600, 930, 620, pal.light_piece)
    canvas.save(name)


def flat_board_scene(
    pal: Palette,
    name: str,
    border: Callable[[Canvas, float, float, float, float], None] | None = None,
    rotate: float = -8,
) -> None:
    """Top-down board, slightly rotated, with optional decorated border."""
    canvas = Canvas(pal.background)
    layer = Image.new("RGBA", (canvas.size, canvas.size), (0, 0, 0, 0))
    sub = Canvas.__new__(Canvas)
    sub.size, sub.image = canvas.size, layer
    left, top, side, margin = 230, 230, 740, 46
    draw = ImageDraw.Draw(layer)
    s = canvas.s
    draw.rectangle(
        (s(left - margin), s(top - margin), s(left + side + margin), s(top + side + margin)),
        fill=pal.frame + (255,),
    )
    cell = side / 8
    for row in range(8):
        for col in range(8):
            color = pal.light_square if (row + col) % 2 == 0 else pal.dark_square
            draw.rectangle(
                (
                    s(left + col * cell),
                    s(top + row * cell),
                    s(left + (col + 1) * cell),
                    s(top + (row + 1) * cell),
                ),
                fill=color + (255,),
            )
    if border:
        border(sub, left - margin, top - margin, side + 2 * margin, margin)
    layer = layer.rotate(rotate, resample=Image.BICUBIC, center=(canvas.size / 2, canvas.size / 2))
    shadow = layer.split()[3].filter(ImageFilter.GaussianBlur(s(26)))
    canvas.image.paste((0, 0, 0), (s(18), s(30)), shadow.point(lambda a: a * 0.55))
    canvas.image.paste(layer, (0, 0), layer)
    canvas.save(name)


def kantha_border(canvas: Canvas, left: float, top: float, side: float, margin: float) -> None:
    """Running-stitch rows along the cloth's border, nakshi kantha style."""
    draw = ImageDraw.Draw(canvas.image)
    s = canvas.s
    for inset, color in ((10, (163, 38, 42)), (24, (31, 76, 122)), (36, (163, 38, 42))):
        for i in range(0, round(side - 2 * inset), 16):
            for x0, y0, x1, y1 in (
                (left + inset + i, top + inset, left + inset + i + 9, top + inset),
                (left + inset + i, top + side - inset, left + inset + i + 9, top + side - inset),
                (left + inset, top + inset + i, left + inset, top + inset + i + 9),
                (left + side - inset, top + inset + i, left + side - inset, top + inset + i + 9),
            ):
                draw.line((s(x0), s(y0), s(x1), s(y1)), fill=color + (255,), width=s(3))


def roll_scene(pal: Palette, name: str) -> None:
    """Silk board unrolling from a cylinder, with a few pieces on it."""
    canvas = Canvas(pal.background)
    perspective_board(canvas, pal, frame_depth=0.12)
    # The rolled-up far end.
    far_left, far_right = board_point(-0.12, 8.12), board_point(8.12, 8.12)
    radius = 46
    canvas.polygon(
        [
            (far_left[0], far_left[1] - 2 * radius),
            (far_right[0], far_right[1] - 2 * radius),
            (far_right[0], far_right[1]),
            (far_left[0], far_left[1]),
        ],
        shade(pal.frame, 0.8),
    )
    draw = ImageDraw.Draw(canvas.image)
    s = canvas.s
    draw.rectangle(
        (
            s(far_left[0]),
            s(far_left[1] - 2 * radius + 10),
            s(far_right[0]),
            s(far_left[1] - radius - 4),
        ),
        fill=shade(pal.frame, 1.25),
    )
    draw.ellipse(
        (s(far_right[0] - 22), s(far_right[1] - 2 * radius), s(far_right[0] + 22), s(far_right[1])),
        fill=shade(pal.frame, 0.6),
    )
    for glyph, col, row, color in (
        (KING, 4, 5, pal.dark_piece),
        (KNIGHT, 2, 3, pal.light_piece),
        (PAWN, 5, 2, pal.light_piece),
    ):
        x, y, scale = square_centre(col, row)
        canvas.piece(glyph, x, y + 10 * scale, (300 if glyph == KING else 230) * scale, color)
    canvas.save(name)


def box_scene(pal: Palette, name: str, woven: bool = False, emblem: str | None = KNIGHT) -> None:
    canvas = Canvas(pal.background)
    body = pal.frame
    front = [(250, 560), (950, 560), (950, 900), (250, 900)]
    top = [(250, 560), (950, 560), (1040, 430), (340, 430)]
    side = [(950, 560), (1040, 430), (1040, 760), (950, 900)]
    canvas.shadow((200, 860, 1100, 960), 190)
    canvas.polygon(front, body)
    canvas.polygon(top, shade(body, 1.25))
    canvas.polygon(side, shade(body, 0.7))
    draw = ImageDraw.Draw(canvas.image)
    s = canvas.s
    if woven:
        # Cane weave: alternating diagonal hatches on the front face.
        for row in range(0, 340, 34):
            for col in range(0, 700, 34):
                x, y = 250 + col, 560 + row
                flip = (row // 34 + col // 34) % 2
                draw.line(
                    (s(x + 4), s(y + (30 if flip else 4)), s(x + 30), s(y + (4 if flip else 30))),
                    fill=shade(body, 0.72),
                    width=s(5),
                )
    else:
        # Lid seam and a carved lotus-ish rosette.
        draw.line((s(250), s(620), s(950), s(620)), fill=shade(body, 0.6), width=s(6))
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            cx, cy = 600 + 70 * math.cos(rad), 760 + 70 * math.sin(rad) * 0.9
            draw.ellipse(
                (s(cx - 40), s(cy - 26), s(cx + 40), s(cy + 26)),
                outline=shade(body, 0.55),
                width=s(5),
            )
    if emblem and woven:
        canvas.piece(emblem, 650, 505, 210, pal.light_piece)
    canvas.save(name)


def clock_scene(pal: Palette, name: str, digital: bool = False) -> None:
    canvas = Canvas(pal.background)
    body = pal.frame
    canvas.shadow((170, 830, 1030, 940), 190)
    canvas.polygon([(200, 880), (1000, 880), (940, 480), (260, 480)], body)
    canvas.polygon([(260, 480), (940, 480), (900, 440), (300, 440)], shade(body, 1.3))
    draw = ImageDraw.Draw(canvas.image)
    s = canvas.s
    # Plungers on top.
    for x, pressed in ((430, False), (770, True)):
        h = 30 if pressed else 70
        draw.rounded_rectangle(
            (s(x - 45), s(440 - h), s(x + 45), s(446)), radius=s(14), fill=shade(body, 0.6)
        )
    if digital:
        draw.rounded_rectangle((s(300), s(560), s(900), s(760)), radius=s(18), fill=(28, 34, 30))
        canvas.text("5:00", 445, 662, 110, (150, 230, 160), mono=True)
        canvas.text("4:58", 755, 662, 110, (150, 230, 160), mono=True)
        draw.line((s(600), s(580), s(600), s(740)), fill=(70, 80, 72), width=s(4))
    else:
        for cx, minute in ((430, 50), (770, 20)):
            draw.ellipse(
                (s(cx - 150), s(530), s(cx + 150), s(830)),
                fill=(240, 232, 214),
                outline=shade(body, 0.5),
                width=s(10),
            )
            for tick in range(12):
                rad = math.radians(tick * 30)
                draw.line(
                    [
                        (s(cx + 120 * math.sin(rad)), s(680 - 120 * math.cos(rad))),
                        (s(cx + 136 * math.sin(rad)), s(680 - 136 * math.cos(rad))),
                    ],
                    fill=(40, 30, 25),
                    width=s(5),
                )
            for length, angle, width in ((80, 330, 9), (118, minute * 6, 6)):
                rad = math.radians(angle)
                draw.line(
                    (
                        s(cx),
                        s(680),
                        s(cx + length * math.sin(rad)),
                        s(680 - length * math.cos(rad)),
                    ),
                    fill=(30, 22, 18),
                    width=s(width),
                )
            draw.polygon(
                [(s(cx + 92), s(560)), (s(cx + 116), s(560)), (s(cx + 104), s(590))],
                fill=(178, 34, 34),
            )
    canvas.save(name)


# --- Palettes -------------------------------------------------------------

ROSEWOOD = palette("#3a2219", "#e6c79c", "#6b2e1f", "#efd7b2", "#4a1f15", "#3d1a12")
MANGO = palette("#3b2a1a", "#e9cf9f", "#a0703c", "#f0dcb4", "#6e4422", "#5b3a1e")
MANGO_EBONISED = palette("#2c2420", "#e9cf9f", "#a0703c", "#f0dcb4", "#211a16", "#5b3a1e")
BRASS_ANTIQUE = palette("#13302e", "#c9ab72", "#5e4b2a", "#b8935a", "#4d3c20", "#3a2c18")
BRASS_POLISHED = palette("#123130", "#efd78e", "#7a5a1c", "#ecc659", "#7a5a1c", "#3a2c18")
BRASS_COPPER = palette("#1d2a33", "#e7c27a", "#7b3f22", "#e2b45a", "#b5653a", "#33231a")
MAPLE_ROSEWOOD = palette("#2f241c", "#ecd9b5", "#5c2a1c", "#efd7b2", "#3b1a12", "#432116")
BOXWOOD = palette("#2a2a2e", "#e2cfa4", "#7a5a3a", "#ecd6a6", "#2a201a", "#4a3a2a")
SILK_MAROON = palette("#2a1418", "#e8c9a8", "#7a1f2b", "#f2e2c8", "#5a3a22", "#8a2433")
SILK_INDIGO = palette("#151a2e", "#d9d4c4", "#2b3a7a", "#f2e2c8", "#5a3a22", "#33449a")
SILK_SAFFRON = palette("#2e2210", "#f6e2b4", "#d4851f", "#fbf0d8", "#6a3d14", "#e39b2d")
KANTHA = palette("#3a3530", "#f3ead6", "#b89a68", "#f2e2c8", "#3a2a1e", "#efe4cc")
CANE = palette("#24302a", "#d9c28e", "#9a7a44", "#f0dcb4", "#4a2e1a", "#c9a868")
WALNUT = palette("#26303a", "#e0c9a0", "#6b4a30", "#f0dcb4", "#2a1c12", "#5a3a22")
DIGITAL = palette("#1e2328", "#e0e0e0", "#6b6b6b", "#f0f0f0", "#202020", "#2b2f33")
EBONY = palette("#18181c", "#d8d2c8", "#1c1714", "#e8e2d8", "#141110", "#26201b")
PLASTIC = palette("#2b3138", "#f2f2f2", "#3a7a4a", "#f5f5f5", "#2a2a2a", "#cfcfcf")


SCENES: dict[str, Callable[[], None]] = {
    "SH-WCS-001-1": lambda: set_scene(ROSEWOOD, "SH-WCS-001-1"),
    "SH-WCS-001-2": lambda: hero_scene(ROSEWOOD, "SH-WCS-001-2"),
    "SH-WCS-002-NAT": lambda: set_scene(MANGO, "SH-WCS-002-NAT"),
    "SH-WCS-002-EBN": lambda: set_scene(MANGO_EBONISED, "SH-WCS-002-EBN"),
    "SH-WCS-002-2": lambda: hero_scene(MANGO, "SH-WCS-002-2"),
    "SH-WCS-003-1": lambda: set_scene(MANGO, "SH-WCS-003-1"),
    "SH-BMS-001-ANT": lambda: set_scene(BRASS_ANTIQUE, "SH-BMS-001-ANT"),
    "SH-BMS-001-POL": lambda: set_scene(BRASS_POLISHED, "SH-BMS-001-POL"),
    "SH-BMS-001-2": lambda: hero_scene(BRASS_POLISHED, "SH-BMS-001-2", KING),
    "SH-BMS-002-1": lambda: set_scene(BRASS_COPPER, "SH-BMS-002-1"),
    "SH-BMS-002-2": lambda: pieces_scene(BRASS_COPPER, "SH-BMS-002-2"),
    "SH-TCS-001-MAR": lambda: roll_scene(SILK_MAROON, "SH-TCS-001-MAR"),
    "SH-TCS-001-IND": lambda: roll_scene(SILK_INDIGO, "SH-TCS-001-IND"),
    "SH-TCS-001-SAF": lambda: roll_scene(SILK_SAFFRON, "SH-TCS-001-SAF"),
    "SH-TCS-002-1": lambda: flat_board_scene(MANGO, "SH-TCS-002-1", rotate=10),
    "SH-CB-001-1": lambda: flat_board_scene(MAPLE_ROSEWOOD, "SH-CB-001-1"),
    "SH-CB-002-1": lambda: flat_board_scene(KANTHA, "SH-CB-002-1", border=kantha_border, rotate=6),
    "SH-CP-001-1": lambda: pieces_scene(BOXWOOD, "SH-CP-001-1"),
    "SH-CP-001-2": lambda: hero_scene(BOXWOOD, "SH-CP-001-2"),
    "SH-CP-002-1": lambda: pieces_scene(
        BRASS_POLISHED, "SH-CP-002-1", (ROOK, BISHOP, KING, QUEEN, KNIGHT, PAWN)
    ),
    "SH-SB-001-1": lambda: box_scene(CANE, "SH-SB-001-1", woven=True),
    "SH-SB-002-1": lambda: box_scene(MANGO, "SH-SB-002-1"),
    "SH-CC-001-1": lambda: clock_scene(WALNUT, "SH-CC-001-1"),
    "SH-CC-002-1": lambda: clock_scene(DIGITAL, "SH-CC-002-1", digital=True),
    "SH-WCS-099-1": lambda: set_scene(EBONY, "SH-WCS-099-1"),
    "SH-TCS-090-1": lambda: set_scene(PLASTIC, "SH-TCS-090-1"),
}


if __name__ == "__main__":
    for render in SCENES.values():
        render()
