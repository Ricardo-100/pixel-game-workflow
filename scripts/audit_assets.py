"""Read-only sprite QA from an explicit contract; requires Python 3.10+ and Pillow."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

from PIL import Image, ImageColor, ImageDraw


def pixel_data(image):
    # Pillow 12.1+ renamed getdata; retain compatibility with older project environments.
    return image.get_flattened_data() if hasattr(image, "get_flattened_data") else image.getdata()


def positive(value):
    if type(value) is not int or value <= 0:
        raise ValueError("Expected a positive integer")
    return value


def pair(value):
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError("Expected [width, height]")
    return tuple(positive(v) for v in value)


def local_file(root, value):
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError("Asset/source paths must be project-relative")
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Asset/source path escapes project root")
    return path


def inspect_asset(root, spec):
    result = {"id": spec.get("id"), "errors": [], "warnings": [], "animations": []}
    errors, warnings = result["errors"], result["warnings"]
    path = local_file(root, spec["path"])
    result["path"] = str(path)
    result["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    if spec.get("source"):
        source = local_file(root, spec["source"])
        if not source.is_file():
            errors.append("Editable source is missing")
        else:
            result["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    with Image.open(path) as original:
        alpha_channel = "A" in original.getbands() or "transparency" in original.info
        image = original.convert("RGBA")
    result["size"] = list(image.size)
    if image.size != pair(spec["size"]):
        errors.append("Image size does not match contract")
    pixels = list(pixel_data(image))
    visible = [p for p in pixels if p[3] > 0]
    colors = set(visible)
    result["visible_colors"] = len(colors)
    result["bbox"] = image.getchannel("A").getbbox()
    if not visible:
        errors.append("Image is fully transparent")
    alpha = spec.get("alpha", "any")
    if alpha not in ("any", "transparent", "binary", "opaque"):
        raise ValueError("alpha must be any, transparent, binary or opaque")
    if alpha in ("transparent", "binary") and (not alpha_channel or not any(p[3] == 0 for p in pixels)):
        errors.append("Expected an alpha channel with transparent pixels")
    if alpha == "binary" and any(p[3] not in (0, 255) for p in pixels):
        errors.append("Partial alpha violates binary transparency")
    if alpha == "opaque" and any(p[3] != 255 for p in pixels):
        errors.append("Expected opaque pixels")
    if "max_colors" in spec and len(colors) > positive(spec["max_colors"]):
        errors.append("Visible RGBA color count exceeds contract")
    if "palette" in spec:
        allowed = {ImageColor.getcolor(c, "RGBA") for c in spec["palette"]}
        outside = colors - allowed
        result["off_palette_colors"] = len(outside)
        if outside:
            errors.append("Visible colors outside declared RGBA palette")
    fw, fh = pair(spec.get("frame_size", spec["size"]))
    if image.width % fw or image.height % fh:
        errors.append("Atlas is not divisible by frame size; padding/gutters need explicit preprocessing")
    columns, rows = image.width // fw, image.height // fh
    frames = [image.crop((x * fw, y * fh, (x + 1) * fw, (y + 1) * fh))
              for y in range(rows) for x in range(columns)]
    for animation in spec.get("animations", []):
        name, indices = animation["name"], animation["frames"]
        if not isinstance(indices, list) or not indices:
            raise ValueError("Animation frames must be a nonempty index list")
        if any(type(i) is not int or i < 0 or i >= len(frames) for i in indices):
            errors.append(f"{name}: frame index outside atlas")
            continue
        durations = animation["durations_ms"]
        if not isinstance(durations, list) or len(durations) != len(indices):
            raise ValueError("durations_ms must match animation frame count")
        for duration in durations:
            positive(duration)
        if type(animation["loop"]) is not bool:
            raise ValueError("loop must be boolean")
        selected = [frames[i] for i in indices]
        # Ignore RGB hidden under alpha=0 when comparing visible poses.
        canonical = [bytes(channel for p in pixel_data(frame) for channel in (p if p[3] else (0, 0, 0, 0)))
                     for frame in selected]
        bounds = [frame.getchannel("A").getbbox() for frame in selected]
        bottoms = [b[3] - 1 for b in bounds if b]
        duplicate_pairs = [[i - 1, i] for i in range(1, len(indices)) if canonical[i - 1] == canonical[i]]
        details = {"name": name, "frames": indices, "durations_ms": durations,
                   "loop": animation["loop"], "empty_frames": [i for i, b in enumerate(bounds) if not b],
                   "identical_adjacent_positions": duplicate_pairs,
                   "bottom_span_px": max(bottoms) - min(bottoms) if bottoms else None,
                   "same_first_last": len(indices) > 1 and canonical[0] == canonical[-1],
                   "border_touch_positions": [i for i, b in enumerate(bounds)
                                              if b and (b[0] == 0 or b[1] == 0 or b[2] == fw or b[3] == fh)]}
        if details["empty_frames"]:
            errors.append(f"{name}: empty animation frames")
        if duplicate_pairs:
            warnings.append(f"{name}: adjacent identical poses; inspect intentional holds")
        if animation["loop"] and details["same_first_last"]:
            warnings.append(f"{name}: repeated wrap pose; inspect loop pause")
        if details["border_touch_positions"]:
            warnings.append(f"{name}: content touches frame edge; inspect clipping")
        if "max_bottom_span_px" in animation:
            tolerance = animation["max_bottom_span_px"]
            if type(tolerance) is not int or tolerance < 0:
                raise ValueError("max_bottom_span_px must be a nonnegative integer")
            if details["bottom_span_px"] is not None and details["bottom_span_px"] > tolerance:
                warnings.append(f"{name}: visible bottom varies beyond declared review tolerance")
        result["animations"].append(details)
    # Native-size contact sheet: preview rendering is explicitly separate from game assets.
    used = sorted({i for a in result["animations"] for i in a["frames"]}) or list(range(len(frames)))
    preview_columns = min(8, max(1, len(used)))
    sheet = Image.new("RGB", (preview_columns * (fw + 4), math.ceil(max(1, len(used)) / preview_columns) * (fh + 16)), "#20232b")
    draw = ImageDraw.Draw(sheet)
    for n, index in enumerate(used):
        x, y = n % preview_columns * (fw + 4), n // preview_columns * (fh + 16)
        for cy in range(0, fh, 4):
            for cx in range(0, fw, 4):
                draw.rectangle((x + cx, y + cy, x + min(cx + 3, fw - 1), y + min(cy + 3, fh - 1)),
                               fill="#757575" if (cx // 4 + cy // 4) % 2 else "#aaaaaa")
        sheet.paste(frames[index], (x, y), frames[index])
        draw.text((x, y + fh), str(index), fill="white")
    result["status"] = "fail" if errors else "review" if warnings else "pass"
    return result, sheet


def audit(root, contract):
    root = Path(root).resolve()
    if not isinstance(contract, dict) or contract.get("schema_version") != 1 or not isinstance(contract.get("assets"), list) or not contract["assets"]:
        raise ValueError("Expected schema_version=1 and a nonempty assets list")
    results, previews, ids = [], {}, set()
    for spec in contract["assets"]:
        if not isinstance(spec, dict):
            raise ValueError("Each asset must be an object")
        identity = spec.get("id")
        if not isinstance(identity, str) or not identity or identity in ids:
            raise ValueError("Asset IDs must be unique nonempty strings")
        ids.add(identity)
        try:
            result, sheet = inspect_asset(root, spec)
            previews[len(results)] = sheet
        except (ValueError, OSError, KeyError, TypeError) as exc:
            result = {"id": identity, "status": "fail", "errors": [str(exc)], "warnings": []}
        results.append(result)
    report = {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
              "project_root": str(root), "scope": "static_asset_checks_only",
              "status": "fail" if any(r["status"] == "fail" for r in results)
                        else "review" if any(r["status"] == "review" for r in results) else "pass",
              "visual_status": "unverified", "runtime_status": "unverified", "assets": results}
    return report, previews


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path, help="New report directory; refuses overwrite")
    args = parser.parse_args()
    try:
        # Resolve every read before creating output; output cannot replace game files.
        raw = args.contract.read_bytes()
        report, previews = audit(args.root, json.loads(raw.decode("utf-8-sig")))
        report["contract_sha256"] = hashlib.sha256(raw).hexdigest()
        args.out.mkdir(parents=True, exist_ok=False)
        for index, sheet in previews.items():
            name = f"asset-{index:03d}-contact.png"
            sheet.save(args.out / name)
            report["assets"][index]["preview"] = name
        (args.out / "asset-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"status": report["status"], "report": str((args.out / "asset-audit.json").resolve())}, ensure_ascii=False))
        return 1 if report["status"] == "fail" else 0
    except (ValueError, OSError, TypeError) as exc:
        print("Asset audit failed: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
