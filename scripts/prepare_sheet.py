"""Deterministically pack reviewed sprite regions; requires Pillow.

This processes an existing generated sheet, not image generation or semantic repair.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


def prepare(source, contract, output):
    spec = json.loads(contract.read_text(encoding="utf-8"))
    image = Image.open(source).convert("RGBA")
    fw, fh = spec["frame_size"]
    ax, ay = spec["anchor"]
    if not (0 <= ax < fw and 0 <= ay < fh):
        raise ValueError("Anchor must be inside frame")
    if not spec["regions"]:
        raise ValueError("No regions")
    if output.exists():
        raise ValueError("Output directory already exists; choose a new version")
    frames, records = [], []
    threshold = spec.get("alpha_threshold")
    for region in spec["regions"]:
        x, y, w, h = region["rect"]
        if min(x, y) < 0 or min(w, h) <= 0 or x+w > image.width or y+h > image.height:
            raise ValueError("Region outside source")
        crop = image.crop((x, y, x+w, y+h))
        if threshold is not None:
            if not 1 <= threshold <= 255:
                raise ValueError("alpha_threshold must be 1..255")
            crop.putalpha(crop.getchannel("A").point(lambda a: 255 if a >= threshold else 0))
        bbox = crop.getchannel("A").getbbox()
        if bbox is None:
            raise ValueError("Empty region: " + region["id"])
        # One shared scale across the entire group; independent fitting distorts animation.
        scale = float(spec["scale"])
        if scale <= 0:
            raise ValueError("Scale must be positive")
        content = crop.crop(bbox)
        old_w, old_h = content.size
        content = content.resize((max(1, round(old_w*scale)), max(1, round(old_h*scale))), Image.Resampling.NEAREST)
        # A reviewed source pivot overrides bbox-bottom centering, e.g. jump animations.
        pivot = region.get("pivot", [(bbox[0]+bbox[2]-1)/2, bbox[3]-1])
        px = round((pivot[0]-bbox[0]+0.5)*content.width/old_w-0.5)
        py = round((pivot[1]-bbox[1]+0.5)*content.height/old_h-0.5)
        dx, dy = ax-px, ay-py
        if dx < 0 or dy < 0 or dx+content.width > fw or dy+content.height > fh:
            raise ValueError("Content would clip: " + region["id"])
        frame = Image.new("RGBA", (fw, fh))
        frame.paste(content, (dx, dy))
        frames.append(frame)
        records.append({"id": region["id"], "rect": region["rect"], "source_bbox": bbox, "pivot": pivot, "output_bbox": frame.getchannel("A").getbbox()})
    output.mkdir(parents=True)
    atlas = Image.new("RGBA", (fw*len(frames), fh))
    for i, frame in enumerate(frames):
        frame.save(output / f"frame_{i:04d}.png")
        atlas.paste(frame, (i*fw, 0))
    atlas.save(output / "sheet.png")
    preview = atlas.resize((atlas.width*4, atlas.height*4), Image.Resampling.NEAREST)
    preview.save(output / "preview.png")
    frames[0].save(output / "animation.gif", save_all=True, append_images=frames[1:], duration=spec.get("duration_ms", 160), loop=0, disposal=2)
    report = {"source": str(source.resolve()), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "contract": spec, "frames": records, "semantic_review": "required", "note": "GIF is preview only; RGBA PNG is authoritative"}
    (output / "processing.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    prepare(args.source, args.contract, args.output)
