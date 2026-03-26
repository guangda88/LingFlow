"""Tests for theme system functionality"""

import pytest

# Functions imported from conftest (which loads the module)
from conftest import COLOR_THEMES, generate_css, generate_mockup


class TestColorThemesStructure:
    """Test color themes structure"""

    def test_all_themes_have_required_keys(self):
        """Test all themes have required color keys"""
        required_keys = {'primary', 'secondary', 'success', 'danger', 'background', 'text'}
        for theme_name, theme_colors in COLOR_THEMES.items():
            missing_keys = required_keys - set(theme_colors.keys())
            assert not missing_keys, f"Theme '{theme_name}' missing keys: {missing_keys}"

    def test_all_colors_are_hex(self):
        """Test all theme colors are valid hex colors"""
        for theme_name, theme_colors in COLOR_THEMES.items():
            for color_key, color_value in theme_colors.items():
                assert color_value.startswith('#'), \
                    f"Theme '{theme_name}' color '{color_key}' is not hex: {color_value}"
                # Check hex length (7 chars including # for standard hex)
                assert len(color_value) == 7, \
                    f"Theme '{theme_name}' color '{color_key}' has invalid length: {color_value}"

    def test_default_theme_exists(self):
        """Test default theme exists"""
        assert 'default' in COLOR_THEMES

    def test_theme_names(self, all_theme_names):
        """Test expected theme names exist"""
        for theme_name in all_theme_names:
            assert theme_name in COLOR_THEMES, f"Theme '{theme_name}' not found"


class TestDefaultTheme:
    """Test default theme colors"""

    def test_default_primary_color(self):
        """Test default primary color"""
        assert COLOR_THEMES['default']['primary'] == '#007bff'

    def test_default_secondary_color(self):
        """Test default secondary color"""
        assert COLOR_THEMES['default']['secondary'] == '#6c757d'

    def test_default_success_color(self):
        """Test default success color"""
        assert COLOR_THEMES['default']['success'] == '#28a745'

    def test_default_danger_color(self):
        """Test default danger color"""
        assert COLOR_THEMES['default']['danger'] == '#dc3545'

    def test_default_background_color(self):
        """Test default background color"""
        assert COLOR_THEMES['default']['background'] == '#ffffff'

    def test_default_text_color(self):
        """Test default text color"""
        assert COLOR_THEMES['default']['text'] == '#333333'


class TestDarkTheme:
    """Test dark theme colors"""

    def test_dark_primary_color(self):
        """Test dark theme primary color"""
        assert COLOR_THEMES['dark']['primary'] == '#0d6efd'

    def test_dark_background_is_dark(self):
        """Test dark theme background is actually dark"""
        bg = COLOR_THEMES['dark']['background']
        assert bg == '#1a1a1a' or bg == '#000000'

    def test_dark_text_is_light(self):
        """Test dark theme text is light colored"""
        text = COLOR_THEMES['dark']['text']
        # Light colors have higher values
        assert text == '#f8f9fa' or text == '#ffffff'


class TestNatureTheme:
    """Test nature theme colors"""

    def test_nature_primary_is_green(self):
        """Test nature theme primary is green"""
        primary = COLOR_THEMES['nature']['primary']
        assert '#2' in primary or '#3' in primary or '#4' in primary

    def test_nature_secondary_is_green(self):
        """Test nature theme secondary is green"""
        secondary = COLOR_THEMES['nature']['secondary']
        assert '#5' in secondary or '#6' in secondary or '#7' in secondary


class TestSunsetTheme:
    """Test sunset theme colors"""

    def test_sunset_primary_is_warm(self):
        """Test sunset theme primary is warm color"""
        primary = COLOR_THEMES['sunset']['primary']
        # Orange/yellow/warm tones
        assert primary in ['#f77f00', '#fcbf49', '#e76f51']

    def test_sunset_secondary_is_warm(self):
        """Test sunset theme secondary is warm color"""
        secondary = COLOR_THEMES['sunset']['secondary']
        # Yellow/warm tones
        assert '#f' in secondary


class TestThemeInCssGeneration:
    """Test theme application in CSS generation"""

    def test_css_includes_theme_variables(self):
        """Test CSS includes theme variables"""
        result = generate_css([], "default", False)
        assert ':root {' in result
        assert '--color-primary:' in result
        assert '--color-secondary:' in result

    def test_default_theme_in_css(self):
        """Test default theme colors in CSS"""
        result = generate_css([], "default", False)
        assert '--color-primary: #007bff' in result
        assert '--color-secondary: #6c757d' in result

    def test_dark_theme_in_css(self):
        """Test dark theme colors in CSS"""
        result = generate_css([], "dark", False)
        assert '--color-primary: #0d6efd' in result
        assert '--color-background: #1a1a1a' in result

    def test_nature_theme_in_css(self):
        """Test nature theme colors in CSS"""
        result = generate_css([], "nature", False)
        assert '--color-primary: #2d6a4f' in result
        assert '--color-secondary: #52b788' in result

    def test_sunset_theme_in_css(self):
        """Test sunset theme colors in CSS"""
        result = generate_css([], "sunset", False)
        assert '--color-primary: #f77f00' in result
        assert '--color-secondary: #fcbf49' in result

    def test_unknown_theme_skips_variables(self):
        """Test unknown theme skips theme variables"""
        result = generate_css([], "nonexistent", False)
        assert ':root {' not in result


class TestThemeInMockupGeneration:
    """Test theme application in full mockup generation"""

    def test_mockup_with_default_theme(self):
        """Test mockup generation with default theme"""
        result = generate_mockup({'requirement': 'create a navbar', 'theme': 'default'})
        assert result is not None
        assert result['metadata']['theme'] == 'default'
        assert '--color-primary: #007bff' in result['css']

    def test_mockup_with_dark_theme(self):
        """Test mockup generation with dark theme"""
        result = generate_mockup({'requirement': 'create a navbar', 'theme': 'dark'})
        assert result is not None
        assert result['metadata']['theme'] == 'dark'
        assert '--color-primary: #0d6efd' in result['css']

    def test_mockup_with_nature_theme(self):
        """Test mockup generation with nature theme"""
        result = generate_mockup({'requirement': 'create a navbar', 'theme': 'nature'})
        assert result is not None
        assert result['metadata']['theme'] == 'nature'
        assert '--color-primary: #2d6a4f' in result['css']

    def test_mockup_with_sunset_theme(self):
        """Test mockup generation with sunset theme"""
        result = generate_mockup({'requirement': 'create a navbar', 'theme': 'sunset'})
        assert result is not None
        assert result['metadata']['theme'] == 'sunset'
        assert '--color-primary: #f77f00' in result['css']

    def test_mockup_default_theme_when_not_specified(self):
        """Test default theme is used when not specified"""
        result = generate_mockup({'requirement': 'create a navbar'})
        assert result is not None
        assert result['metadata']['theme'] == 'default'


class TestThemeConsistency:
    """Test theme consistency across generations"""

    def test_same_theme_produces_same_colors(self):
        """Test same theme produces consistent colors"""
        result1 = generate_css([], "default", False)
        result2 = generate_css([], "default", False)
        assert result1 == result2

    def test_different_themes_produce_different_colors(self):
        """Test different themes produce different colors"""
        result_default = generate_css([], "default", False)
        result_dark = generate_css([], "dark", False)
        assert result_default != result_dark
        assert '#007bff' in result_default
        assert '#0d6efd' in result_dark

    def test_theme_affects_all_color_variables(self):
        """Test theme affects all color variables"""
        for theme_name in COLOR_THEMES:
            result = generate_css([], theme_name, False)
            theme = COLOR_THEMES[theme_name]
            for color_key, color_value in theme.items():
                css_var = f'--color-{color_key}: {color_value}'
                assert css_var in result, \
                    f"Theme '{theme_name}' missing CSS variable: {css_var}"


class TestThemeEdgeCases:
    """Test theme edge cases"""

    def test_empty_theme_name(self):
        """Test empty theme name defaults"""
        result = generate_css([], "", False)
        # Should handle gracefully
        assert result is not None

    def test_none_theme_name(self):
        """Test None theme name"""
        result = generate_css([], None, False)
        # Should handle gracefully
        assert result is not None

    def test_case_sensitive_theme_names(self):
        """Test theme names are case sensitive"""
        result_lower = generate_css([], "default", False)
        result_upper = generate_css([], "DEFAULT", False)
        # Different case should produce different results
        # (uppercase won't match, so no theme variables)
        assert '--color-primary:' in result_lower
        assert '--color-primary:' not in result_upper

    def test_theme_with_special_characters(self):
        """Test theme name with special characters"""
        result = generate_css([], "theme-with-dash", False)
        # Should handle gracefully (no match, no crash)
        assert result is not None


class TestThemeColorsValidity:
    """Test theme colors are valid CSS colors"""

    def test_all_hex_colors_valid(self):
        """Test all hex colors are valid 6-digit hex codes"""
        hex_pattern = re.compile(r'^#[0-9a-fA-F]{6}$')
        for theme_name, theme_colors in COLOR_THEMES.items():
            for color_key, color_value in theme_colors.items():
                assert hex_pattern.match(color_value), \
                    f"Invalid hex color in theme '{theme_name}': {color_key}={color_value}"

    def test_no_duplicate_theme_colors(self):
        """Test no duplicate color values within a theme (reasonable test)"""
        # This is a soft test - some colors might legitimately be the same
        for theme_name, theme_colors in COLOR_THEMES.items():
            values = list(theme_colors.values())
            # Check that not ALL colors are the same
            assert len(set(values)) > 1, \
                f"Theme '{theme_name}' has all identical colors"


# Import re for regex
import re
