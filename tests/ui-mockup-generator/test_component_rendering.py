"""Tests for component rendering functionality"""

import pytest

# Functions imported from conftest (which loads the module)
from conftest import COMPONENT_TEMPLATES, render_component


class TestRenderComponentBasic:
    """Test basic component rendering"""

    def test_render_button(self, mock_component_button):
        """Test rendering button component"""
        result = render_component(mock_component_button)
        assert result is not None
        assert "<button" in result
        assert "Submit" in result
        assert "primary" in result

    def test_render_button_secondary(self):
        """Test rendering secondary button"""
        component = {"type": "button", "props": {"text": "Cancel", "style": "secondary"}}
        result = render_component(component)
        assert "secondary" in result
        assert "Cancel" in result

    def test_render_button_outline(self):
        """Test rendering outline button"""
        component = {"type": "button", "props": {"text": "Learn More", "style": "outline"}}
        result = render_component(component)
        assert "outline" in result
        assert "Learn More" in result

    def test_render_card(self, mock_component_card):
        """Test rendering card component"""
        result = render_component(mock_component_card)
        assert result is not None
        assert '<div class="card"' in result
        assert "Test Card" in result
        assert "Test Content" in result
        assert "card-header" in result
        assert "card-body" in result

    def test_render_navbar(self, mock_component_navbar):
        """Test rendering navbar component"""
        result = render_component(mock_component_navbar)
        assert result is not None
        assert '<nav class="navbar"' in result
        assert "BrandName" in result
        assert "Home" in result
        assert "About" in result
        assert "Services" in result
        assert "Contact" in result

    def test_render_form(self, mock_component_form):
        """Test rendering form component"""
        result = render_component(mock_component_form)
        assert result is not None
        assert '<form class="form"' in result
        assert "Name" in result
        assert "Email" in result
        assert "Password" in result
        assert "Sign Up" in result

    def test_render_grid(self, mock_component_grid):
        """Test rendering grid component"""
        result = render_component(mock_component_grid)
        assert result is not None
        assert '<div class="grid"' in result
        assert "grid-template-columns: repeat(4, 1fr)" in result
        assert "grid-item" in result

    def test_render_table(self, mock_component_table):
        """Test rendering table component"""
        result = render_component(mock_component_table)
        assert result is not None
        assert '<table class="table"' in result
        assert "<thead>" in result
        assert "<tbody>" in result
        assert "ID" in result
        assert "Name" in result
        assert "Status" in result
        assert "Date" in result

    def test_render_modal(self, mock_component_modal):
        """Test rendering modal component"""
        result = render_component(mock_component_modal)
        assert result is not None
        assert '<div class="modal"' in result
        assert 'id="testModal"' in result
        assert "Test Modal" in result
        assert "modal-overlay" in result
        assert "modal-content" in result

    def test_render_footer(self, mock_component_footer):
        """Test rendering footer component"""
        result = render_component(mock_component_footer)
        assert result is not None
        assert '<footer class="footer"' in result
        assert "Test Inc." in result
        assert str(datetime.now().year) in result

    def test_render_hero(self):
        """Test rendering hero component"""
        component = {"type": "hero", "props": {"title": "Welcome", "subtitle": "Get Started"}}
        result = render_component(component)
        assert result is not None
        assert '<section class="hero"' in result
        assert "Welcome" in result
        assert "Get Started" in result


class TestRenderComponentEdgeCases:
    """Test edge cases in component rendering"""

    def test_render_unknown_component(self):
        """Test rendering unknown component type"""
        component = {"type": "unknown", "props": {}}
        result = render_component(component)
        assert result is None

    def test_render_component_empty_props(self):
        """Test rendering component with empty props"""
        component = {"type": "button", "props": {}}
        result = render_component(component)
        assert result is not None
        assert "<button" in result

    def test_render_component_missing_type(self):
        """Test rendering component without type"""
        component = {"props": {"text": "Click"}}
        result = render_component(component)
        assert result is None

    def test_render_component_missing_props(self):
        """Test rendering component without props"""
        component = {"type": "button"}
        result = render_component(component)
        assert result is not None

    def test_render_component_none_props(self):
        """Test rendering component with None props"""
        component = {"type": "button", "props": None}
        result = render_component(component)
        assert result is not None


class TestRenderComponentDefaults:
    """Test default values in component rendering"""

    def test_button_default_text(self):
        """Test button default text"""
        component = {"type": "button", "props": {}}
        result = render_component(component)
        assert "Click Me" in result

    def test_button_default_style(self):
        """Test button default style"""
        component = {"type": "button", "props": {"text": "Test"}}
        result = render_component(component)
        # Should have some style class
        assert 'class="btn' in result

    def test_card_default_content(self):
        """Test card default content"""
        component = {"type": "card", "props": {}}
        result = render_component(component)
        assert "Card Title" in result
        assert "Card content goes here." in result

    def test_navbar_default_brand(self):
        """Test navbar default brand"""
        component = {"type": "navbar", "props": {}}
        result = render_component(component)
        assert "MyApp" in result

    def test_navbar_default_links(self):
        """Test navbar default links"""
        component = {"type": "navbar", "props": {}}
        result = render_component(component)
        assert "Home" in result
        assert "About" in result
        assert "Contact" in result

    def test_form_default_fields(self):
        """Test form default fields"""
        component = {"type": "form", "props": {}}
        result = render_component(component)
        assert "Name" in result
        assert "Email" in result

    def test_form_default_submit_text(self):
        """Test form default submit text"""
        component = {"type": "form", "props": {}}
        result = render_component(component)
        assert "Submit" in result

    def test_grid_default_columns(self):
        """Test grid default columns"""
        component = {"type": "grid", "props": {}}
        result = render_component(component)
        assert "repeat(3, 1fr)" in result

    def test_grid_default_items(self):
        """Test grid default item count"""
        component = {"type": "grid", "props": {}}
        result = render_component(component)
        # Should have 3 items
        assert result.count("grid-item") == 3

    def test_table_default_headers(self):
        """Test table default headers"""
        component = {"type": "table", "props": {}}
        result = render_component(component)
        assert "Name" in result
        assert "Description" in result
        assert "Status" in result

    def test_modal_default_id(self):
        """Test modal default id"""
        component = {"type": "modal", "props": {}}
        result = render_component(component)
        assert 'id="myModal"' in result

    def test_modal_default_title(self):
        """Test modal default title"""
        component = {"type": "modal", "props": {}}
        result = render_component(component)
        assert "Modal Title" in result

    def test_footer_default_company(self):
        """Test footer default company"""
        component = {"type": "footer", "props": {}}
        result = render_component(component)
        assert "My Company" in result


class TestRenderComponentSpecialValues:
    """Test rendering with special values"""

    def test_button_with_html_text(self):
        """Test button with HTML-like text (should be escaped or handled)"""
        component = {"type": "button", "props": {"text": '<script>alert("xss")</script>'}}
        result = render_component(component)
        assert result is not None
        # The text should be present (even if not escaped in this simple implementation)
        assert "script" in result

    def test_card_with_long_content(self):
        """Test card with very long content"""
        long_content = "A" * 1000
        component = {"type": "card", "props": {"title": "Title", "content": long_content}}
        result = render_component(component)
        assert result is not None
        assert long_content in result

    def test_navbar_with_many_links(self):
        """Test navbar with many links"""
        many_links = [f"Link{i}" for i in range(20)]
        component = {"type": "navbar", "props": {"brand": "Test", "links": many_links}}
        result = render_component(component)
        assert result is not None
        for link in many_links[:5]:  # Check first few
            assert link in result

    def test_form_with_many_fields(self):
        """Test form with many fields"""
        many_fields = [f"Field{i}" for i in range(15)]
        component = {"type": "form", "props": {"fields": many_fields}}
        result = render_component(component)
        assert result is not None
        for field in many_fields[:5]:
            assert field in result

    def test_table_with_many_headers(self):
        """Test table with many headers"""
        many_headers = [f"Col{i}" for i in range(10)]
        component = {"type": "table", "props": {"headers": many_headers, "row_count": 2}}
        result = render_component(component)
        assert result is not None
        for header in many_headers[:5]:
            assert header in result

    def test_table_with_many_rows(self):
        """Test table with many rows"""
        component = {"type": "table", "props": {"headers": ["A", "B"], "row_count": 50}}
        result = render_component(component)
        assert result is not None
        # Should have 50 data rows
        assert result.count("<tr>") >= 50


class TestAllComponentTypes:
    """Test that all component types can be rendered"""

    def test_all_defined_components_renderable(self, all_component_types):
        """Test that all defined component types are renderable"""
        for component_type in all_component_types:
            component = {"type": component_type, "props": {}}
            result = render_component(component)
            assert result is not None, f"Component type '{component_type}' failed to render"

    def test_all_components_in_templates(self, all_component_types):
        """Test that all component types exist in templates"""
        for component_type in all_component_types:
            assert component_type in COMPONENT_TEMPLATES, f"Component type '{component_type}' not in templates"

    def test_all_templates_have_html_and_styles(self, all_component_types):
        """Test that all templates have html and styles"""
        for component_type in all_component_types:
            template = COMPONENT_TEMPLATES[component_type]
            assert "html" in template
            assert "styles" in template
            assert template["html"]
            assert template["styles"]


class TestComponentStructure:
    """Test the structure of rendered components"""

    def test_button_has_class(self):
        """Test button has class attribute"""
        component = {"type": "button", "props": {}}
        result = render_component(component)
        assert "class=" in result
        assert "btn" in result

    def test_input_has_placeholder(self):
        """Test input has placeholder"""
        component = {"type": "input", "props": {}}
        result = render_component(component)
        assert "placeholder=" in result

    def test_card_has_classes(self):
        """Test card has proper classes"""
        component = {"type": "card", "props": {}}
        result = render_component(component)
        assert 'class="card"' in result
        assert "card-header" in result
        assert "card-body" in result

    def test_form_has_form_group(self):
        """Test form has form-group wrapping"""
        component = {"type": "form", "props": {"fields": ["Test"]}}
        result = render_component(component)
        assert "form-group" in result

    def test_modal_has_overlay(self):
        """Test modal has overlay element"""
        component = {"type": "modal", "props": {}}
        result = render_component(component)
        assert "modal-overlay" in result

    def test_navbar_has_structure(self):
        """Test navbar has proper structure"""
        component = {"type": "navbar", "props": {}}
        result = render_component(component)
        assert "nav-brand" in result
        assert "nav-links" in result

    def test_table_has_structure(self):
        """Test table has proper structure"""
        component = {"type": "table", "props": {}}
        result = render_component(component)
        assert "<thead>" in result
        assert "<tbody>" in result
        assert "</thead>" in result
        assert "</tbody>" in result


# Import datetime for footer test
from datetime import datetime
