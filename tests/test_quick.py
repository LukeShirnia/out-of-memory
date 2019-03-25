import pytest
import oom_analyzer
import mock
import textwrap


LOGFILE = textwrap.dedent("""\
    Jun 29 15:39:16 server-03 kernel: imklog 5.8.10, log source = /proc/kmsg started.
""")
LOGFILE1 = textwrap.dedent("""\
    Jul 1 15:39:16 server-03 kernel: imklog 5.8.10, log source = /proc/kmsg started.
""")
LOGFILE2 = textwrap.dedent("""\
    Aug 1  15:39:16 server-03 kernel: imklog 5.8.10, log source = /proc/kmsg started.
""")


MEMINFO = textwrap.dedent("""\
    MemTotal:         500412 kB
    MemFree:           89492 kB
    MemAvailable:     356280 kB
    Buffers:           58608 kB
    Cached:           204472 kB
    SwapCached:            0 kB
    Active:           257928 kB
    Inactive:          96228 kB
    Active(anon):      91308 kB
    Inactive(anon):    12424 kB
    Active(file):     166620 kB
    Inactive(file):    83804 kB
    Unevictable:           0 kB
    Mlocked:               0 kB
    SwapTotal:             0 kB
    SwapFree:              0 kB
    Dirty:               200 kB
    Writeback:             0 kB
    AnonPages:         91076 kB
    Mapped:            23828 kB
    Shmem:             12656 kB
    Slab:              40564 kB
    SReclaimable:      26912 kB
    SUnreclaim:        13652 kB
    KernelStack:        1648 kB
    PageTables:         2796 kB
    NFS_Unstable:          0 kB
    Bounce:                0 kB
    WritebackTmp:          0 kB
    CommitLimit:      250204 kB
    Committed_AS:     261552 kB
    VmallocTotal:   34359738367 kB
    VmallocUsed:        4680 kB
    VmallocChunk:   34359699432 kB
    HardwareCorrupted:     0 kB
    AnonHugePages:         0 kB
    HugePages_Total:       0
    HugePages_Free:        0
    HugePages_Rsvd:        0
    HugePages_Surp:        0
    Hugepagesize:       2048 kB
    DirectMap4k:       38912 kB
    DirectMap2M:      612352 kB
""")


OOMOUTPUT = textwrap.dedent("""\

    \x1b[4mLog Information\x1b[0m
    \x1b[92mLog File  : \x1b[93m /var/log/messages \x1b[0m
    \x1b[92mStart date: \x1b[0m\x1b[93m Jun, 29, 15:39:16 \x1b[0m
    \x1b[92mEnd Date  : \x1b[0m\x1b[93m Jun, 29, 15:39:16 \x1b[0m
    
    
    
    ----------------------------------------
    OOM has \x1b[92mNOT\x1b[0m occured in specified log file!
    ----------------------------------------
    
    \x1b[93mChecking other logs, select an option:\x1b[0m
               /var/log/messages.1        - Occurrences: 0
               /var/log/messages.2        - Occurrences: 0

""")


QUICKOUTPUT = textwrap.dedent("""\
    \x1b[36m----------------------------------------\x1b[0m
          _____ _____ _____ 
         |     |     |     |
         |  |  |  |  | | | |
         |_____|_____|_|_|_|
        Out Of Memory Analyzer

    \x1b[91m\x1b[4mDisclaimer:\x1b[0m
    \x1b[91mIf system OOMs too viciously, there may be nothing logged!
    Do NOT take this script as FACT, investigate further.\x1b[0m
    \x1b[36m----------------------------------------\x1b[0m
    \x1b[93mChecking other logs, select an option:\x1b[0m
               /var/log/messages          - Occurrences: 0
               /var/log/messages.1        - Occurrences: 0

""")


def test_quick(fs, monkeypatch, capsys):
    def returnlf():
        return '/var/log/messages'
    _lf = '/var/log/messages'
    monkeypatch.setattr(oom_analyzer.sys, 'argv', ['oom_analyzer.py', '--quick'])
    monkeypatch.setattr(oom_analyzer, 'get_log_file', returnlf)
    monkeypatch.setattr(oom_analyzer.GetLogData, 'checkfilesize', lambda x: True)
    monkeypatch.setattr(oom_analyzer, 'check_dmesg', lambda x: True)
    fs.CreateFile('/var/log/messages', contents=LOGFILE)
    fs.CreateFile('/var/log/messages.1', contents=LOGFILE1)
    fs.CreateFile('/proc/meminfo', contents=MEMINFO)

    with pytest.raises(SystemExit) as ex:
        oom_analyzer.main()
        assert ex.code == 0
    out, err = capsys.readouterr()
    assert str(out) == QUICKOUTPUT


def test_output(fs, monkeypatch, capsys):
    _lf = '/var/log/messages'
    monkeypatch.setattr(oom_analyzer.GetLogData, 'checkfilesize', lambda x: True)
    monkeypatch.setattr(oom_analyzer, 'check_dmesg', lambda x: True)
    fs.CreateFile('/var/log/messages', contents=LOGFILE)
    fs.CreateFile('/var/log/messages.1', contents=LOGFILE1)
    fs.CreateFile('/var/log/messages.2', contents=LOGFILE2)
    fs.CreateFile('/proc/meminfo', contents=MEMINFO)

    oom_analyzer.catch_log_exceptions(_lf)
    out, err = capsys.readouterr()
    assert str(out) == OOMOUTPUT
