"""Second reviewed palette: reserve berry-blue accents; keep 48 colors total."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
NAMES = ('fox', 'hedgehog', 'tree', 'tent', 'fire', 'bush', 'rock', 'sign')


def requantize(root=ROOT):
    root = Path(root)
    outputs = [root / 'processed' / name / 'limited-v2.png' for name in NAMES]
    atlas_path = root / 'processed/props-atlas-v2.png'
    if any(path.exists() for path in [*outputs, atlas_path]):
        raise ValueError('v2 output exists; use a fresh copy to preserve prior processing')
    images, pixels, blue = [], [], []
    for name in NAMES:
        with Image.open(root / 'processed' / name / 'sheet.png') as source:
            image = source.convert('RGBA')
        images.append(image)
        data = image.get_flattened_data() if hasattr(image, 'get_flattened_data') else image.getdata()
        visible = [p[:3] for p in data if p[3] > 0]
        if not visible:
            raise ValueError('Empty processed sheet: ' + name)
        pixels.extend(visible * max(1, 12000 // len(visible)))
        blue.extend([p for p in visible if p[2] > p[0]+10 and p[2] > p[1]+5])
    if sum(im.width for im in images[2:]) != 440 or any(im.height > 128 for im in images[2:]):
        raise ValueError('Prop sheets do not fit the declared 440x128 atlas')
    pixels.extend(blue * 20)
    sample = Image.new('RGB', (len(pixels), 1))
    sample.putdata(pixels)
    palette = sample.quantize(colors=48, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    reduced_images = []
    for im in images:
        reduced = im.convert('RGB').quantize(palette=palette, dither=Image.Dither.NONE).convert('RGBA')
        reduced.putalpha(im.getchannel('A'))
        reduced_images.append(reduced)
    atlas = Image.new('RGBA', (440, 128))
    x = 0
    for im in reduced_images[2:]:
        atlas.paste(im, (x, 0))
        x += im.width
    for path, im in zip(outputs, reduced_images):
        im.save(path)
    atlas.save(atlas_path)
    return len(blue)


if __name__ == '__main__':
    try:
        print('Palette v2 written; berry blue pixels:', requantize())
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc))
