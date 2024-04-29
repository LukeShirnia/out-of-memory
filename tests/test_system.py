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
            "show_all": False
        }
    )

    def test_distro_info_imports(self):
        # very basic test to check if the distro info is returned
        # Designed to run on docker containers for python 2.7, 3.6, 3.10
        distro_info = self.system.get_distro_info()
        assert distro_info[0] is not None
        assert distro_info[1] is not None

    def test_file_processing(self, capsys):
        # Test specific functionality when '-f messages' is passed
        options = self.values
        options.file = "tests/assets/logs/messages"
        # While we're here, we might as well test the --all functionality so we don't have to pass
        # the large log file too many times
        options.show_all = True

        with pytest.raises(SystemExit) as ex:
            self.system.log_to_use = options.file
            run(self.system, options)
            assert ex.code == 0

        out, _ = capsys.readouterr()
        assert "Using Log File: \x1b[0m\x1b[1;32mtests/assets/logs/messages" in out
        assert "OOM Incidents: \x1b[0m\x1b[1;31m19\x1b[0m" in out
        assert "OOM Incident: \x1b[0m\x1b[0;96m19\x1b[0m" in out
        assert "Displaying all OOM incidents:" in out

    def test_default_system_log(self):
        # Test default system log file
        options = self.values

        system = validate_options(self.system, options)
        with pytest.raises(SystemExit) as ex:
            run(system, options)
            assert ex.code == 0
