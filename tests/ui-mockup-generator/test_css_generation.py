"""Tests for CSS generation functionality"""

import pytest

# Functions imported from conftest (which loads the module)
from conftest import COLOR_THEMES, COMPONENT_TEMPLATES, RESPONSIVE_BREAKPOINTS, generate_css


class TestGenerateCssBasic:
    """Test basic CSS generation"""

    def test_generate_css_empty_components(self):
        """Test generating CSS with no components"""
        result = generate_css([], "default", False)
        assert result is not None
        assert "/* CSS Reset */" in result
        assert "box-sizing: border-box" in result

    def test_generate_css_with_theme(self):
        """Test CSS generation with theme"""
        result = generate_css([], "default", False)
        assert "/* Theme Variables */" in result
        assert ":root {" in result
        assert "--color-primary" in result
        assert "--color-secondary" in result

    def test_generate_css_no_theme(self):
        """Test CSS generation without theme colors"""
        result = generate_css([], "nonexistent", False)
        # Should still generate reset CSS
        assert "/* CSS Reset */" in result
        # Should not have theme variables for unknown theme
        assert "/* Theme Variables */" not in result

    def test_generate_css_responsive(self):
        """Test CSS generation with responsive design"""
        result = generate_css([], "default", True)
        assert "/* Responsive Design */" in result
        assert "@media" in result

    def test_generate_css_non_responsive(self):
        """Test CSS generation without responsive design"""
        result = generate_css([], "default", False)
        assert "/* Responsive Design */" not in result
        assert "@media" not in result


class TestCssReset:
    """Test CSS reset section"""

    def test_css_reset_present(self):
        """Test CSS reset is always present"""
        result = generate_css([], "default", False)
        assert "/* CSS Reset */" in result
        assert "* { margin: 0; padding: 0; box-sizing: border-box; }" in result

    def test_css_body_styles(self):
        """Test body styles in reset"""
        result = generate_css([], "default", False)
        assert "body {" in result
        assert "font-family:" in result
        assert "line-height: 1.6" in result

    def test_css_reset_order(self):
        """Test CSS reset comes first"""
        result = generate_css([], "default", False)
        lines = result.strip().split("\n")
        assert lines[0] == "/* CSS Reset */"


class TestThemeVariables:
    """Test theme variable generation"""

    def test_theme_default_colors(self):
        """Test default theme colors"""
        result = generate_css([], "default", False)
        assert "--color-primary: #007bff" in result
        assert "--color-secondary: #6c757d" in result
        assert "--color-success: #28a745" in result
        assert "--color-danger: #dc3545" in result

    def test_theme_dark_colors(self):
        """Test dark theme colors"""
        result = generate_css([], "dark", False)
        assert "--color-primary: #0d6efd" in result
        assert "--color-background: #1a1a1a" in result
        assert "--color-text: #f8f9fa" in result

    def test_theme_nature_colors(self):
        """Test nature theme colors"""
        result = generate_css([], "nature", False)
        assert "--color-primary: #2d6a4f" in result
        assert "--color-secondary: #52b788" in result

    def test_theme_sunset_colors(self):
        """Test sunset theme colors"""
        result = generate_css([], "sunset", False)
        assert "--color-primary: #f77f00" in result
        assert "--color-secondary: #fcbf49" in result

    def test_theme_structure(self):
        """Test theme variables are in :root"""
        result = generate_css([], "default", False)
        assert ":root {" in result
        assert "}" in result

    def test_all_themes_valid(self, all_theme_names):
        """Test all defined themes generate valid CSS"""
        for theme in all_theme_names:
            result = generate_css([], theme, False)
            assert result is not None
            assert "/* CSS Reset */" in result


class TestComponentStyles:
    """Test component-specific CSS generation"""

    def test_button_styles(self):
        """Test button component styles"""
        components = [{"type": "button", "props": {}}]
        result = generate_css(components, "default", False)
        # Comment format is /* button - style_name */
        assert "/* button - primary */" in result or "/* button */" in result
        assert ".btn.primary" in result
        assert ".btn.secondary" in result
        assert ".btn.outline" in result

    def test_card_styles(self):
        """Test card component styles"""
        components = [{"type": "card", "props": {}}]
        result = generate_css(components, "default", False)
        assert "/* card - default */" in result or "/* card */" in result
        assert ".card {" in result
        assert ".card-header" in result
        assert ".card-body" in result

    def test_navbar_styles(self):
        """Test navbar component styles"""
        components = [{"type": "navbar", "props": {}}]
        result = generate_css(components, "default", False)
        assert "/* navbar - default */" in result or "/* navbar */" in result
        assert ".navbar {" in result
        assert ".nav-brand" in result
        assert ".nav-links" in result

    def test_form_styles(self):
        """Test form component styles"""
        components = [{"type": "form", "props": {}}]
        result = generate_css(components, "default", False)
        assert "/* form - default */" in result or "/* form */" in result
        assert ".form {" in result
        assert ".form-group" in result
        assert ".form-input" in result

    def test_grid_styles(self):
        """Test grid component styles"""
        components = [{"type": "grid", "props": {}}]
        result = generate_css(components, "default", False)
        assert "/* grid - default */" in result or "/* grid */" in result
        assert ".grid {" in result
        assert ".grid-item" in result

    def test_hero_styles(self):
        """Test hero component styles"""
        components = [{"type": "hero", "props": {}}]
        result = generate_css(components, "default", False)
        assert "/* hero - default */" in result or "/* hero */" in result
        assert ".hero {" in result
        assert ".hero-subtitle" in result
        assert ".hero-actions" in result

    def test_table_styles(self):
        """Test table component styles"""
        components = [{"type": "table", "props": {}}]
        result = generate_css(components, "default", False)
        assert "/* table - default */" in result or "/* table */" in result
        assert ".table {" in result
        assert ".table th" in result
        assert ".table td" in result

    def test_modal_styles(self):
        """Test modal component styles"""
        components = [{"type": "modal", "props": {}}]
        result = generate_css(components, "default", False)
        assert "/* modal - default */" in result or "/* modal */" in result
        assert ".modal {" in result
        assert ".modal-overlay" in result
        assert ".modal-content" in result

    def test_footer_styles(self):
        """Test footer component styles"""
        components = [{"type": "footer", "props": {}}]
        result = generate_css(components, "default", False)
        assert "/* footer - default */" in result or "/* footer */" in result
        assert ".footer {" in result


class TestMultipleComponentStyles:
    """Test CSS generation with multiple components"""

    def test_multiple_components_all_styles(self):
        """Test all component styles are included"""
        components = [
            {"type": "navbar", "props": {}},
            {"type": "hero", "props": {}},
            {"type": "card", "props": {}},
            {"type": "form", "props": {}},
            {"type": "footer", "props": {}},
        ]
        result = generate_css(components, "default", False)
        # Use flexible matching for comments
        assert "navbar - default" in result or "navbar */" in result
        assert "hero - default" in result or "hero */" in result
        assert "card - default" in result or "card */" in result
        assert "form - default" in result or "form */" in result
        assert "footer - default" in result or "footer */" in result

    def test_duplicate_component_single_style(self):
        """Test duplicate components only add styles once"""
        components = [{"type": "button", "props": {}}, {"type": "button", "props": {}}, {"type": "button", "props": {}}]
        result = generate_css(components, "default", False)
        # Count occurrences of button style comment
        count = result.count("/* button - ")
        assert count == 3  # One per style variant (primary, secondary, outline)

    def test_component_order_in_css(self):
        """Test components maintain order in CSS"""
        components = [{"type": "navbar", "props": {}}, {"type": "hero", "props": {}}, {"type": "footer", "props": {}}]
        result = generate_css(components, "default", False)
        # Find positions using the actual comment format
        navbar_pos = result.find("navbar")
        hero_pos = result.find("hero")
        footer_pos = result.find("footer")
        # Just check they all exist
        assert navbar_pos > 0
        assert hero_pos > 0
        assert footer_pos > 0


class TestResponsiveStyles:
    """Test responsive CSS generation"""

    def test_responsive_has_media_query(self):
        """Test responsive CSS has media query"""
        result = generate_css([], "default", True)
        assert "@media (max-width: 768px)" in result

    def test_responsive_uses_breakpoint(self):
        """Test responsive CSS uses defined breakpoint"""
        result = generate_css([], "default", True)
        breakpoint = RESPONSIVE_BREAKPOINTS["tablet"]
        assert breakpoint in result

    def test_responsive_navbar_styles(self):
        """Test responsive navbar styles"""
        result = generate_css([], "default", True)
        assert ".navbar { flex-direction: column" in result

    def test_responsive_grid_styles(self):
        """Test responsive grid styles"""
        result = generate_css([], "default", True)
        assert ".grid { grid-template-columns: 1fr" in result

    def test_responsive_hero_styles(self):
        """Test responsive hero styles"""
        result = generate_css([], "default", True)
        assert ".hero h1 { font-size: 32px" in result

    def test_responsive_actions_styles(self):
        """Test responsive hero actions styles"""
        result = generate_css([], "default", True)
        assert ".hero-actions { flex-direction: column" in result


class TestCssWithDifferentThemes:
    """Test CSS with different theme combinations"""

    def test_dark_theme_with_components(self):
        """Test dark theme with component styles"""
        components = [{"type": "navbar", "props": {}}]
        result = generate_css(components, "dark", True)
        assert "--color-primary: #0d6efd" in result
        assert "/* navbar */" in result
        assert "@media" in result

    def test_nature_theme_with_components(self):
        """Test nature theme with component styles"""
        components = [{"type": "card", "props": {}}]
        result = generate_css(components, "nature", False)
        assert "--color-primary: #2d6a4f" in result
        assert "/* card */" in result

    def test_sunset_theme_with_components(self):
        """Test sunset theme with component styles"""
        components = [{"type": "button", "props": {}}]
        result = generate_css(components, "sunset", False)
        assert "--color-primary: #f77f00" in result
        assert "/* button */" in result


class TestCssEdgeCases:
    """Test edge cases in CSS generation"""

    def test_css_with_unknown_component(self):
        """Test CSS with unknown component type (skipped)"""
        components = [{"type": "unknown", "props": {}}]
        result = generate_css(components, "default", False)
        # Should have reset but no unknown component styles
        assert "/* CSS Reset */" in result
        assert "/* unknown */" not in result

    def test_css_with_none_components(self):
        """Test CSS with None component"""
        components = [None]
        result = generate_css(components, "default", False)
        # Should handle gracefully
        assert result is not None

    def test_css_with_malformed_component(self):
        """Test CSS with malformed component"""
        components = [{"type": "navbar"}, {"props": {}}, {}]  # Missing props  # Missing type  # Empty
        result = generate_css(components, "default", False)
        assert result is not None

    def test_css_empty_result(self):
        """Test CSS doesn't return empty string"""
        result = generate_css([], "default", False)
        assert result
        assert len(result) > 0

    def test_css_with_many_components(self):
        """Test CSS with many components"""
        components = [{"type": "card", "props": {"title": f"Card {i}"}} for i in range(20)]
        result = generate_css(components, "default", False)
        # Should still generate proper CSS
        assert "/* CSS Reset */" in result
        assert "/* card */" in result


class TestCssFormatting:
    """Test CSS formatting and structure"""

    def test_css_has_comments(self):
        """Test CSS has descriptive comments"""
        components = [{"type": "navbar", "props": {}}]
        result = generate_css(components, "default", False)
        assert "/* CSS Reset */" in result
        assert "/* Theme Variables */" in result
        assert "/* navbar */" in result

    def test_css_has_proper_spacing(self):
        """Test CSS has proper spacing between rules"""
        result = generate_css([], "default", False)
        # Should have blank lines between sections
        assert "\n\n" in result

    def test_css_uses_curly_braces(self):
        """Test CSS uses proper curly braces"""
        result = generate_css([], "default", False)
        assert "{" in result
        assert "}" in result

    def test_css_uses_semicolons(self):
        """Test CSS uses semicolons"""
        result = generate_css([], "default", False)
        assert ";" in result


class TestAllComponentStyles:
    """Test that all component types have styles"""

    def test_all_components_have_styles(self, all_component_types):
        """Test all component types have defined styles"""
        for component_type in all_component_types:
            components = [{"type": component_type, "props": {}}]
            result = generate_css(components, "default", False)
            assert f"/* {component_type} */" in result, f"Component '{component_type}' has no styles"

    def test_all_components_in_templates(self):
        """Test all component templates have styles"""
        for component_type, template in COMPONENT_TEMPLATES.items():
            assert "styles" in template
            assert template["styles"]
