"""Portable regression checks; no editors, network, or image generation needed."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bootstrap = load('bootstrap')
pack = load('prepare_sheet')
qa = load('audit_assets')
release = load('check_release')
example_spec = importlib.util.spec_from_file_location('requantize', ROOT / 'examples/woodland-camp/requantize.py')
example = importlib.util.module_from_spec(example_spec)
example_spec.loader.exec_module(example)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_standalone_bootstrap_preserves_template_and_honest_status(self):
        out = self.root / '农场 demo'
        result = bootstrap.create_project(out, '农场 "Demo"', None, None)
        self.assertEqual(result['status'], 'created_not_run')
        self.assertFalse(result['godot_ai_enabled'])
        config = (out / 'project.godot').read_text(encoding='utf-8')
        self.assertIn('config/name=' + json.dumps('农场 "Demo"', ensure_ascii=False), config)
        self.assertNotIn('[autoload]', config)
        for name in ('farmer.png', 'environment.png'):
            self.assertEqual((out / 'assets' / name).read_bytes(),
                             (ROOT / 'assets/farm-template/assets' / name).read_bytes())
        report, _ = qa.audit(out, json.loads((out / 'assets/qa-contract.json').read_text(encoding='utf-8')))
        self.assertNotEqual(report['status'], 'fail')
        self.assertEqual(report['runtime_status'], 'unverified')

    def test_bootstrap_refuses_nonempty_destination_without_changes(self):
        out = self.root / 'existing'
        out.mkdir()
        sentinel = out / 'save.txt'
        sentinel.write_bytes(b'keep my progress')
        with self.assertRaises(ValueError):
            bootstrap.create_project(out, 'Demo', None, None)
        self.assertEqual(list(out.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_bytes(), b'keep my progress')

    def test_invalid_addon_does_not_create_destination(self):
        out = self.root / 'new'
        with self.assertRaises(ValueError):
            bootstrap.create_project(out, 'Demo', None, self.root / 'missing-addon')
        self.assertFalse(out.exists())

    def test_bootstrap_addon_configuration_and_copy(self):
        addon = self.root / 'addon'
        for name in ('plugin.cfg', 'plugin.gd', 'runtime/game_helper.gd'):
            path = addon / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('# fixture', encoding='utf-8')
        out = self.root / 'with-addon'
        result = bootstrap.create_project(out, 'Demo', None, addon)
        self.assertTrue(result['godot_ai_enabled'])
        self.assertEqual((out / 'addons/godot_ai/plugin.cfg').read_bytes(), b'# fixture')
        config = (out / 'project.godot').read_text(encoding='utf-8')
        self.assertIn('_mcp_game_helper="*res://addons/godot_ai/runtime/game_helper.gd"', config)
        self.assertIn('enabled=PackedStringArray("res://addons/godot_ai/plugin.cfg")', config)

    def fixture_sheet(self):
        source = self.root / 'candidate.png'
        image = Image.new('RGBA', (16, 8))
        for x in (2, 3, 10, 11):
            for y in (2, 3, 4):
                image.putpixel((x, y), (50, 100, 150, 128))
        image.save(source)
        spec = {'frame_size': [8, 8], 'anchor': [4, 6], 'scale': 1,
                'regions': [{'id': 'a', 'rect': [0, 0, 8, 8]},
                            {'id': 'b', 'rect': [8, 0, 8, 8]}]}
        return source, spec

    def prepare(self, source, spec, folder='processed'):
        contract = self.root / 'slicing.json'
        contract.write_text(json.dumps(spec), encoding='utf-8')
        return pack.prepare(source, contract, self.root / folder)

    def test_sheet_preserves_alpha_and_aligns_bottom(self):
        source, spec = self.fixture_sheet()
        report = self.prepare(source, spec)
        self.assertEqual(len(report['frames']), 2)
        with Image.open(self.root / 'processed/sheet.png') as sheet:
            self.assertEqual(sheet.size, (16, 8))
            self.assertEqual(set(qa.pixel_data(sheet.getchannel('A'))), {0, 128})
        for record in report['frames']:
            self.assertEqual(record['output_bbox'][3], 7)

    def test_sheet_refuses_overwrite(self):
        source, spec = self.fixture_sheet()
        self.prepare(source, spec)
        before = (self.root / 'processed/sheet.png').read_bytes()
        with self.assertRaises(ValueError):
            self.prepare(source, spec)
        self.assertEqual((self.root / 'processed/sheet.png').read_bytes(), before)

    def test_sheet_rejects_outside_empty_and_clipped_regions(self):
        source, spec = self.fixture_sheet()
        invalid = []
        outside = copy.deepcopy(spec)
        outside['regions'][0]['rect'] = [15, 0, 8, 8]
        invalid.append(outside)
        empty = copy.deepcopy(spec)
        empty['regions'][0]['rect'] = [0, 0, 1, 1]
        invalid.append(empty)
        clipped = copy.deepcopy(spec)
        clipped['scale'] = 10
        invalid.append(clipped)
        for index, contract in enumerate(invalid):
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.prepare(source, contract, str(index))
            self.assertFalse((self.root / str(index)).exists())

    def test_asset_audit_reports_size_failure(self):
        source, _ = self.fixture_sheet()
        spec = {'schema_version': 1, 'assets': [{'id': 'candidate', 'path': source.name,
                                              'size': [99, 99]}]}
        report, _ = qa.audit(self.root, spec)
        self.assertEqual(report['status'], 'fail')
        self.assertTrue(report['assets'][0]['errors'])

    def test_asset_audit_refuses_path_escape(self):
        spec = {'schema_version': 1, 'assets': [{'id': 'escape', 'path': '../outside.png',
                                              'size': [8, 8]}]}
        report, _ = qa.audit(self.root, spec)
        self.assertEqual(report['status'], 'fail')
        self.assertIn('escapes project root', report['assets'][0]['errors'][0])

    def test_palette_refuses_every_existing_output_before_reading_inputs(self):
        targets = [Path('processed') / name / 'limited-v2.png' for name in example.NAMES]
        targets.append(Path('processed/props-atlas-v2.png'))
        for index, relative in enumerate(targets):
            with self.subTest(path=str(relative)):
                root = self.root / str(index)
                sentinel = root / relative
                sentinel.parent.mkdir(parents=True)
                sentinel.write_bytes(b'keep reviewed art')
                with self.assertRaisesRegex(ValueError, 'v2 output exists'):
                    example.requantize(root)
                self.assertEqual(sentinel.read_bytes(), b'keep reviewed art')
                self.assertEqual([p for p in root.rglob('*') if p.is_file()], [sentinel])

    def test_release_reports_missing_metadata_without_crashing(self):
        report = release.check(self.root)
        self.assertEqual(report['status'], 'fail')
        self.assertTrue(any('Missing required file: SKILL.md' in e for e in report['errors']))

    def test_release_reports_malformed_metadata_without_crashing(self):
        (self.root / 'agents').mkdir()
        for content in ('interface: [invalid]', 'interface: [', ''):
            with self.subTest(content=content):
                (self.root / 'agents/openai.yaml').write_text(content, encoding='utf-8')
                (self.root / 'SKILL.md').write_text('---\n[]\n---\n', encoding='utf-8')
                report = release.check(self.root)
                self.assertEqual(report['status'], 'fail')
                self.assertIn('Incomplete UI metadata', report['errors'])


if __name__ == '__main__':
    unittest.main()
