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
    def test_distro_info_imports(self):
        # very basic test to check if the distro info is returned
        # Designed to run on docker containers for python 2.7, 3.6, 3.10
        system = System()
        distro_info = system.get_distro_info()
        assert distro_info[0] is not None
        assert distro_info[1] is not None

    def test_file_processing(self, capsys):
        # Test specific functionality when '-f messages' is passed
        system = System()
        options = Values(
            {
                "file": "tests/assets/logs/messages",
                "show_counter": 5,
                "reverse": False,
                "journalctl": False,
                "dmesg": False,
                "quick": False,
                "version": None,
            }
        )

        with pytest.raises(SystemExit) as ex:
            system.log_to_use = options.file
            run(system, options)
            assert ex.code == 0

        out, _ = capsys.readouterr()
        assert "Using Log File: \x1b[0m\x1b[1;32mtests/assets/logs/messages" in out
