import pytest
import oom_analyzer
import textwrap


scriptheader = textwrap.dedent("""\
    \x1b[36m----------------------------------------\x1b[0m
          _____ _____ _____ 
         |     |     |     |
         |  |  |  |  | | | |
         |_____|_____|_|_|_|
         Out Of Memory Analyser
    
    \x1b[91m\x1b[4mDisclaimer:\x1b[0m
    \x1b[91mIf system OOMs too viciously, there may be nothing logged!
    Do NOT take this script as FACT, investigate further\x1b[0m
    \x1b[36m----------------------------------------\x1b[0m
    """)


def test_bcolors_header():
    assert oom_analyzer.bcolors.HEADER == "\033[95m"


def test_header(capsys):
    oom_analyzer.print_header()
    out, err = capsys.readouterr()
    assert str(out) == scriptheader
