import pytest
import oom_analyzer
import mock
import textwrap


UNSUPPORTEDERROR = textwrap.dedent("""\
    Unsupported OS
    """)


@pytest.mark.parametrize('os, logfile', [
    (('redhat', '7.6', 'Maipo'), '/var/log/messages'),
    (('Ubuntu', '18.04', 'bionic'), '/var/log/syslog'),
    (('oracle', '7.5', ''), '/var/log/messages'),
    (('fedora', '28', 'Twenty Eight'), '/var/log/messages'),
    (('debian', '9.6', ''), '/var/log/syslog')
])
def test_os_logfile(monkeypatch, capsys, os, logfile):
    def return_value():
        return os
    monkeypatch.setattr(oom_analyzer.platform, 'dist', return_value)

    assert oom_analyzer.get_log_file(logf=None) == logfile


def test_unsupported_os(monkeypatch, capsys):
    def return_value():
        return ('unknown', 'x.x', '')
    monkeypatch.setattr(oom_analyzer.platform, 'dist', return_value)

    with pytest.raises(SystemExit) as ex:
        oom_analyzer.get_log_file(logf=None)
        assert ex.code == 1

    out, err = capsys.readouterr()
    assert str(out) == UNSUPPORTEDERROR
