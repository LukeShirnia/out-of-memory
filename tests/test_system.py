import os
import sys

import pytest

# Add the parent directory to the path so we can import the latest version of the script
oom_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, oom_dir)

from oom_investigate import System

# Ignore DeprecationWarning and PendingDeprecationWarning warnings
pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
pytestmark = pytest.mark.filterwarnings("ignore::PendingDeprecationWarning")


class TestSystem:
    def test_distro_info_imports(self):
        # very basic test to check if the distro info is returned
        # Designed to run on docker containers for python 2.7, 3.6, 3.10
        system = System()
        distro_info = system.get_distro_info()
        assert distro_info[0] is not None
        assert distro_info[1] is not None
