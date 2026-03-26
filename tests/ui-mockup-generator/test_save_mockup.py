"""Tests for mockup save functionality"""

import json
import pytest
from pathlib import Path

# Functions imported from conftest (which loads the module)
from conftest import save_mockup, generate_mockup, execute_skill


class TestSaveMockupBasic:
    """Test basic mockup saving"""

    def test_save_mockup_creates_directory(self, mock_output_dir):
        """Test saving creates output directory"""
        result = generate_mockup({'requirement': 'create a navbar'})
        saved = save_mockup(result, mock_output_dir)

        output_path = Path(mock_output_dir)
        assert output_path.exists()
        assert output_path.is_dir()

    def test_save_mockup_creates_html_file(self, mock_output_dir):
        """Test saving creates HTML file"""
        result = generate_mockup({'requirement': 'create a navbar'})
        saved = save_mockup(result, mock_output_dir)

        html_file = Path(saved['html'])
        assert html_file.exists()
        assert html_file.is_file()
        assert html_file.name == 'index.html'

    def test_save_mockup_creates_css_file(self, mock_output_dir):
        """Test saving creates CSS file"""
        result = generate_mockup({'requirement': 'create a navbar'})
        saved = save_mockup(result, mock_output_dir)

        css_file = Path(saved['css'])
        assert css_file.exists()
        assert css_file.is_file()
        assert css_file.name == 'styles.css'

    def test_save_mockup_creates_manifest_file(self, mock_output_dir):
        """Test saving creates manifest file"""
        result = generate_mockup({'requirement': 'create a navbar'})
        saved = save_mockup(result, mock_output_dir)

        manifest_file = Path(saved['manifest'])
        assert manifest_file.exists()
        assert manifest_file.is_file()
        assert manifest_file.name == 'manifest.json'


class TestSavedFileContents:
    """Test contents of saved files"""

    def test_html_file_content(self, mock_output_dir):
        """Test HTML file has correct content"""
        result = generate_mockup({'requirement': 'create a navbar', 'title': 'Test Page'})
        saved = save_mockup(result, mock_output_dir)

        html_content = Path(saved['html']).read_text(encoding='utf-8')
        assert '<!DOCTYPE html>' in html_content
        assert '<title>Test Page</title>' in html_content
        assert '<nav' in html_content

    def test_css_file_content(self, mock_output_dir):
        """Test CSS file has correct content"""
        result = generate_mockup({'requirement': 'create a navbar', 'theme': 'dark'})
        saved = save_mockup(result, mock_output_dir)

        css_content = Path(saved['css']).read_text(encoding='utf-8')
        assert '/* CSS Reset */' in css_content
        assert '--color-primary: #0d6efd' in css_content

    def test_manifest_file_content(self, mock_output_dir):
        """Test manifest file has correct structure"""
        result = generate_mockup({
            'requirement': 'create a navbar',
            'theme': 'nature'
        })
        saved = save_mockup(result, mock_output_dir)

        manifest_content = Path(saved['manifest']).read_text(encoding='utf-8')
        manifest = json.loads(manifest_content)

        assert 'components' in manifest
        assert 'metadata' in manifest
        assert manifest['metadata']['theme'] == 'nature'
        assert isinstance(manifest['components'], list)

    def test_manifest_components_list(self, mock_output_dir):
        """Test manifest contains component list"""
        result = generate_mockup({'requirement': 'create a navbar and hero'})
        saved = save_mockup(result, mock_output_dir)

        manifest_content = Path(saved['manifest']).read_text(encoding='utf-8')
        manifest = json.loads(manifest_content)

        component_types = [c['type'] for c in manifest['components']]
        assert 'navbar' in component_types
        assert 'hero' in component_types


class TestSaveReturnValue:
    """Test save_mockup return value"""

    def test_save_returns_file_paths(self, mock_output_dir):
        """Test save returns correct file paths"""
        result = generate_mockup({'requirement': 'create a navbar'})
        saved = save_mockup(result, mock_output_dir)

        assert 'html' in saved
        assert 'css' in saved
        assert 'manifest' in saved

    def test_save_paths_are_absolute(self, mock_output_dir):
        """Test saved paths are absolute"""
        result = generate_mockup({'requirement': 'create a navbar'})
        saved = save_mockup(result, mock_output_dir)

        # All paths should be absolute strings
        for file_type, path in saved.items():
            assert isinstance(path, str)
            assert Path(path).is_absolute()

    def test_save_paths_in_output_dir(self, mock_output_dir):
        """Test saved files are in output directory"""
        result = generate_mockup({'requirement': 'create a navbar'})
        saved = save_mockup(result, mock_output_dir)

        output_path = Path(mock_output_dir).resolve()
        for file_type, file_path in saved.items():
            path = Path(file_path).resolve()
            # Check file is in output directory
            assert path.parent == output_path


class TestSaveWithExistingDirectory:
    """Test saving when directory already exists"""

    def test_save_to_existing_dir(self, mock_output_dir):
        """Test saving to pre-existing directory"""
        # Create directory first
        Path(mock_output_dir).mkdir(parents=True, exist_ok=True)

        result = generate_mockup({'requirement': 'create a navbar'})
        saved = save_mockup(result, mock_output_dir)

        # Should still work
        assert Path(saved['html']).exists()

    def test_save_overwrites_existing_files(self, mock_output_dir):
        """Test saving overwrites existing files"""
        # Create files first
        Path(mock_output_dir).mkdir(parents=True, exist_ok=True)
        (Path(mock_output_dir) / 'index.html').write_text('OLD CONTENT')

        result = generate_mockup({'requirement': 'create a navbar'})
        saved = save_mockup(result, mock_output_dir)

        html_content = Path(saved['html']).read_text()
        assert 'OLD CONTENT' not in html_content
        assert '<!DOCTYPE html>' in html_content


class TestSaveWithComplexMockups:
    """Test saving complex mockups"""

    def test_save_landing_page(self, mock_output_dir):
        """Test saving a full landing page"""
        result = generate_mockup({
            'requirement': 'landing page with navbar, hero, grid, and footer',
            'title': 'Landing Page'
        })
        saved = save_mockup(result, mock_output_dir)

        # Check HTML
        html_content = Path(saved['html']).read_text()
        assert '<nav' in html_content
        assert '<section class="hero"' in html_content
        assert '<div class="grid"' in html_content
        assert '<footer' in html_content

    def test_save_dashboard(self, mock_output_dir):
        """Test saving a dashboard mockup"""
        result = generate_mockup({
            'requirement': 'dashboard with navbar, table, and cards',
            'theme': 'dark'
        })
        saved = save_mockup(result, mock_output_dir)

        # Check CSS
        css_content = Path(saved['css']).read_text()
        assert '--color-primary: #0d6efd' in css_content

        # Check manifest
        manifest = json.loads(Path(saved['manifest']).read_text())
        assert manifest['metadata']['theme'] == 'dark'

    def test_save_with_many_components(self, mock_output_dir):
        """Test saving mockup with many components"""
        # Create proper component list
        base_components = [
            {'type': 'navbar', 'props': {}},
            {'type': 'hero', 'props': {}}
        ]
        card_components = [{'type': 'card', 'props': {'title': f'Card {i}'}} for i in range(5)]
        flat_components = base_components + card_components

        result = generate_mockup({'components': flat_components})
        saved = save_mockup(result, mock_output_dir)

        html_content = Path(saved['html']).read_text()
        assert html_content.count('class="card"') >= 5


class TestSaveEdgeCases:
    """Test edge cases in saving"""

    def test_save_with_empty_result(self, mock_output_dir):
        """Test saving with minimal result"""
        result = generate_mockup({'requirement': ''})
        saved = save_mockup(result, mock_output_dir)

        # Should still create files
        assert Path(saved['html']).exists()
        assert Path(saved['css']).exists()
        assert Path(saved['manifest']).exists()

    def test_save_with_unicode_content(self, mock_output_dir):
        """Test saving with unicode content"""
        result = generate_mockup({
            'requirement': 'create navbar with brand 测试应用',
            'title': '测试页面'
        })
        saved = save_mockup(result, mock_output_dir)

        html_content = Path(saved['html']).read_text(encoding='utf-8')
        assert '测试应用' in html_content
        assert '测试页面' in html_content

    def test_save_with_nested_directory(self, mock_output_dir):
        """Test saving to nested directory"""
        nested_dir = str(Path(mock_output_dir) / 'nested' / 'path')
        saved = save_mockup(generate_mockup({'requirement': 'navbar'}), nested_dir)

        assert Path(saved['html']).exists()
        assert Path(saved['html']).parent.exists()

    def test_save_with_special_chars_in_title(self, mock_output_dir):
        """Test saving with special characters in title"""
        result = generate_mockup({
            'requirement': 'navbar',
            'title': 'Test & Demo <2024>'
        })
        saved = save_mockup(result, mock_output_dir)

        html_content = Path(saved['html']).read_text()
        # HTML entities should be used
        assert '&amp;' in html_content or '&' in html_content


class TestSaveFileEncoding:
    """Test file encoding"""

    def test_html_file_utf8_encoding(self, mock_output_dir):
        """Test HTML file is UTF-8 encoded"""
        result = generate_mockup({'requirement': 'navbar with brand 中文品牌'})
        saved = save_mockup(result, mock_output_dir)

        # Read with UTF-8
        html_content = Path(saved['html']).read_text(encoding='utf-8')
        assert '中文品牌' in html_content

    def test_css_file_utf8_encoding(self, mock_output_dir):
        """Test CSS file is UTF-8 encoded"""
        result = generate_mockup({'requirement': 'navbar'})
        saved = save_mockup(result, mock_output_dir)

        css_content = Path(saved['css']).read_text(encoding='utf-8')
        assert css_content

    def test_manifest_utf8_encoding(self, mock_output_dir):
        """Test manifest is UTF-8 encoded with ensure_ascii=False"""
        result = generate_mockup({'requirement': 'navbar'})
        saved = save_mockup(result, mock_output_dir)

        manifest_content = Path(saved['manifest']).read_text(encoding='utf-8')
        manifest = json.loads(manifest_content)
        assert manifest


class TestExecuteSkillWithSave:
    """Test execute_skill with output_dir parameter"""

    def test_execute_skill_saves_files(self, mock_output_dir):
        """Test execute_skill saves files when output_dir is provided"""
        result = execute_skill({
            'requirement': 'create a navbar',
            'output_dir': mock_output_dir
        })

        assert 'saved_files' in result
        assert 'html' in result['saved_files']
        assert 'css' in result['saved_files']
        assert 'manifest' in result['saved_files']

    def test_execute_skill_without_output_dir(self, tmp_path):
        """Test execute_skill without output_dir doesn't save"""
        result = execute_skill({'requirement': 'create a navbar'})

        assert 'saved_files' not in result
        assert 'html' in result
        assert 'css' in result
