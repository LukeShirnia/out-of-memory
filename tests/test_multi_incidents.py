import pytest
import oom_analyzer
import mock
import textwrap


LOGFILE = textwrap.dedent("""\
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
    Jun 29 15:39:16 server-03 kernel: [17007]     0 17007   105524     3104   0       0             0 httpd.worker
    Jun 29 15:39:16 server-03 kernel: [13262]     0 13262    20196      236   1       0             0 master
    Jun 29 15:39:16 server-03 kernel: [13265]    89 13265    20259      251   3       0             0 qmgr
    Jun 29 15:39:16 server-03 kernel: [32612]    48 32612   113806     1202   0       0             0 php-fpm
    Jun 29 15:39:16 server-03 kernel: [12081]    48 12081   113806     1204   1       0             0 php-fpm
    Jun 29 15:39:16 server-03 kernel: [12757]    48 12757   113806     1206   0       0             0 php-fpm
    Jun 29 15:39:16 server-03 kernel: [26214]    48 26214   113806     1207   0       0             0 php-fpm
    Jun 29 15:39:16 server-03 kernel: [24449]    48 24449    31749     2342   1       0             0 httpd.worker
    Jun 29 15:39:16 server-03 kernel: [13361]    89 13361    20216      239   3       0             0 pickup
    Jun 29 15:39:16 server-03 kernel: [18598]    48 18598  1035523   478968   3       0             0 httpd.worker
    Jun 29 15:39:16 server-03 kernel: [18965]     0 18965     1018       31   3       0             0 sleep
    Jun 29 15:39:16 server-03 kernel: [18972]    48 18968   838915   406545   1       0             0 httpd.worker
    Jun 29 15:39:16 server-03 kernel: Out of memory (oom_kill_allocating_task): Kill process 18624 (httpd.worker) score 0 or sacrifice child
    Jun 29 15:39:16 server-03 kernel: Killed process 18624, UID 48, (httpd.worker) total-vm:4142092kB, anon-rss:1900656kB, file-rss:15216kB
    Jun 29 15:39:16 server-03 kernel: [ pid ]   uid  tgid total_vm      rss cpu oom_adj oom_score_adj name
    Jun 29 15:39:16 server-03 kernel: [  333]     0   333     2667      111   0     -17         -1000 udevd
    Jun 29 15:39:16 server-03 kernel: [  533]     0   533     2666      111   0     -17         -1000 udevd
    Jun 29 15:39:16 server-03 kernel: [  984]     0   984     1220      204   0       0             0 cachefilesd
    Jun 29 15:39:16 server-03 kernel: [ 1003]    32  1003     4744       66   0       0             0 rpcbind
    Jun 29 15:39:16 server-03 kernel: [ 1025]    29  1025     5837      113   0       0             0 rpc.statd
    Jun 29 15:39:16 server-03 kernel: [ 1046]     0  1046     2925      186   0       0             0 xe-daemon
    Jun 29 15:39:16 server-03 kernel: [ 1289]    38  1289     7684      173   0       0             0 ntpd
    Jun 29 15:39:16 server-03 kernel: [ 1395]     0  1395    76335     2861   0       0             0 python
    Jun 29 15:39:16 server-03 kernel: [ 1535]     0  1535     5276       48   0       0             0 atd
    Jun 29 15:39:16 server-03 kernel: [ 1588]     0  1588     1020       22   0       0             0 agetty
    Jun 29 15:39:16 server-03 kernel: [ 1590]     0  1590     1016       21   0       0             0 mingetty
    Jun 29 15:39:16 server-03 kernel: [ 1593]     0  1593     1016       21   0       0             0 mingetty
    Jun 29 15:39:16 server-03 kernel: [ 1597]     0  1597     1016       21   0       0             0 mingetty
    Jun 29 15:39:16 server-03 kernel: [ 1598]     0  1598     2666      109   0     -17         -1000 udevd
    Jun 29 15:39:16 server-03 kernel: [ 1602]     0  1602     1016       21   0       0             0 mingetty
    Jun 29 15:39:16 server-03 kernel: [ 1606]     0  1606     1016       21   0       0             0 mingetty
    Jun 29 15:39:16 server-03 kernel: [ 1612]     0  1612     1016       22   3       0             0 mingetty
    Jun 29 15:39:16 server-03 kernel: [20963]     0 20963    29223      181   1       0             0 crond
    Jun 29 15:39:16 server-03 kernel: [14534]     0 14534   113806     1262   3       0             0 php-fpm
    Jun 29 15:39:16 server-03 kernel: [27645]     0 27645     5417      153   1       0             0 rpc.mountd
    Jun 29 15:39:16 server-03 kernel: [27692]     0 27692     5774       63   0       0             0 rpc.idmapd
    Jun 29 15:39:16 server-03 kernel: [27711]     0 27711    16556      191   0     -17         -1000 sshd
    Jun 29 15:39:16 server-03 kernel: [13262]     0 13262    20196      241   1       0             0 master
    Jun 29 15:39:16 server-03 kernel: [13265]    89 13265    20259      260   3       0             0 qmgr
    Jun 29 15:39:16 server-03 kernel: [12081]    48 12081   113806     1204   1       0             0 php-fpm
    Jun 29 15:39:16 server-03 kernel: [12757]    48 12757   113806     1205   0       0             0 php-fpm
    Jun 29 15:39:16 server-03 kernel: [26214]    48 26214   113806     1205   0       0             0 php-fpm
    Jun 29 15:39:16 server-03 kernel: [20353]     0 20353   104880     2477   2       0             0 httpd.worker
    Jun 29 15:39:16 server-03 kernel: [ 7186]    48  7186   113806     1205   0       0             0 php-fpm
    Jun 29 15:39:16 server-03 kernel: [27006]    48 27006   113806     1206   3       0             0 php-fpm
    Jun 29 15:39:16 server-03 kernel: [12007]    48 12007    31105     1699   1       0             0 httpd.worker
    Jun 29 15:39:16 server-03 kernel: [18818]    89 18818    20216      252   1       0             0 pickup
    Jun 29 15:39:16 server-03 kernel: [22386]    48 22386  1021320   631184   0       0             0 httpd.worker
    Jun 29 15:39:16 server-03 kernel: [22460]     0 22460     1018       37   2       0             0 sleep
    Jun 29 15:39:16 server-03 kernel: [22466]    48 22466   707199   247048   3       0             0 httpd.worker
    Jun 29 15:39:16 server-03 kernel: Out of memory (oom_kill_allocating_task): Kill process 20353 (httpd.worker) score 0 or sacrifice child
    Jun 29 15:39:16 server-03 kernel: Killed process 22386, UID 48, (httpd.worker) total-vm:4085280kB, anon-rss:2509624kB, file-rss:15112kB
    Jun 29 15:39:16 server-03 kernel: Out of memory (oom_kill_allocating_task): Kill process 20353 (httpd.worker) score 0 or sacrifice child
    Jun 29 15:39:16 server-03 kernel: Killed process 22386, UID 48, (httpd.worker) total-vm:4085280kB, anon-rss:2509628kB, file-rss:15112kB
    Jun 29 15:39:16 server-03 kernel: Out of memory (oom_kill_allocating_task): Kill process 20353 (httpd.worker) score 0 or sacrifice child
    Jun 29 15:39:16 server-03 kernel: Killed process 22386, UID 48, (httpd.worker) total-vm:4085280kB, anon-rss:2509628kB, file-rss:15112kB
    Jun 29 15:39:16 server-03 kernel: Out of memory (oom_kill_allocating_task): Kill process 14534 (php-fpm) score 0 or sacrifice child
    Jun 29 15:39:16 server-03 kernel: Killed process 12081, UID 48, (php-fpm) total-vm:455224kB, anon-rss:4792kB, file-rss:24kB
    Jun 29 15:39:16 server-03 kernel: Out of memory (oom_kill_allocating_task): Kill process 14534 (php-fpm) score 0 or sacrifice child
    Jun 29 15:39:16 server-03 kernel: Killed process 12757, UID 48, (php-fpm) total-vm:455224kB, anon-rss:4792kB, file-rss:28kB
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

    \x1b[91m\x1b[1m######## OOM ISSUE ########\x1b[0m

    Service \x1b[91mhttpd.worker \x1b[0mKilled \x1b[91m5 \x1b[0mtime(s)
    Service \x1b[91mphp-fpm      \x1b[0mKilled \x1b[91m2 \x1b[0mtime(s)

    \x1b[93m\x1b[4mKEY\x1b[0m\x1b[93m
    D = Date(s) OOM
    H = Hour OOM Occurred
    O = Number of Occurrences in Date/Hour\x1b[0m

    \x1b[4mD\x1b[0m      \x1b[4mH\x1b[0m  \x1b[4m\x1b[4mO\x1b[0m
    Jun 29 15 3

    \x1b[95m\x1b[4mNote:\x1b[0m Only Showing: \x1b[92m3 \x1b[0mof the\x1b[91m 3 occurrence\x1b[0m
    Showing the \x1b[92m1st\x1b[0m, \x1b[92m2nd\x1b[0m and\x1b[92m last\x1b[0m
    \x1b[1m----------------------------------------\x1b[0m
    \x1b[1m\x1b[35mJun 29 15:39:16 \x1b[0m
    \x1b[93mSystem RAM:             \x1b[0m\x1b[36m488 MB\x1b[0m
    \x1b[93mEstimated RAM at OOM:   \x1b[0m\x1b[36m3530 MB\x1b[0m
    \x1b[93mServices\x1b[0m\x1b[91m Killed:        \x1b[0m\x1b[91mhttpd.worker \x1b[0m
    
    \x1b[4mTop 5 RAM Consumers at time of OOM:\x1b[0m
    Service: httpd.worker      (4)   3480 MB 
    Service: php-fpm           (6)     28 MB 
    Service: python            (1)     11 MB 
    Service: udevd             (3)      1 MB 
    Service: rpc.statd         (1)      0 MB 
    
    \x1b[1m----------------------------------------\x1b[0m
    \x1b[1m\x1b[35mJun 29 15:39:16 \x1b[0m
    \x1b[93mSystem RAM:             \x1b[0m\x1b[36m488 MB\x1b[0m
    \x1b[93mEstimated RAM at OOM:   \x1b[0m\x1b[36m3530 MB\x1b[0m
    \x1b[93mServices\x1b[0m\x1b[91m Killed:        \x1b[0m\x1b[91mhttpd.worker \x1b[0m
    
    \x1b[4mTop 5 RAM Consumers at time of OOM:\x1b[0m
    Service: httpd.worker      (4)   3480 MB 
    Service: php-fpm           (6)     28 MB 
    Service: python            (1)     11 MB 
    Service: udevd             (3)      1 MB 
    Service: rpc.statd         (1)      0 MB 
    
    \x1b[1m----------------------------------------\x1b[0m
    \x1b[1m\x1b[35mJun 29 15:39:16 \x1b[0m
    \x1b[93mSystem RAM:             \x1b[0m\x1b[36m488 MB\x1b[0m
    \x1b[93mEstimated RAM at OOM:   \x1b[0m\x1b[36m3530 MB\x1b[0m
    \x1b[93mServices\x1b[0m\x1b[91m Killed:        \x1b[0m\x1b[91mhttpd.worker \x1b[0m
    
    \x1b[4mTop 5 RAM Consumers at time of OOM:\x1b[0m
    Service: httpd.worker      (4)   3480 MB 
    Service: php-fpm           (6)     28 MB 
    Service: python            (1)     11 MB 
    Service: udevd             (3)      1 MB 
    Service: rpc.statd         (1)      0 MB 
    
""")


def test_output(fs, monkeypatch, capsys):
    _lf = '/var/log/messages'
    monkeypatch.setattr(oom_analyzer.GetLogData, 'checkfilesize', lambda x: True)
    monkeypatch.setattr(oom_analyzer, 'check_dmesg', lambda x: True)
    fs.CreateFile('/var/log/messages', contents=LOGFILE)
    fs.CreateFile('/proc/meminfo', contents=MEMINFO)

    oom_analyzer.catch_log_exceptions(_lf)
    out, err = capsys.readouterr()
    assert str(out) == OOMOUTPUT
