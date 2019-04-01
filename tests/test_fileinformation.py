import pytest
import oom_analyzer
import mock
import textwrap


MEMINFO = textwrap.dedent("""\
        MemTotal:        1877804 kB
        MemFree:          401640 kB
        MemAvailable:    1074132 kB
        Buffers:          144000 kB
        Cached:           411680 kB
        SwapCached:            0 kB
        Active:           765748 kB
        Inactive:         213348 kB
        Active(anon):     471384 kB
        Inactive(anon):    51104 kB
        Active(file):     294364 kB
        Inactive(file):   162244 kB
        Unevictable:           0 kB
        Mlocked:               0 kB
        SwapTotal:             0 kB
        SwapFree:              0 kB
        Dirty:                32 kB
        Writeback:             0 kB
        AnonPages:        423416 kB
        Mapped:            44196 kB
        Shmem:             99072 kB
        Slab:             443552 kB
        SReclaimable:     403348 kB
        SUnreclaim:        40204 kB
        KernelStack:        2720 kB
        PageTables:        14620 kB
        NFS_Unstable:          0 kB
        Bounce:                0 kB
        WritebackTmp:          0 kB
        CommitLimit:      938900 kB
        Committed_AS:    1471400 kB
        VmallocTotal:   34359738367 kB
        VmallocUsed:       13480 kB
        VmallocChunk:   34359717628 kB
        HardwareCorrupted:     0 kB
        AnonHugePages:     75776 kB
        HugePages_Total:       0
        HugePages_Free:        0
        HugePages_Rsvd:        0
        HugePages_Surp:        0
        Hugepagesize:       2048 kB
        DirectMap4k:      106496 kB
        DirectMap2M:     1986560 kB
""")

FILECONTENTS = textwrap.dedent("""\
    Jun 29 15:39:16 server-03 kernel: [ pid ]   uid  tgid total_vm      rss cpu oom_adj oom_score_adj name
    Jun 29 15:39:16 server-03 kernel: [  333]     0   333     2667      111   0     -17         -1000 udevd
    Jun 29 15:39:16 server-03 kernel: [  533]     0   533     2666      111   0     -17         -1000 udevd
    Jun 29 15:39:16 server-03 kernel: [  984]     0   984     1220      204   0       0             0 cachefilesd
    Jun 29 15:39:16 server-03 kernel: [ 1003]    32  1003     4744       65   3       0             0 rpcbind
    Jun 29 15:39:16 server-03 kernel: [ 1025]    29  1025     5837      113   0       0             0 rpc.statd
    Jun 29 15:39:16 server-03 kernel: [ 1046]     0  1046     2925      181   1       0             0 xe-daemon
    Jun 29 15:39:16 server-03 kernel: [ 1289]    38  1289     7684      166   0       0             0 ntpd
    Jun 29 15:39:16 server-03 kernel: [ 1395]     0  1395    76335     2861   0       0             0 python
    Jun 29 15:39:16 server-03 kernel: [ 1535]     0  1535     5276       49   0       0             0 atd
    Jun 29 15:39:16 server-03 kernel: [ 1588]     0  1588     1020       22   0       0             0 agetty
    Jun 29 15:39:16 server-03 kernel: [ 1590]     0  1590     1016       21   0       0             0 mingetty
    Jun 29 15:39:16 server-03 kernel: [ 1593]     0  1593     1016       21   0       0             0 mingetty
    Jun 29 15:39:16 server-03 kernel: [ 1597]     0  1597     1016       21   0       0             0 mingetty
    Jun 29 15:39:16 server-03 kernel: [ 1598]     0  1598     2666      109   0     -17         -1000 udevd
    Jun 29 15:39:16 server-03 kernel: [ 1602]     0  1602     1016       21   0       0             0 mingetty
    Jun 29 15:39:16 server-03 kernel: [ 1606]     0  1606     1016       21   0       0             0 mingetty
    Jun 29 15:39:16 server-03 kernel: [ 1612]     0  1612     1016       22   3       0             0 mingetty
    Jun 29 15:39:16 server-03 kernel: [20963]     0 20963    29223      174   3       0             0 crond
    Jun 29 15:39:16 server-03 kernel: [14534]     0 14534   113806     1260   3       0             0 php-fpm
    Jun 29 15:39:16 server-03 kernel: [27645]     0 27645     5417      153   1       0             0 rpc.mountd
    Jun 29 15:39:16 server-03 kernel: [27692]     0 27692     5774       63   0       0             0 rpc.idmapd
    Jun 29 15:39:16 server-03 kernel: [ 4300]    48  4300   113806     1202   0       0             0 php-fpm
    Jun 29 15:39:16 server-03 kernel: [27711]     0 27711    16556      186   0     -17         -1000 sshd
    Jun 29 15:39:16 server-03 kernel: [17007]     0 17007   105524     3104   3       0             0 httpd.worker
    Jun 29 15:39:16 server-03 kernel: [13262]     0 13262    20196      236   1       0             0 master
    Jun 29 15:39:16 server-03 kernel: [13265]    89 13265    20259      251   3       0             0 qmgr
    Jun 29 15:39:16 server-03 kernel: [32612]    48 32612   113806     1202   0       0             0 php-fpm
    Jun 29 15:39:16 server-03 kernel: [12081]    48 12081   113806     1204   1       0             0 php-fpm
    Jun 29 15:39:16 server-03 kernel: [12757]    48 12757   113806     1206   0       0             0 php-fpm
    Jun 29 15:39:16 server-03 kernel: [26214]    48 26214   113806     1207   0       0             0 php-fpm
    Jun 29 15:39:16 server-03 kernel: [24449]    48 24449    31749     2342   1       0             0 httpd.worker
    Jun 29 15:39:16 server-03 kernel: [13361]    89 13361    20216      239   3       0             0 pickup
    Jun 29 15:39:16 server-03 kernel: [18598]    48 18598  1035523   478973   3       0             0 httpd.worker
    Jun 29 15:39:16 server-03 kernel: [18965]     0 18965     1018       31   3       0             0 sleep
    Jun 29 15:39:16 server-03 kernel: [18968]    48 18968   838915   406534   0       0             0 httpd.worker
    Jun 29 15:39:16 server-03 kernel: Out of memory (oom_kill_allocating_task): Kill process 18992 (httpd.worker) score 0 or sacrifice child
    Jun 29 15:39:16 server-03 kernel: Killed process 18992, UID 48, (httpd.worker) total-vm:3355660kB, anon-rss:1615472kB, file-rss:10664kB
""")


EMPTYFILERESPONSE = textwrap.dedent("""\
    
    \x1b[4mLog Information\x1b[0m
    \x1b[92mLog File  : \x1b[93m /var/log/messages \x1b[0m
    \x1b[91mFile appears to be empty\x1b[0m
    
""")

LARGEFILERESPONSE = textwrap.dedent("""\

    !!! File is too LARGE !!!
    Size: 300 MB

    Investigating this 300MB log file could cause memory issues on small servers
    Please consider splitting the file into smallerchunks (such as dates)

""")


NONEXISTENTFILEOUTPUT = textwrap.dedent("""\

    Does the file specified exist? /var/log/nonexistentfile
    Please check again

""")


def test_empty_file(fs, monkeypatch, capsys):
    _lf = '/var/log/messages'
    monkeypatch.setattr(oom_analyzer.DmesgInfo, 'check_dmesg', lambda x: True)
    fs.CreateFile('/var/log/messages', st_size=0)
    fs.CreateFile('/proc/meminfo', contents=MEMINFO)


    with pytest.raises(SystemExit) as ex:
        oom_analyzer.showlogoverview(_lf, "", "")
        assert ex.code == 1

    out, err = capsys.readouterr()
    assert str(out) == EMPTYFILERESPONSE


def test_file_too_large(fs, monkeypatch, capsys):
    _lf = '/var/log/messages'
    monkeypatch.setattr(oom_analyzer.DmesgInfo, 'check_dmesg', lambda x: True)
    monkeypatch.setattr(oom_analyzer.GetLogData, 'size_of_file', lambda x: 300.0)
    fs.CreateFile(_lf, contents=FILECONTENTS, st_size=251)
    fs.CreateFile('/proc/meminfo', contents=MEMINFO)

    o = oom_analyzer.GetLogData(_lf)
    with pytest.raises(SystemExit) as ex:
        o.information()
        assert ex.code == 1

    out, err = capsys.readouterr()
    assert str(out) == LARGEFILERESPONSE


def test_openfile(fs, monkeypatch, capsys):
    with pytest.raises(SystemExit) as ex:
        oom_analyzer.get_log_file(logf="/var/log/nonexistentfile")
        assert ex.code == 1

    out, err = capsys.readouterr()
    assert str(out) == NONEXISTENTFILEOUTPUT