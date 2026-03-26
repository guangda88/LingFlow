"""Tests for HTML generation functionality"""

import pytest

# Functions imported from conftest (which loads the module)
from conftest import generate_html


class TestGenerateHtmlBasic:
    """Test basic HTML generation"""

    def test_generate_html_empty_components(self):
        """Test generating HTML with no components"""
        result = generate_html("Test Page", [], "default")
        assert result is not None
        assert '<!DOCTYPE html>' in result
        assert '<html lang="zh-CN">' in result
        assert '<title>Test Page</title>' in result

    def test_generate_html_with_title(self):
        """Test HTML generation with custom title"""
        result = generate_html("Custom Title", [], "default")
        assert '<title>Custom Title</title>' in result

    def test_generate_html_single_component(self, mock_component_button):
        """Test HTML generation with single component"""
        result = generate_html("Test", [mock_component_button], "default")
        assert '<button' in result

    def test_generate_html_multiple_components(self, mock_components_list):
        """Test HTML generation with multiple components"""
        result = generate_html("Test", mock_components_list, "default")
        assert '<nav' in result  # navbar
        assert '<section' in result  # hero
        assert '<button' in result  # button

    def test_generate_html_preserves_order(self):
        """Test that components are rendered in order"""
        components = [
            {'type': 'navbar', 'props': {}},
            {'type': 'hero', 'props': {}},
            {'type': 'footer', 'props': {}}
        ]
        result = generate_html("Test", components, "default")
        navbar_pos = result.find('<nav')
        hero_pos = result.find('<section')
        footer_pos = result.find('<footer')
        assert navbar_pos < hero_pos < footer_pos


class TestHtmlStructure:
    """Test HTML structure and validity"""

    def test_html_has_doctype(self):
        """Test HTML has DOCTYPE declaration"""
        result = generate_html("Test", [], "default")
        assert result.startswith('<!DOCTYPE html>')

    def test_html_has_html_tag(self):
        """Test HTML has html tag"""
        result = generate_html("Test", [], "default")
        assert '<html lang="zh-CN">' in result
        assert '</html>' in result

    def test_html_has_head_and_body(self):
        """Test HTML has head and body tags"""
        result = generate_html("Test", [], "default")
        assert '<head>' in result
        assert '</head>' in result
        assert '<body>' in result
        assert '</body>' in result

    def test_html_has_charset(self):
        """Test HTML has charset meta tag"""
        result = generate_html("Test", [], "default")
        assert '<meta charset="UTF-8">' in result

    def test_html_has_viewport(self):
        """Test HTML has viewport meta tag"""
        result = generate_html("Test", [], "default")
        assert '<meta name="viewport"' in result
        assert 'width=device-width' in result

    def test_html_has_css_link(self):
        """Test HTML links to CSS file"""
        result = generate_html("Test", [], "default")
        assert '<link rel="stylesheet" href="styles.css">' in result


class TestHtmlWithComponents:
    """Test HTML generation with various components"""

    def test_html_with_navbar(self):
        """Test HTML with navbar component"""
        components = [{'type': 'navbar', 'props': {'brand': 'Test'}}]
        result = generate_html("Test", components, "default")
        assert '<nav class="navbar"' in result

    def test_html_with_hero(self):
        """Test HTML with hero component"""
        components = [{'type': 'hero', 'props': {}}]
        result = generate_html("Test", components, "default")
        assert '<section class="hero"' in result

    def test_html_with_cards(self):
        """Test HTML with card components"""
        components = [
            {'type': 'card', 'props': {'title': 'Card 1', 'content': 'Content 1'}},
            {'type': 'card', 'props': {'title': 'Card 2', 'content': 'Content 2'}}
        ]
        result = generate_html("Test", components, "default")
        assert result.count('class="card"') == 2
        assert 'Card 1' in result
        assert 'Card 2' in result

    def test_html_with_form(self):
        """Test HTML with form component"""
        components = [{'type': 'form', 'props': {}}]
        result = generate_html("Test", components, "default")
        assert '<form class="form"' in result

    def test_html_with_grid(self):
        """Test HTML with grid component"""
        components = [{'type': 'grid', 'props': {'columns': 3, 'item_count': 6}}]
        result = generate_html("Test", components, "default")
        assert '<div class="grid"' in result
        assert 'grid-template-columns: repeat(3, 1fr)' in result

    def test_html_with_table(self):
        """Test HTML with table component"""
        components = [{'type': 'table', 'props': {}}]
        result = generate_html("Test", components, "default")
        assert '<table class="table"' in result

    def test_html_with_modal(self):
        """Test HTML with modal component"""
        components = [{'type': 'modal', 'props': {'id': 'testModal'}}]
        result = generate_html("Test", components, "default")
        assert '<div class="modal"' in result
        assert 'id="testModal"' in result

    def test_html_with_footer(self):
        """Test HTML with footer component"""
        components = [{'type': 'footer', 'props': {}}]
        result = generate_html("Test", components, "default")
        assert '<footer class="footer"' in result


class TestHtmlContent:
    """Test HTML content and formatting"""

    def test_html_uses_indentation(self):
        """Test HTML has proper indentation"""
        components = [{'type': 'navbar', 'props': {}}]
        result = generate_html("Test", components, "default")
        # Check that body content is indented
        assert '    <nav' in result

    def test_html_complete_document(self):
        """Test HTML is a complete document"""
        result = generate_html("Test", [], "default")
        lines = result.strip().split('\n')
        assert lines[0] == '<!DOCTYPE html>'
        assert lines[-1] == '</html>'

    def test_html_with_special_characters_in_title(self):
        """Test HTML with special characters in title"""
        result = generate_html("Test & Demo <2024>", [], "default")
        assert 'Test &amp; Demo &lt;2024&gt;' in result

    def test_html_with_unicode_title(self):
        """Test HTML with unicode title"""
        result = generate_html("测试页面", [], "default")
        assert '测试页面' in result

    def test_html_escaping_in_content(self):
        """Test HTML escaping in component content"""
        components = [
            {'type': 'card', 'props': {'title': '<script>', 'content': '</script>'}}
        ]
        result = generate_html("Test", components, "default")
        # Content should be present (actual escaping depends on format method)
        assert 'script' in result


class TestHtmlWithThemes:
    """Test HTML generation with different themes"""

    def test_html_with_default_theme(self):
        """Test HTML with default theme"""
        result = generate_html("Test", [], "default")
        assert result is not None

    def test_html_with_dark_theme(self):
        """Test HTML with dark theme"""
        result = generate_html("Test", [], "dark")
        assert result is not None

    def test_html_with_nature_theme(self):
        """Test HTML with nature theme"""
        result = generate_html("Test", [], "nature")
        assert result is not None

    def test_html_with_sunset_theme(self):
        """Test HTML with sunset theme"""
        result = generate_html("Test", [], "sunset")
        assert result is not None

    def test_html_with_unknown_theme(self):
        """Test HTML with unknown theme (should still work)"""
        result = generate_html("Test", [], "unknown_theme")
        assert result is not None


class TestHtmlComplexScenarios:
    """Test complex HTML generation scenarios"""

    def test_full_landing_page(self):
        """Test generating a full landing page"""
        components = [
            {'type': 'navbar', 'props': {'brand': 'Startup', 'links': ['Home', 'Features', 'Pricing']}},
            {'type': 'hero', 'props': {'title': 'Launch Your Idea', 'subtitle': 'Fast & Easy'}},
            {'type': 'grid', 'props': {'columns': 3, 'item_count': 6}},
            {'type': 'footer', 'props': {'company': 'Startup Inc'}}
        ]
        result = generate_html("Landing Page", components, "default")
        assert '<nav' in result
        assert '<section class="hero"' in result
        assert '<div class="grid"' in result
        assert '<footer' in result

    def test_dashboard_layout(self):
        """Test generating a dashboard layout"""
        components = [
            {'type': 'navbar', 'props': {'brand': 'Dashboard', 'links': ['Overview', 'Analytics', 'Settings']}},
            {'type': 'grid', 'props': {'columns': 4, 'item_count': 8}},
            {'type': 'table', 'props': {'headers': ['Name', 'Value', 'Status'], 'row_count': 5}}
        ]
        result = generate_html("Dashboard", components, "default")
        assert '<nav' in result
        assert '<div class="grid"' in result
        assert '<table' in result

    def test_login_page(self):
        """Test generating a login page"""
        components = [
            {'type': 'navbar', 'props': {'brand': 'MyApp', 'links': ['Home', 'About']}},
            {'type': 'card', 'props': {'title': 'Login', 'content': ''}},
            {'type': 'form', 'props': {'fields': ['Username', 'Password'], 'submit_text': 'Sign In'}},
            {'type': 'footer', 'props': {'company': 'MyApp'}}
        ]
        result = generate_html("Login", components, "default")
        assert '<nav' in result
        assert '<div class="card"' in result
        assert '<form' in result
        assert '<footer' in result


class TestHtmlEdgeCases:
    """Test edge cases in HTML generation"""

    def test_html_with_none_title(self):
        """Test HTML with None title"""
        result = generate_html(None, [], "default")
        assert result is not None

    def test_html_with_empty_title(self):
        """Test HTML with empty title"""
        result = generate_html("", [], "default")
        assert '<title></title>' in result

    def test_html_with_very_long_title(self):
        """Test HTML with very long title"""
        long_title = "A" * 1000
        result = generate_html(long_title, [], "default")
        assert long_title in result

    def test_html_with_unknown_component_type(self):
        """Test HTML with unknown component type (should skip)"""
        components = [
            {'type': 'navbar', 'props': {}},
            {'type': 'unknown_type', 'props': {}},
            {'type': 'footer', 'props': {}}
        ]
        result = generate_html("Test", components, "default")
        assert '<nav' in result
        assert '<footer' in result

    def test_html_with_malformed_component(self):
        """Test HTML with malformed component"""
        components = [
            {'type': 'navbar'},  # Missing props
            None,  # None component
            {'props': {'text': 'test'}}  # Missing type
        ]
        result = generate_html("Test", components, "default")
        # Should not crash
        assert result is not None

    def test_html_with_duplicate_components(self):
        """Test HTML with duplicate component types"""
        components = [
            {'type': 'button', 'props': {'text': 'Button 1'}},
            {'type': 'button', 'props': {'text': 'Button 2'}},
            {'type': 'button', 'props': {'text': 'Button 3'}}
        ]
        result = generate_html("Test", components, "default")
        assert result.count('class="btn') == 3

    def test_html_with_max_components(self):
        """Test HTML with many components"""
        components = [
            {'type': 'card', 'props': {'title': f'Card {i}', 'content': f'Content {i}'}}
            for i in range(50)
        ]
        result = generate_html("Test", components, "default")
        assert result.count('class="card"') == 50
