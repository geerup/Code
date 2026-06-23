import pytest

from aio_control.runner import first_token, run_capture


@pytest.mark.asyncio
async def test_run_capture_success():
    res = await run_capture("echo hello")
    assert res.ok
    assert res.exit_code == 0
    assert res.output == "hello"


@pytest.mark.asyncio
async def test_run_capture_failure():
    res = await run_capture("exit 3")
    assert not res.ok
    assert res.exit_code == 3


@pytest.mark.asyncio
async def test_run_capture_combines_stderr():
    res = await run_capture("echo err 1>&2")
    assert "err" in res.output


@pytest.mark.asyncio
async def test_run_capture_timeout():
    res = await run_capture("sleep 5", timeout=0.3)
    assert res.timed_out
    assert res.exit_code == 124


@pytest.mark.parametrize(
    "cmd, expected",
    [
        ("hackrf_info", "hackrf_info"),
        ("/usr/bin/gqrx --foo", "gqrx"),
        ("FOO=bar rtl_fm -f 96.9M", "rtl_fm"),
        ("uhubctl -a on -p 2", "uhubctl"),
    ],
)
def test_first_token(cmd, expected):
    assert first_token(cmd) == expected
