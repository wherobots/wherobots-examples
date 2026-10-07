import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


AUDIT = Path(__file__).parent
UPDATER = Path(os.environ.get('UPDATER_PATH', str(AUDIT.parent / 'update_docs_navigation.py')))
EXAMPLES = json.loads((AUDIT / 'fixtures/examples.json').read_text())
LEGACY = json.loads((AUDIT / 'fixtures/legacy.json').read_text())


def tab(config, name):
    return next(t for t in config['navigation']['tabs'] if t['tab'] == name)


def group(pages, *names):
    for name in names:
        pages = next(p for p in pages if isinstance(p, dict) and p.get('group') == name)['pages']
    return pages


def paths(pages):
    result = []
    for item in pages:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            if 'root' in item:
                result.append(item['root'])
            result.extend(paths(item.get('pages', [])))
    return result


def shared_sidebar():
    config = copy.deepcopy(EXAMPLES)
    sections = []
    for item in config['navigation'].pop('tabs'):
        if item['tab'] == 'Examples':
            section = item['pages'][0]
        else:
            section = {'group': item['tab'], 'root': item['pages'][0], 'pages': item['pages'][1:]}
        section['expanded'] = False
        sections.append(section)
    config['navigation']['groups'] = [{'group': 'Documentation', 'root': 'index', 'pages': sections}]
    return config


NOTEBOOK_NAMES = {Path(p).name for p in paths(tab(EXAMPLES, 'Examples')['pages']) if p.startswith('tutorials/example-notebooks/')}


class NavigationSyncTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config_file = self.root / 'docs.json'
        self.notebooks = self.root / 'notebooks'
        self.notebooks.mkdir()

    def run_script(self, config, names=NOTEBOOK_NAMES):
        self.config_file.write_text(json.dumps(config, indent=2) + '\n')
        for name in names:
            (self.notebooks / (name + '.mdx')).write_text('---\ntitle: Example\n---\n')
        before = self.config_file.read_bytes()
        result = subprocess.run([sys.executable, str(UPDATER), '--docs-json', str(self.config_file), '--notebooks-dir', str(self.notebooks)], capture_output=True, text=True)
        return result, json.loads(self.config_file.read_text()), before

    def test_examples_restores_notebooks_to_each_current_chapter(self):
        config = copy.deepcopy(EXAMPLES)
        pages = group(tab(config, 'Examples')['pages'], 'Examples')
        cases = [
            ('part-4-spatial-joins', ('Beginner learning path',)),
            ('pmtiles-railroad', ('Spatial SQL and visualization',)),
            ('stac-reader', ('Data sources',)),
            ('rasterflow-sam3', ('Raster imagery',)),
            ('gps-map-matching', ('Statistics and routing',)),
            ('clustering-dbscan', ('Statistics and routing', 'Spatial Statistics')),
        ]
        for name, route in cases:
            group(pages, *route).remove('tutorials/example-notebooks/' + name)
        result, actual, _ = self.run_script(config)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        actual_pages = group(tab(actual, 'Examples')['pages'], 'Examples')
        for name, route in cases:
            with self.subTest(notebook=name):
                self.assertIn('tutorials/example-notebooks/' + name, group(actual_pages, *route))

    def test_removes_stale_notebook_in_unmapped_branch_preserving_everything_else(self):
        config = copy.deepcopy(EXAMPLES)
        group(tab(config, 'Examples')['pages'], 'Examples', 'Use Cases').append('tutorials/example-notebooks/removed-notebook')
        result, actual, _ = self.run_script(config)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(actual, EXAMPLES)

    def test_legacy_current_geostats_name_and_sam3_are_supported(self):
        config = copy.deepcopy(LEGACY)
        pages = tab(config, 'Spatial Analytics Tutorials')['pages']
        group(pages, 'GeoStats & Map Matching', 'Spatial Statistics').remove('tutorials/example-notebooks/clustering-dbscan')
        group(pages, 'GeoStats & Map Matching').remove('tutorials/example-notebooks/gps-map-matching')
        group(pages, 'RasterFlow').remove('tutorials/example-notebooks/rasterflow-sam3')
        result, actual, _ = self.run_script(config)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        pages = tab(actual, 'Spatial Analytics Tutorials')['pages']
        self.assertIn('tutorials/example-notebooks/clustering-dbscan', group(pages, 'GeoStats & Map Matching', 'Spatial Statistics'))
        self.assertIn('tutorials/example-notebooks/gps-map-matching', group(pages, 'GeoStats & Map Matching'))
        self.assertIn('tutorials/example-notebooks/rasterflow-sam3', group(pages, 'RasterFlow'))

    def test_older_wherobotsai_group_alias_remains_supported(self):
        config = copy.deepcopy(LEGACY)
        pages = tab(config, 'Spatial Analytics Tutorials')['pages']
        next(p for p in pages if isinstance(p, dict) and p.get('group') == 'GeoStats & Map Matching')['group'] = 'WherobotsAI'
        group(pages, 'WherobotsAI', 'Spatial Statistics').remove('tutorials/example-notebooks/clustering-dbscan')
        result, actual, _ = self.run_script(config)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('tutorials/example-notebooks/clustering-dbscan', group(tab(actual, 'Spatial Analytics Tutorials')['pages'], 'WherobotsAI', 'Spatial Statistics'))

    def test_unknown_layout_fails_nonzero_without_writing(self):
        config = {'navigation': {'tabs': [{'tab': 'Unsupported', 'pages': ['index']}]}}
        result, actual, before = self.run_script(config)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.config_file.read_bytes(), before)

    def test_missing_required_chapter_fails_nonzero_without_partial_writes(self):
        config = copy.deepcopy(EXAMPLES)
        pages = group(tab(config, 'Examples')['pages'], 'Examples')
        pages[:] = [p for p in pages if not isinstance(p, dict) or p.get('group') != 'Raster imagery']
        result, actual, before = self.run_script(config)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.config_file.read_bytes(), before)

    def test_unmapped_new_notebook_fails_nonzero_without_writing(self):
        result, actual, before = self.run_script(EXAMPLES, NOTEBOOK_NAMES | {'unmapped-new-notebook'})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.config_file.read_bytes(), before)

    def test_empty_discovery_fails_nonzero_without_removing_notebooks(self):
        result, actual, before = self.run_script(EXAMPLES, set())
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(actual, EXAMPLES)
        self.assertEqual(self.config_file.read_bytes(), before)

    def test_full_current_inventory_is_idempotent_and_preserves_collapsed_state(self):
        result, actual, before = self.run_script(EXAMPLES)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('Error:', result.stdout)
        self.assertEqual(actual, EXAMPLES)
        self.assertEqual(self.config_file.read_bytes(), before)

    def test_shared_sidebar_restores_notebooks_using_stable_root(self):
        config = shared_sidebar()
        sections = config['navigation']['groups'][0]['pages']
        examples = next(p for p in sections if p.get('root') == 'tutorials/index')
        examples['group'] = 'Worked examples'
        cases = [
            ('part-4-spatial-joins', ('Beginner learning path',)),
            ('pmtiles-railroad', ('Spatial SQL and visualization',)),
            ('overture-maps', ('Data sources',)),
            ('rasterflow-sam3', ('Raster imagery',)),
            ('isochrones', ('Statistics and routing',)),
            ('clustering-dbscan', ('Statistics and routing', 'Spatial Statistics')),
        ]
        for name, route in cases:
            group(examples['pages'], *route).remove('tutorials/example-notebooks/' + name)
        expected = copy.deepcopy(config)
        expected_examples = next(p for p in expected['navigation']['groups'][0]['pages'] if p.get('root') == 'tutorials/index')
        for name, route in cases:
            group(expected_examples['pages'], *route).append('tutorials/example-notebooks/' + name)
        result, actual, _ = self.run_script(config)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(actual, expected)

    def test_shared_sidebar_removes_stale_notebook_preserving_manual_pages_and_metadata(self):
        expected = shared_sidebar()
        config = copy.deepcopy(expected)
        group(config['navigation']['groups'], 'Documentation', 'Examples', 'Use Cases').append('tutorials/example-notebooks/removed-notebook')
        result, actual, _ = self.run_script(config)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(actual, expected)

    def test_shared_sidebar_is_idempotent(self):
        config = shared_sidebar()
        result, actual, before = self.run_script(config)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(actual, config)
        self.assertEqual(self.config_file.read_bytes(), before)
        result, actual, before = self.run_script(actual)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(actual, config)
        self.assertEqual(self.config_file.read_bytes(), before)

    def test_shared_sidebar_missing_root_fails_nonzero_without_writing(self):
        config = shared_sidebar()
        examples = next(p for p in config['navigation']['groups'][0]['pages'] if p.get('root') == 'tutorials/index')
        examples['root'] = 'tutorials/unsupported'
        result, actual, before = self.run_script(config)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.config_file.read_bytes(), before)

    def test_multiple_shared_sidebar_roots_fail_nonzero_without_writing(self):
        config = shared_sidebar()
        config['navigation']['groups'].append({'group': 'Other wrapper', 'pages': [copy.deepcopy(next(p for p in config['navigation']['groups'][0]['pages'] if p.get('root') == 'tutorials/index'))]})
        result, actual, before = self.run_script(config)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.config_file.read_bytes(), before)
        self.assertIn('exactly one', result.stderr)

    def test_simultaneous_tab_and_shared_sidebar_fail_nonzero_without_writing(self):
        config = shared_sidebar()
        config['navigation']['tabs'] = copy.deepcopy(EXAMPLES['navigation']['tabs'])
        result, actual, before = self.run_script(config)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.config_file.read_bytes(), before)
        self.assertIn('exactly one', result.stderr)

    def test_missing_docs_file_fails_nonzero(self):
        result = subprocess.run([sys.executable, str(UPDATER), '--docs-json', str(self.config_file), '--notebooks-dir', str(self.notebooks)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)

    def test_missing_notebooks_directory_fails_nonzero(self):
        self.config_file.write_text(json.dumps(EXAMPLES))
        result = subprocess.run([sys.executable, str(UPDATER), '--docs-json', str(self.config_file), '--notebooks-dir', str(self.root / 'missing')], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
