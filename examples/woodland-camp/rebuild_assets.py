"""Pack the saved candidates with reviewed slicing contracts; refuses overwrite."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL = ROOT.parents[1]
spec = importlib.util.spec_from_file_location('prepare_sheet', SKILL / 'scripts/prepare_sheet.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

if __name__ == '__main__':
    if (ROOT / 'processed').exists():
        raise SystemExit('processed already exists; preserve it and use a fresh copy of this example')
    for name in ('fox', 'hedgehog', 'tree', 'tent', 'fire', 'bush', 'rock', 'sign'):
        original = 'characters-original.png' if name in ('fox', 'hedgehog') else 'props-original.png'
        module.prepare(ROOT / 'source' / original, ROOT / 'source' / (name+'-slicing.json'),
                       ROOT / 'processed' / name)
    print('Packed 8 groups. Run requantize.py, then import the reviewed outputs in Pixelorama.')
