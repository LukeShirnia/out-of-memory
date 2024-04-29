import os
import sys
from optparse import Values

import pytest

# Add the parent directory to the path so we can import the latest version of the script
oom_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, oom_dir)

from oom_investigate import System, run, validate_options

# Ignore DeprecationWarning and PendingDeprecationWarning warnings
pytest.mark.filterwarnings("ignore::DeprecationWarning")
pytest.mark.filterwarnings("ignore::PendingDeprecationWarning")


class TestSystem:
    system = System()
    values = Values(
        {
            "file": False,
            "show_counter": 5,
            "reverse": False,
            "journalctl": False,
            "dmesg": False,
            "quick": False,
            "version": None,
        }
    )

    def test_dmesg(self, capsys):
        # Test journalctl log
        options = self.values
        options.dmesg = True
        options.file = False

        system = validate_options(self.system, options)
        with pytest.raises(SystemExit) as ex:
            run(system, options)
            assert ex.code == 0

        out, _ = capsys.readouterr()
        assert "Using Dmesg: \x1b[0m\x1b[1;32mTrue" in out

    def test_too_many_options(self, capsys):
        # Test too many options
        options = self.values
        options.dmesg = True
        options.journalctl = True
        options.file = "tests/assets/logs/messages"

        with pytest.raises(SystemExit) as ex:
            validate_options(self.system, options)

        assert ex.value.code == 1

        out, _ = capsys.readouterr()
        assert (
            "Error: Please specify only a single option; a log file, dmesg or journalctl."
            in out
        )
        assert "- File: tests/assets/logs/messages" in out
        assert "- journalctl: True" in out
        assert "- dmesg: True" in out
