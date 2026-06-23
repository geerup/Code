import pytest

from aio_control.app import AIOControlApp, CategoryTable
from aio_control.config import load_config


@pytest.mark.asyncio
async def test_app_boots_and_has_tabs():
    cfg = load_config()
    app = AIOControlApp(cfg)
    async with app.run_test() as pilot:
        # one CategoryTable per category, each populated.
        tables = list(app.query(CategoryTable))
        assert len(tables) == len(cfg.categories)
        for table, cat in zip(tables, cfg.categories):
            assert table.row_count == len(cat.entries)
        await pilot.pause()


@pytest.mark.asyncio
async def test_run_command_logs_output():
    cfg = load_config()
    app = AIOControlApp(cfg)
    async with app.run_test() as pilot:
        cid, row, entry = "t", 0, None
        # Drive a known command entry directly through the helper.
        from aio_control.models import Entry, EntryType

        entry = Entry(name="Echo", type=EntryType.COMMAND, cmd="echo smoketest")
        # Inject a temporary table-free command run via the internal helper.
        await app._run_command(cfg.categories[0].id, 0, entry)
        await pilot.pause()
        # The RichLog should contain our output somewhere in its lines.
        from textual.widgets import RichLog

        log = app.query_one("#log", RichLog)
        text = "\n".join(str(line) for line in log.lines)
        assert "smoketest" in text


@pytest.mark.asyncio
async def test_navigation_keys_dont_crash():
    cfg = load_config()
    app = AIOControlApp(cfg)
    async with app.run_test() as pilot:
        await pilot.press("right", "down", "down", "left")
        await pilot.pause()
        assert app._active_category_id() is not None
