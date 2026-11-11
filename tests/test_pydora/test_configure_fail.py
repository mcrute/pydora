import pytest

from pydora.configure import Configurator


def test_fail_prints_message_without_stray_none(capsys):
    with pytest.raises(SystemExit) as exc_info:
        Configurator().fail("boom")

    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    assert "boom" in out
    assert "None" not in out
