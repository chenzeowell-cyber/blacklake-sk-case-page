#!/usr/bin/env python3
"""Render a Black Lake SK case JSON to the fixed 910x1236 PNG canvas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps


SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS = SKILL_DIR / "assets"
FONTS = ASSETS / "fonts"
W, H = 910, 1236


def font(name: str, size: float) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), round(size))


F_HEAVY_64 = font("MiSans-Heavy.ttf", 64)
F_REG_28 = font("MiSans-Regular.ttf", 28)
F_MED_28 = font("MiSans-Medium.ttf", 28)
F_REG_16 = font("MiSans-Regular.ttf", 16)
F_SEMI_17 = font("MiSans-Semibold.ttf", 17)
F_REG_14 = font("MiSans-Regular.ttf", 14.5)
F_MED_15 = font("MiSans-Medium.ttf", 15)
F_MED_10 = font("MiSans-Medium.ttf", 10)


def gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    im = Image.new("RGB", size)
    d = ImageDraw.Draw(im)
    for y in range(size[1]):
        t = y / max(1, size[1] - 1)
        color = tuple(round(a * (1 - t) + b * t) for a, b in zip(top, bottom))
        d.line((0, y, size[0], y), fill=color)
    return im


def wrap(draw: ImageDraw.ImageDraw, value: str, face: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for ch in value.strip():
        trial = current + ch
        if current and draw.textlength(trial, font=face) > max_width:
            lines.append(current)
            current = ch
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def draw_lines(draw: ImageDraw.ImageDraw, xy: tuple[int, int], lines: list[str], face: ImageFont.FreeTypeFont,
               fill: tuple[int, int, int], line_height: int, max_lines: int, qa: dict, field: str) -> None:
    if len(lines) > max_lines:
        qa["errors"].append(f"{field} 需要 {len(lines)} 行，超过版式上限 {max_lines} 行")
    for i, line in enumerate(lines[:max_lines]):
        draw.text((xy[0], xy[1] + i * line_height), line, font=face, fill=fill, anchor="lt")


def resolve_media(json_path: Path, value: object) -> tuple[Path | None, bool]:
    if isinstance(value, str):
        raw, generated = value, False
    elif isinstance(value, dict):
        raw, generated = str(value.get("path", "")), bool(value.get("ai_generated", False))
    else:
        raw, generated = "", False
    if not raw:
        return None, generated
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (json_path.parent / path).resolve()
    return path, generated


def fit_media(path: Path | None, size: tuple[int, int], qa: dict, slot: str) -> Image.Image:
    if path is None or not path.is_file():
        qa["errors"].append(f"缺少图片：{slot}")
        placeholder = gradient(size, (239, 247, 246), (218, 232, 230))
        d = ImageDraw.Draw(placeholder)
        label = f"请补充{slot}"
        box = d.textbbox((0, 0), label, font=F_REG_14)
        d.text(((size[0] - (box[2] - box[0])) // 2, (size[1] - (box[3] - box[1])) // 2), label,
               font=F_REG_14, fill=(110, 137, 133))
        return placeholder
    try:
        with Image.open(path) as raw:
            return ImageOps.fit(raw.convert("RGB"), size, method=Image.Resampling.LANCZOS)
    except Exception as exc:
        qa["errors"].append(f"图片无法读取：{slot} -> {exc}")
        return Image.new("RGB", size, (225, 235, 234))


def paste_rounded(canvas: Image.Image, media: Image.Image, box: tuple[int, int, int, int], radius: int = 9,
                  outline: tuple[int, int, int] | None = None) -> None:
    x0, y0, x1, y1 = box
    mask = Image.new("L", (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, x1 - x0, y1 - y0), radius=radius, fill=255)
    canvas.paste(media.resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS), (x0, y0), mask)
    if outline:
        ImageDraw.Draw(canvas).rounded_rectangle(box, radius=radius, outline=outline, width=1)


def badge(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    label = "AI 示意图"
    width = round(draw.textlength(label, font=F_MED_10)) + 12
    bx0, by0 = x1 - width - 7, y1 - 22
    draw.rounded_rectangle((bx0, by0, x1 - 7, y1 - 7), radius=4, fill=(26, 53, 50))
    draw.text((bx0 + 6, by0 + 3), label, font=F_MED_10, fill="white", anchor="lt")


def draw_pain_card(canvas: Image.Image, draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], item: dict,
                   qa: dict, index: int) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=9, fill=(238, 246, 245))
    draw.rounded_rectangle((x0, y0, x1, y0 + 30), radius=9, fill=(204, 220, 218))
    draw.rectangle((x0, y0 + 21, x1, y0 + 30), fill=(204, 220, 218))
    title = str(item.get("title", ""))
    tb = draw.textbbox((0, 0), title, font=F_SEMI_17)
    draw.text(((x0 + x1 - (tb[2] - tb[0])) / 2, y0 + 5), title, font=F_SEMI_17, fill=(104, 130, 127), anchor="lt")
    lines = wrap(draw, str(item.get("body", "")), F_REG_14, x1 - x0 - 34)
    draw_lines(draw, (x0 + 17, y0 + 39), lines, F_REG_14, (63, 69, 69), 21, 3, qa, f"pains[{index}].body")


def draw_value_card(canvas: Image.Image, draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], item: dict,
                    json_path: Path, qa: dict, index: int) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=9, fill=(246, 251, 250))
    media_box = (x0 + 12, y0 + 11, x0 + 157, y1 - 10)
    media_path, generated = resolve_media(json_path, item.get("image"))
    media = fit_media(media_path, (media_box[2] - media_box[0], media_box[3] - media_box[1]), qa, f"价值点 {index} 图片")
    paste_rounded(canvas, media, media_box, radius=8, outline=(82, 204, 186))
    if generated:
        badge(draw, media_box)
    tx = x0 + 170
    draw.text((tx, y0 + 11), "✓", font=font("MiSans-Semibold.ttf", 22), fill=(0, 169, 91), anchor="lt")
    title = str(item.get("title", ""))
    title_lines = wrap(draw, title, F_SEMI_17, x1 - tx - 12 - 24)
    draw_lines(draw, (tx + 23, y0 + 12), title_lines, F_SEMI_17, (0, 169, 91), 21, 2, qa, f"values[{index}].title")
    body_y = y0 + 12 + min(2, len(title_lines)) * 21 + 5
    body_lines = wrap(draw, str(item.get("body", "")), F_REG_14, x1 - tx - 12)
    available = max(1, (y1 - 10 - body_y) // 21)
    draw_lines(draw, (tx, body_y), body_lines, F_REG_14, (63, 69, 69), 21, available, qa, f"values[{index}].body")


def render(data: dict, json_path: Path, output: Path) -> dict:
    qa = {"canvas": f"{W}x{H}", "errors": [], "warnings": []}
    canvas = gradient((W, H), (238, 245, 245), (230, 239, 239))

    hero = Image.open(ASSETS / "hero-background.png").convert("RGB")
    hero = ImageOps.fit(hero, (W, 500), method=Image.Resampling.LANCZOS, centering=(0.5, 0.0)).crop((0, 0, W, 430))
    canvas.paste(Image.blend(canvas.crop((0, 0, W, 430)), hero, 0.86), (0, 0))
    fade = Image.new("RGBA", (W, 150), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fade)
    for y in range(150):
        alpha = round(255 * (y / 149) ** 1.5)
        fd.line((0, y, W, y), fill=(234, 242, 242, alpha))
    canvas.paste(fade, (0, 280), fade)

    logo = Image.open(ASSETS / "blacklake-xiaogongdan-logo.png").convert("RGB")
    lw = 142
    lh = round(logo.height * lw / logo.width)
    logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
    logo_bg = canvas.crop((64, 45, 64 + lw, 45 + lh))
    canvas.paste(ImageChops.multiply(logo_bg, logo), (64, 45))
    draw = ImageDraw.Draw(canvas)

    draw.text((84, 132), str(data.get("headline", "")), font=F_HEAVY_64, fill=(33, 31, 33), anchor="lt",
              stroke_width=0)
    subtitle = "、".join(str(x) for x in data.get("subtitle_clauses", []))
    draw.text((85, 234), subtitle, font=F_REG_28, fill=(38, 36, 38), anchor="lt")

    draw.rectangle((86, 286, 840, 412), fill=(239, 248, 247), outline=(87, 204, 188), width=1)
    draw.polygon([(86, 286), (192, 286), (203, 299), (192, 313), (86, 313)], fill=(8, 184, 156))
    draw.text((95, 289), "客户简介", font=F_MED_15, fill="white", anchor="lt")
    profile_lines = wrap(draw, str(data.get("profile", "")), F_REG_16, 714)
    draw_lines(draw, (106, 322), profile_lines, F_REG_16, (66, 73, 74), 25, 3, qa, "profile")

    def heading(y: int, symbol: str, label: str) -> None:
        draw.rectangle((86, y, 107, y + 25), outline=(8, 184, 156), width=2)
        sb = draw.textbbox((0, 0), symbol, font=F_MED_15)
        draw.text((96.5 - (sb[2] - sb[0]) / 2, y + 4), symbol, font=F_MED_15, fill=(8, 184, 156), anchor="lt")
        draw.text((117, y - 1), label, font=F_MED_28, fill=(41, 40, 42), anchor="lt")

    heading(434, "?", "需求痛点")
    pains = data.get("pains", [])
    pain_boxes = [(86, 475, 444, 589), (482, 475, 840, 589), (86, 605, 444, 719)]
    for index, (item, box) in enumerate(zip(pains, pain_boxes), 1):
        draw_pain_card(canvas, draw, box, item, qa, index)

    media = data.get("media", {}) if isinstance(data.get("media"), dict) else {}
    scene_path, scene_generated = resolve_media(json_path, media.get("scene_image"))
    scene_box = (482, 605, 840, 719)
    paste_rounded(canvas, fit_media(scene_path, (358, 114), qa, "客户或行业场景图"), scene_box, radius=9)
    if scene_generated:
        badge(draw, scene_box)

    heading(746, "≡", "方案及价值")
    values = data.get("values", [])
    value_boxes = [(86, 793, 444, 963), (482, 793, 840, 963), (86, 980, 444, 1150)]
    for index, (item, box) in enumerate(zip(values, value_boxes), 1):
        draw_value_card(canvas, draw, box, item, json_path, qa, index)

    result_path, result_generated = resolve_media(json_path, media.get("result_image"))
    result_box = (482, 980, 840, 1150)
    paste_rounded(canvas, fit_media(result_path, (358, 170), qa, "数据或管理场景图"), result_box, radius=9)
    if result_generated:
        badge(draw, result_box)

    wave = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wave)
    wd.arc((-80, 1150, 900, 1370), 190, 350, fill=(41, 174, 228, 125), width=16)
    wd.arc((-60, 1135, 920, 1355), 190, 350, fill=(83, 204, 234, 70), width=13)
    wd.arc((360, 1135, 1120, 1375), 190, 350, fill=(21, 191, 151, 120), width=18)
    wd.arc((340, 1118, 1110, 1358), 190, 350, fill=(82, 218, 180, 66), width=14)
    canvas.paste(wave, (0, 0), wave)

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG", optimize=True)
    qa["status"] = "failed" if qa["errors"] else "passed_with_warnings" if qa["warnings"] else "passed"
    report = output.with_name(output.stem + "_render-qa.json")
    report.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    return qa


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Path to case.json")
    parser.add_argument("--output", type=Path, required=True, help="Output PNG path")
    args = parser.parse_args()
    json_path = args.input.expanduser().resolve()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    qa = render(data, json_path, args.output.expanduser().resolve())
    print(json.dumps(qa, ensure_ascii=False, indent=2))
    raise SystemExit(1 if qa["errors"] else 0)


if __name__ == "__main__":
    main()
