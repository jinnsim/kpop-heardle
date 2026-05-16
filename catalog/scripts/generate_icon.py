#!/usr/bin/env python3
"""Generate the 1024x1024 K-Pop Heardle iOS app icon."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


SIZE = 1024
CENTER_Y = 512
BAR_WIDTH = 96
BAR_GAP = 56
BAR_RADIUS = 48
BAR_HEIGHTS = [280, 520, 720, 520, 280]
BAR_COLOR = (255, 255, 255, 255)
SHADOW_OFFSET_Y = 30
SHADOW_BLUR_RADIUS = 60
SHADOW_COLOR = (0, 0, 0, int(255 * 0.25))

TOP = (0x7C, 0x3A, 0xED)
MIDDLE = (0xE9, 0x4B, 0x7B)
BOTTOM = (0xFF, 0x9F, 0x66)

OUT_PATH = Path(
    "ios/KPopHeardle/Resources/Assets.xcassets/"
    "AppIcon.appiconset/Icon-1024.png"
)


def lerp_channel(start: int, end: int, t: float) -> int:
    return round(start + (end - start) * t)


def lerp_color(start: tuple[int, int, int], end: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(lerp_channel(a, b, t) for a, b in zip(start, end, strict=True))


def background_gradient() -> Image.Image:
    image = Image.new("RGB", (SIZE, SIZE))
    pixels = image.load()

    for y in range(SIZE):
        if y <= CENTER_Y:
            color = lerp_color(TOP, MIDDLE, y / CENTER_Y)
        else:
            color = lerp_color(MIDDLE, BOTTOM, (y - CENTER_Y) / (SIZE - CENTER_Y - 1))

        for x in range(SIZE):
            pixels[x, y] = color

    return image


def draw_bars(mask: Image.Image, fill: int | tuple[int, int, int, int]) -> None:
    draw = ImageDraw.Draw(mask)
    total_width = len(BAR_HEIGHTS) * BAR_WIDTH + (len(BAR_HEIGHTS) - 1) * BAR_GAP
    x = (SIZE - total_width) // 2

    for height in BAR_HEIGHTS:
        y0 = CENTER_Y - height // 2
        y1 = y0 + height - 1
        draw.rounded_rectangle(
            (x, y0, x + BAR_WIDTH - 1, y1),
            radius=BAR_RADIUS,
            fill=fill,
        )
        x += BAR_WIDTH + BAR_GAP


def main() -> None:
    icon = background_gradient()

    shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw_bars(shadow, SHADOW_COLOR)
    shadow = shadow.filter(ImageFilter.GaussianBlur(SHADOW_BLUR_RADIUS))
    icon = Image.alpha_composite(
        icon.convert("RGBA"),
        Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0)),
    )
    icon.alpha_composite(shadow, (0, SHADOW_OFFSET_Y))

    bars = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw_bars(bars, BAR_COLOR)
    icon.alpha_composite(bars)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    icon.convert("RGB").save(OUT_PATH, "PNG")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
