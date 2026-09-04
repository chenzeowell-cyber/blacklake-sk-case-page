#!/usr/bin/env python3
"""Build a fixed-layout Black Lake SK customer case page from JSON."""

from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
ASSET_DIR = SKILL_DIR / "assets"
TEMPLATE = ASSET_DIR / "template.html"


def text(value: object) -> str:
    return html.escape(str(value or "").strip(), quote=True)


def display_len(value: object) -> int:
    return len(str(value or "").replace("\n", "").strip())


def add_limit(qa: dict, field: str, value: object, minimum: int, maximum: int) -> None:
    size = display_len(value)
    if size > maximum:
        qa["errors"].append(f"{field} 共 {size} 字，超过上限 {maximum} 字")
    elif size < minimum:
        qa["warnings"].append(f"{field} 仅 {size} 字，建议至少 {minimum} 字")


def normalize_media(value: object) -> dict:
    if isinstance(value, str):
        return {"path": value, "ai_generated": False}
    if isinstance(value, dict):
        return {"path": str(value.get("path", "")).strip(), "ai_generated": bool(value.get("ai_generated", False))}
    return {"path": "", "ai_generated": False}


def copy_media(spec: dict, json_dir: Path, media_dir: Path, slot: str, qa: dict) -> tuple[str, bool]:
    source_value = spec.get("path", "")
    if not source_value:
        qa["errors"].append(f"缺少图片：{slot}")
        return "", bool(spec.get("ai_generated"))
    source = Path(source_value).expanduser()
    if not source.is_absolute():
        source = (json_dir / source).resolve()
    if not source.is_file():
        qa["errors"].append(f"图片不存在：{slot} -> {source}")
        return "", bool(spec.get("ai_generated"))
    suffix = source.suffix.lower() or ".png"
    destination = media_dir / f"{slot}{suffix}"
    shutil.copy2(source, destination)
    return f"media/{destination.name}", bool(spec.get("ai_generated"))


def media_html(path: str, ai_generated: bool, css_class: str, alt: str) -> str:
    badge = '<span class="media-badge">AI 示意图</span>' if ai_generated else ""
    if path:
        return f'<div class="{css_class}"><img src="{text(path)}" alt="{text(alt)}">{badge}</div>'
    return f'<div class="{css_class} placeholder">请补充{html.escape(alt)}</div>'


def build(data: dict, json_path: Path, output_dir: Path) -> dict:
    qa = {"canvas": "910x1236", "font_family": "MiSans", "errors": [], "warnings": []}
    output_dir.mkdir(parents=True, exist_ok=True)
    output_assets = output_dir / "assets"
    output_media = output_dir / "media"
    output_assets.mkdir(exist_ok=True)
    output_media.mkdir(exist_ok=True)

    for item in ["blacklake-xiaogongdan-logo.png", "hero-background.png"]:
        shutil.copy2(ASSET_DIR / item, output_assets / item)
    shutil.copytree(ASSET_DIR / "fonts", output_assets / "fonts", dirs_exist_ok=True)

    for key in ["client_name", "headline", "profile"]:
        if not str(data.get(key, "")).strip():
            qa["errors"].append(f"缺少必填字段：{key}")

    subtitle = data.get("subtitle_clauses", [])
    pains = data.get("pains", [])
    values = data.get("values", [])
    if not isinstance(subtitle, list) or len(subtitle) != 3:
        qa["errors"].append("subtitle_clauses 必须恰好包含 3 项")
        subtitle = list(subtitle)[:3] if isinstance(subtitle, list) else []
    if not isinstance(pains, list) or len(pains) != 3:
        qa["errors"].append("pains 必须恰好包含 3 项")
        pains = list(pains)[:3] if isinstance(pains, list) else []
    if not isinstance(values, list) or len(values) != 3:
        qa["errors"].append("values 必须恰好包含 3 项")
        values = list(values)[:3] if isinstance(values, list) else []

    while len(subtitle) < 3:
        subtitle.append("待补充")
    while len(pains) < 3:
        pains.append({"title": "待补充", "body": "待补充"})
    while len(values) < 3:
        values.append({"title": "待补充", "body": "待补充", "image": {}})

    add_limit(qa, "headline", data.get("headline"), 8, 12)
    add_limit(qa, "profile", data.get("profile"), 45, 105)
    for index, clause in enumerate(subtitle, 1):
        add_limit(qa, f"subtitle_clauses[{index}]", clause, 4, 12)
    add_limit(qa, "subtitle_clauses 整行", "、".join(str(item) for item in subtitle), 14, 27)
    for index, item in enumerate(pains, 1):
        add_limit(qa, f"pains[{index}].title", item.get("title"), 6, 16)
        add_limit(qa, f"pains[{index}].body", item.get("body"), 35, 78)
    for index, item in enumerate(values, 1):
        add_limit(qa, f"values[{index}].title", item.get("title"), 6, 16)
        add_limit(qa, f"values[{index}].body", item.get("body"), 35, 60)

    if not data.get("sources"):
        qa["warnings"].append("未记录 sources；正式发布前建议补充事实来源")

    pain_cards = [f'<article class="pain-card"><h3>{text(item.get("title"))}</h3><p>{text(item.get("body"))}</p></article>' for item in pains]

    value_cards = []
    for index, item in enumerate(values, 1):
        spec = normalize_media(item.get("image"))
        media_path, ai_generated = copy_media(spec, json_path.parent, output_media, f"value-{index:02d}", qa)
        badge = '<span class="media-badge">AI 示意图</span>' if ai_generated else ""
        if media_path:
            visual = f'<div class="value-media"><img src="{text(media_path)}" alt="价值点 {index} 产品截图">{badge}</div>'
        else:
            visual = '<div class="value-media placeholder">请补充产品截图</div>'
        value_cards.append(f'<article class="value-card">{visual}<div class="value-copy"><h3>{text(item.get("title"))}</h3><p>{text(item.get("body"))}</p></div></article>')

    media = data.get("media", {}) if isinstance(data.get("media"), dict) else {}
    scene_path, scene_ai = copy_media(normalize_media(media.get("scene_image")), json_path.parent, output_media, "scene", qa)
    result_path, result_ai = copy_media(normalize_media(media.get("result_image")), json_path.parent, output_media, "result", qa)

    replacements = {
        "{{PAGE_TITLE}}": text(f'{data.get("client_name", "客户")} SK 案例页'),
        "{{HEADLINE}}": text(data.get("headline")),
        "{{SUBTITLE}}": "、".join(text(item) for item in subtitle),
        "{{PROFILE}}": text(data.get("profile")),
        "{{PAIN_CARDS}}": "".join(pain_cards),
        "{{SCENE_MEDIA}}": media_html(scene_path, scene_ai, "scene-card", "客户或行业场景图"),
        "{{VALUE_CARDS}}": "".join(value_cards),
        "{{RESULT_MEDIA}}": media_html(result_path, result_ai, "result-card", "数据或管理场景图"),
    }
    rendered = TEMPLATE.read_text(encoding="utf-8")
    for key, value in replacements.items():
        rendered = rendered.replace(key, value)
    (output_dir / "index.html").write_text(rendered, encoding="utf-8")
    (output_dir / "case.normalized.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    qa["status"] = "failed" if qa["errors"] else "passed_with_warnings" if qa["warnings"] else "passed"
    (output_dir / "qa-report.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    return qa


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Path to case.json")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory")
    args = parser.parse_args()
    input_path = args.input.expanduser().resolve()
    data = json.loads(input_path.read_text(encoding="utf-8"))
    qa = build(data, input_path, args.output_dir.expanduser().resolve())
    print(json.dumps(qa, ensure_ascii=False, indent=2))
    raise SystemExit(1 if qa["errors"] else 0)


if __name__ == "__main__":
    main()
