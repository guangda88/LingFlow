"""Tests for requirement parsing functionality"""

import pytest

# Functions imported from conftest (which loads the module)
from conftest import COMPONENT_TEMPLATES, extract_component_props, parse_requirements


class TestParseRequirements:
    """Test parse_requirements function"""

    def test_parse_empty_requirement(self):
        """Test parsing empty requirement returns default components"""
        result = parse_requirements("")
        assert len(result) == 2
        assert result[0]["type"] == "navbar"
        assert result[1]["type"] == "hero"

    def test_parse_none_requirement(self):
        """Test parsing None requirement returns default components"""
        result = parse_requirements(None)
        assert len(result) == 2
        assert result[0]["type"] == "navbar"

    def test_parse_navbar_requirement(self):
        """Test parsing navbar from requirement"""
        result = parse_requirements("Create a navbar for my app")
        types = [c["type"] for c in result]
        assert "navbar" in types

    def test_parse_navbar_chinese(self):
        """Test parsing navbar from Chinese requirement"""
        result = parse_requirements("创建一个导航栏")
        types = [c["type"] for c in result]
        assert "navbar" in types

    def test_parse_hero_requirement(self):
        """Test parsing hero from requirement"""
        result = parse_requirements("Add a hero banner section")
        types = [c["type"] for c in result]
        assert "hero" in types

    def test_parse_card_requirement(self):
        """Test parsing card from requirement"""
        result = parse_requirements("Include information cards")
        types = [c["type"] for c in result]
        assert "card" in types

    def test_parse_form_requirement(self):
        """Test parsing form from requirement"""
        result = parse_requirements("Add a login form")
        types = [c["type"] for c in result]
        assert "form" in types

    def test_parse_button_requirement(self):
        """Test parsing button from requirement"""
        result = parse_requirements("Add a click button")
        types = [c["type"] for c in result]
        assert "button" in types

    def test_parse_table_requirement(self):
        """Test parsing table from requirement"""
        result = parse_requirements("Display a data table")
        types = [c["type"] for c in result]
        assert "table" in types

    def test_parse_grid_requirement(self):
        """Test parsing grid from requirement"""
        result = parse_requirements("Create a grid layout")
        types = [c["type"] for c in result]
        assert "grid" in types

    def test_parse_modal_requirement(self):
        """Test parsing modal from requirement"""
        result = parse_requirements("Add a popup dialog")
        types = [c["type"] for c in result]
        assert "modal" in types

    def test_parse_footer_requirement(self):
        """Test parsing footer from requirement"""
        result = parse_requirements("Add a footer section")
        types = [c["type"] for c in result]
        assert "footer" in types

    def test_parse_multiple_components(self):
        """Test parsing multiple components from single requirement"""
        result = parse_requirements("Create a navbar with a hero section and some cards")
        types = [c["type"] for c in result]
        assert "navbar" in types
        assert "hero" in types
        assert "card" in types

    def test_parse_case_insensitive(self):
        """Test that parsing is case insensitive"""
        result_lower = parse_requirements("create a navbar")
        result_upper = parse_requirements("CREATE A NAVBAR")
        result_mixed = parse_requirements("Create a NavBar")

        assert "navbar" in [c["type"] for c in result_lower]
        assert "navbar" in [c["type"] for c in result_upper]
        assert "navbar" in [c["type"] for c in result_mixed]

    def test_parse_with_brand_name(self):
        """Test parsing with brand name specified"""
        result = parse_requirements("navbar with brand TechCorp")
        navbar = next((c for c in result if c["type"] == "navbar"), None)
        assert navbar is not None
        assert navbar["props"]["brand"] == "TechCorp"

    def test_parse_with_links(self):
        """Test parsing with links specified"""
        result = parse_requirements("navbar with links Home, About, Contact")
        navbar = next((c for c in result if c["type"] == "navbar"), None)
        assert navbar is not None
        assert "Home" in navbar["props"]["links"]
        assert "About" in navbar["props"]["links"]
        assert "Contact" in navbar["props"]["links"]

    def test_parse_hero_with_titles(self):
        """Test parsing hero with title and subtitle"""
        result = parse_requirements("hero section with title 'Welcome' and subtitle 'Get Started'")
        hero = next((c for c in result if c["type"] == "hero"), None)
        assert hero is not None
        assert "Welcome" in hero["props"]["title"]
        assert "Get Started" in hero["props"]["subtitle"]


class TestExtractComponentProps:
    """Test extract_component_props function"""

    def test_extract_navbar_props_default(self):
        """Test extracting navbar props with defaults"""
        props = extract_component_props("navbar", "navbar")
        assert "brand" in props
        assert "links" in props
        assert props["brand"] == "MyApp"
        assert len(props["links"]) == 3

    def test_extract_navbar_props_custom_brand(self):
        """Test extracting navbar props with custom brand"""
        props = extract_component_props("brand: StartupCo", "navbar")
        assert props["brand"] == "StartupCo"

    def test_extract_navbar_props_custom_links(self):
        """Test extracting navbar props with custom links"""
        props = extract_component_props("links: Products, Pricing, Contact", "navbar")
        assert "Products" in props["links"]
        assert "Pricing" in props["links"]
        assert "Contact" in props["links"]

    def test_extract_hero_props_default(self):
        """Test extracting hero props with defaults"""
        props = extract_component_props("hero section", "hero")
        assert "title" in props
        assert "subtitle" in props

    def test_extract_hero_props_custom(self):
        """Test extracting hero props with custom values"""
        props = extract_component_props("title: Hello World, subtitle: Join Us", "hero")
        assert "Hello World" in props["title"]
        assert "Join Us" in props["subtitle"]

    def test_extract_button_props_primary(self):
        """Test extracting button props with primary style"""
        props = extract_component_props("primary button", "button")
        assert props["style"] == "primary"

    def test_extract_button_props_outline(self):
        """Test extracting button props with outline style"""
        props = extract_component_props("outline button", "button")
        assert props["style"] == "outline"

    def test_extract_button_props_secondary(self):
        """Test extracting button props with secondary style"""
        props = extract_component_props("secondary button", "button")
        assert props["style"] == "secondary"

    def test_extract_button_props_default_style(self):
        """Test extracting button props defaults to secondary"""
        props = extract_component_props("button", "button")
        assert props["style"] == "secondary"

    def test_extract_card_props(self):
        """Test extracting card props"""
        props = extract_component_props("card with title About and content Lorem ipsum", "card")
        assert "About" in props["title"]
        assert "Lorem ipsum" in props["content"]

    def test_extract_form_props(self):
        """Test extracting form props"""
        props = extract_component_props("form with fields Username, Email, Password", "form")
        assert "Username" in props["fields"]
        assert "Email" in props["fields"]
        assert "Password" in props["fields"]

    def test_extract_form_submit_text(self):
        """Test extracting form submit button text"""
        props = extract_component_props("submit text: Sign Up Now", "form")
        assert "Sign Up Now" in props["submit_text"]

    def test_extract_grid_props_columns(self):
        """Test extracting grid columns"""
        props = extract_component_props("grid with 4 columns", "grid")
        assert props["columns"] == 4

    def test_extract_grid_props_items(self):
        """Test extracting grid item count"""
        props = extract_component_props("grid with 6 items", "grid")
        assert props["item_count"] == 6

    def test_extract_table_props_headers(self):
        """Test extracting table headers"""
        props = extract_component_props("table with headers ID, Name, Email, Role", "table")
        assert "ID" in props["headers"]
        assert "Name" in props["headers"]
        assert "Email" in props["headers"]
        assert "Role" in props["headers"]

    def test_extract_table_props_rows(self):
        """Test extracting table row count"""
        props = extract_component_props("table with 10 rows", "table")
        assert props["row_count"] == 10

    def test_extract_modal_props(self):
        """Test extracting modal props"""
        props = extract_component_props("modal with title Confirmation", "modal")
        assert "Confirmation" in props["title"]
        assert props["id"] == "myModal"

    def test_extract_footer_props(self):
        """Test extracting footer props"""
        props = extract_component_props("footer with company Acme Inc", "footer")
        assert "Acme Inc" in props["company"]

    def test_extract_props_unknown_component(self):
        """Test extracting props for unknown component type"""
        props = extract_component_props("some text", "unknown")
        assert props == {}


class TestComponentKeywords:
    """Test component keyword detection"""

    def test_all_components_have_keywords(self):
        """Test that all component types have keywords defined"""
        # 使用已经导入的 parse_requirements
        # This should not raise any errors
        for component_type in COMPONENT_TEMPLATES.keys():
            # Create a requirement with just the component type
            result = parse_requirements(f"Create a {component_type}")
            types = [c["type"] for c in result]
            assert component_type in types

    def test_keyword_variations_navbar(self):
        """Test various navbar keyword variations"""
        keywords = ["navbar", "导航", "导航栏", "header", "页头"]
        for keyword in keywords:
            result = parse_requirements(f"Create a {keyword}")
            types = [c["type"] for c in result]
            assert "navbar" in types, f"Failed for keyword: {keyword}"

    def test_keyword_variations_hero(self):
        """Test various hero keyword variations"""
        keywords = ["hero", "首屏", "banner", "横幅", "主区域"]
        for keyword in keywords:
            result = parse_requirements(f"Add a {keyword}")
            types = [c["type"] for c in result]
            assert "hero" in types, f"Failed for keyword: {keyword}"

    def test_keyword_variations_card(self):
        """Test various card keyword variations"""
        keywords = ["card", "卡片", "信息卡"]
        for keyword in keywords:
            result = parse_requirements(f"Add a {keyword}")
            types = [c["type"] for c in result]
            assert "card" in types, f"Failed for keyword: {keyword}"

    def test_keyword_variations_modal(self):
        """Test various modal keyword variations"""
        keywords = ["modal", "弹窗", "对话框", "popup"]
        for keyword in keywords:
            result = parse_requirements(f"Add a {keyword}")
            types = [c["type"] for c in result]
            assert "modal" in types, f"Failed for keyword: {keyword}"


class TestRequirementEdgeCases:
    """Test edge cases in requirement parsing"""

    def test_requirement_with_special_chars(self):
        """Test parsing requirement with special characters"""
        result = parse_requirements("Create a navbar with brand @#$%")
        navbar = next((c for c in result if c["type"] == "navbar"), None)
        assert navbar is not None

    def test_requirement_with_unicode(self):
        """Test parsing requirement with unicode characters"""
        result = parse_requirements("创建导航栏，品牌是'我的应用'，链接是首页、关于、联系")
        navbar = next((c for c in result if c["type"] == "navbar"), None)
        assert navbar is not None

    def test_requirement_very_long(self):
        """Test parsing very long requirement"""
        long_req = "Create a " + "very " * 100 + "navbar"
        result = parse_requirements(long_req)
        types = [c["type"] for c in result]
        assert "navbar" in types

    def test_requirement_with_numbers(self):
        """Test parsing requirement with numbers"""
        result = parse_requirements("Create a navbar with 5 links")
        navbar = next((c for c in result if c["type"] == "navbar"), None)
        assert navbar is not None

    def test_requirement_with_newlines(self):
        """Test parsing requirement with newlines"""
        result = parse_requirements("Create a navbar\nwith brand MyApp\nand links Home, About")
        navbar = next((c for c in result if c["type"] == "navbar"), None)
        assert navbar is not None
