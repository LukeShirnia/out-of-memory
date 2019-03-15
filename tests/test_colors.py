import pytest
import oom_analyzer

def test_header():
    assert oom_analyzer.bcolors.HEADER == "\033[95m"
