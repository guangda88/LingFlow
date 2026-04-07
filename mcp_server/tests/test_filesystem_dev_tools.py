"""Tests for Phase 4 filesystem and dev tools (multiedit, ls, download, diagnostics, references)"""

import pytest

from lingflow_mcp.tools import ToolRegistry


@pytest.fixture
def registry():
    r = ToolRegistry()
    r.register_filesystem_and_dev_tools()
    return r


class TestMultiedit:
    @pytest.mark.asyncio
    async def test_single_edit(self, tmp_path, registry):
        f = tmp_path / "test.txt"
        f.write_text("hello world\n")
        handler = registry.get_tool_handler("multiedit")
        result = await handler(
            file_path=str(f),
            edits=[{"old_string": "hello", "new_string": "goodbye"}],
        )
        assert result["success"] is True
        assert result["applied"] == 1
        assert f.read_text() == "goodbye world\n"

    @pytest.mark.asyncio
    async def test_multiple_edits(self, tmp_path, registry):
        f = tmp_path / "test.txt"
        f.write_text("aaa bbb ccc\n")
        handler = registry.get_tool_handler("multiedit")
        result = await handler(
            file_path=str(f),
            edits=[
                {"old_string": "aaa", "new_string": "xxx"},
                {"old_string": "bbb", "new_string": "yyy"},
            ],
        )
        assert result["success"] is True
        assert result["applied"] == 2
        assert f.read_text() == "xxx yyy ccc\n"

    @pytest.mark.asyncio
    async def test_file_not_found(self, registry):
        handler = registry.get_tool_handler("multiedit")
        result = await handler(
            file_path="/nonexistent/path.txt",
            edits=[{"old_string": "a", "new_string": "b"}],
        )
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_old_string_not_found(self, tmp_path, registry):
        f = tmp_path / "test.txt"
        f.write_text("hello\n")
        handler = registry.get_tool_handler("multiedit")
        result = await handler(
            file_path=str(f),
            edits=[{"old_string": "nonexistent", "new_string": "x"}],
        )
        assert result["success"] is True
        assert result["applied"] == 0
        assert len(result["failed"]) == 1

    @pytest.mark.asyncio
    async def test_replace_all(self, tmp_path, registry):
        f = tmp_path / "test.txt"
        f.write_text("aaa bbb aaa\n")
        handler = registry.get_tool_handler("multiedit")
        result = await handler(
            file_path=str(f),
            edits=[{"old_string": "aaa", "new_string": "zzz", "replace_all": True}],
        )
        assert result["success"] is True
        assert result["applied"] == 1
        assert f.read_text() == "zzz bbb zzz\n"


class TestListDirectory:
    @pytest.mark.asyncio
    async def test_basic_listing(self, tmp_path, registry):
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.py").write_text("b")
        handler = registry.get_tool_handler("list_directory")
        result = await handler(path=str(tmp_path), depth=1)
        assert result["success"] is True
        names = [c["name"] for c in result["tree"]["children"]]
        assert "a.txt" in names
        assert "b.py" in names

    @pytest.mark.asyncio
    async def test_depth_control(self, tmp_path, registry):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "deep.txt").write_text("deep")
        handler = registry.get_tool_handler("list_directory")
        result = await handler(path=str(tmp_path), depth=0)
        assert result["success"] is True
        children = result["tree"].get("children", [])
        sub_entry = next((c for c in children if c["name"] == "sub"), None)
        if sub_entry:
            assert "children" not in sub_entry or sub_entry.get("children") is None or "children" not in sub_entry

    @pytest.mark.asyncio
    async def test_not_a_directory(self, tmp_path, registry):
        f = tmp_path / "file.txt"
        f.write_text("x")
        handler = registry.get_tool_handler("list_directory")
        result = await handler(path=str(f))
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_ignore_patterns(self, tmp_path, registry):
        (tmp_path / "keep.txt").write_text("k")
        (tmp_path / "skip.log").write_text("s")
        handler = registry.get_tool_handler("list_directory")
        result = await handler(path=str(tmp_path), depth=1, ignore=["*.log"])
        assert result["success"] is True
        names = [c["name"] for c in result["tree"]["children"]]
        assert "keep.txt" in names
        assert "skip.log" not in names


class TestDownloadFile:
    @pytest.mark.asyncio
    async def test_file_not_found_url(self, registry):
        handler = registry.get_tool_handler("download_file")
        result = await handler(
            url="http://localhost:1/nonexistent",
            file_path="/tmp/test_dl.txt",
            timeout=2,
        )
        assert result["success"] is False


class TestGetDiagnostics:
    @pytest.mark.asyncio
    async def test_returns_structure(self, registry):
        handler = registry.get_tool_handler("get_diagnostics")
        result = await handler(file_path="/home/ai/LingFlow/lingflow/__init__.py")
        assert result["success"] is True
        assert "diagnostics" in result


class TestFindReferences:
    @pytest.mark.asyncio
    async def test_finds_known_symbol(self, registry):
        handler = registry.get_tool_handler("find_references")
        result = await handler(
            symbol="ExternalServerConfig",
            path="/home/ai/LingFlow/mcp_server",
        )
        assert result["success"] is True
        assert result["total"] > 0
        files = [r["file"] for r in result["references"]]
        assert any("external_router" in f for f in files)

    @pytest.mark.asyncio
    async def test_not_a_directory(self, registry):
        handler = registry.get_tool_handler("find_references")
        result = await handler(symbol="foo", path="/nonexistent/dir")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_no_results(self, tmp_path, registry):
        handler = registry.get_tool_handler("find_references")
        result = await handler(
            symbol="xyzzy_nonexistent_symbol_12345",
            path=str(tmp_path),
        )
        assert result["success"] is True
        assert result["total"] == 0


class TestToolRegistration:
    def test_all_five_tools_registered(self, registry):
        expected = {"multiedit", "list_directory", "download_file", "get_diagnostics", "find_references"}
        registered = set(registry.tools.keys())
        assert expected.issubset(registered), f"Missing: {expected - registered}"

    def test_all_have_mcp_schemas(self, registry):
        mcp_tools = registry.get_mcp_tools()
        mcp_names = {t.name for t in mcp_tools}
        expected = {"multiedit", "list_directory", "download_file", "get_diagnostics", "find_references"}
        assert expected.issubset(mcp_names)
