"""Check this distributable skill and print a portable SHA-256 inventory."""
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.git', '__pycache__', '.venv', 'venv', 'local-reports', 'dist', 'build'}


def check(root=ROOT):
    root = Path(root).resolve()
    errors, inventory = [], {}
    required = ['SKILL.md', 'agents/openai.yaml', 'LICENSE', 'README.md',
                'requirements.txt', 'requirements-dev.txt', '.gitignore',
                'docs/setup.md', 'docs/provenance.md', 'docs/validation.md',
                'assets/farm-template/project.godot', 'tests/test_workflow.py',
                '.github/workflows/check.yml', 'docs/images/game-current.png',
                'docs/images/assets-current.png', 'examples/woodland-camp/README.md',
                'examples/woodland-camp/project.godot', 'examples/woodland-camp/main.gd',
                'examples/woodland-camp/main.tscn',
                'examples/woodland-camp/assets/qa-contract.json']
    for name in ('fox_spritesheet.png', 'hedgehog_spritesheet.png', 'props-atlas.png', 'props-layout.json'):
        required.append('examples/woodland-camp/assets/' + name)
    for name in ('fox-v2.pxo', 'hedgehog-v2.pxo', 'props-v3.pxo',
                 'characters-original.png', 'props-original.png'):
        required.append('examples/woodland-camp/source/' + name)
    for name in required:
        if not (root / name).is_file():
            errors.append('Missing required file: ' + name)

    def metadata(name, frontmatter=False):
        try:
            content = (root / name).read_text(encoding='utf-8')
            if frontmatter:
                match = re.match(r'^---\s*\n(.*?)\n---', content, re.S)
                content = match.group(1) if match else ''
            value = yaml.safe_load(content)
            if not isinstance(value, dict):
                raise ValueError('Expected a YAML mapping')
            return value
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append('Invalid metadata in ' + name + ': ' + str(exc))
            return {}

    meta = metadata('SKILL.md', frontmatter=True)
    if meta.get('name') != 'pixel-game-workflow' or not meta.get('description'):
        errors.append('Invalid skill frontmatter')
    ui = metadata('agents/openai.yaml').get('interface')
    if not isinstance(ui, dict) or not all(ui.get(key) for key in
               ('display_name', 'short_description', 'default_prompt')):
        errors.append('Incomplete UI metadata')
    for path in sorted(root.rglob('*')):
        rel = path.relative_to(root)
        if not path.is_file() or any(p in SKIP for p in rel.parts):
            continue
        if path.suffix in {'.pyc', '.log'} or '.godot' in rel.parts or path.name.startswith('.env'):
            errors.append('Local/generated file in release: ' + rel.as_posix())
        inventory[rel.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        if path.suffix.lower() in {'.md', '.py', '.json', '.gd', '.mjs', '.yaml', '.yml', '.txt'}:
            text = path.read_text(encoding='utf-8')
            # Drive-root and user-home paths should never be copied from a developer machine.
            if re.search(r'\b[A-Za-z]:[\\/](?![\\/])', text) or re.search(r'/home/[A-Za-z0-9_.-]+/', text):
                errors.append('Machine-specific absolute path: ' + rel.as_posix())
            if path.suffix == '.md':
                for link in re.findall(r'\]\(([^)]+)\)', text):
                    target = link.split('#', 1)[0]
                    if not target or '://' in target or target.startswith('mailto:'):
                        continue
                    destination = (path.parent / unquote(target)).resolve()
                    if not destination.is_relative_to(root) or not destination.exists():
                        errors.append(f'Broken local link in {rel.as_posix()}: {link}')
    return {'status': 'fail' if errors else 'pass', 'scope': 'release_structure_only',
            'errors': errors, 'files': inventory}


if __name__ == '__main__':
    result = check()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(1 if result['errors'] else 0)
