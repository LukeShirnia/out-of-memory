import pytest
import oom_analyzer
import mock
import textwrap


LOGFILE = textwrap.dedent("""\
        Apr 12 10:23:56 cloud-web1 kernel: [668192.306121] [ pid ]   uid  tgid total_vm      rss cpu oom_adj oom_score_adj name
        Apr 12 10:23:56 cloud-web1 kernel: [668192.306910] [ 1060]     0  1060     2767       22   0     -17         -1000 udevd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.307585] [ 2257]     0  2257    15901      114   9       0             0 vmtoolsd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.308258] [ 2459]     0  2459    23289       44   0     -17         -1000 auditd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.308888] [ 2483]     0  2483     1541        2   9       0             0 portreserve
        Apr 12 10:23:56 cloud-web1 kernel: [668192.309523] [ 2493]     0  2493    62464     1197   0       0             0 rsyslogd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.310167] [ 2508]     0  2508     4604       62  21       0             0 irqbalance
        Apr 12 10:23:56 cloud-web1 kernel: [668192.310762] [ 2526]    32  2526     4745       25   0       0             0 rpcbind
        Apr 12 10:23:56 cloud-web1 kernel: [668192.311362] [ 2573]     0  2573   145590      227  18       0             0 savd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.311944] [ 2648]    29  2648     6894        2   0       0             0 rpc.statd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.312514] [ 2685]    81  2685     5359        3   0       0             0 dbus-daemon
        Apr 12 10:23:56 cloud-web1 kernel: [668192.313075] [ 2776]     0  2776     1020        1  19       0             0 acpid
        Apr 12 10:23:56 cloud-web1 kernel: [668192.313606] [ 2788]    68  2788     9805      362  18       0             0 hald
        Apr 12 10:23:56 cloud-web1 kernel: [668192.314128] [ 2789]     0  2789     5100        2   4       0             0 hald-runner
        Apr 12 10:23:56 cloud-web1 kernel: [668192.314657] [ 2822]     0  2822     5630        2   0       0             0 hald-addon-inpu
        Apr 12 10:23:56 cloud-web1 kernel: [668192.315164] [ 2835]    68  2835     4502        2   7       0             0 hald-addon-acpi
        Apr 12 10:23:56 cloud-web1 kernel: [668192.315637] [ 3232]     0  3232     1572        1  19       0             0 mcelog
        Apr 12 10:23:56 cloud-web1 kernel: [668192.316104] [ 3244]     0  3244    50655      175  12       0             0 snmpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.316556] [ 3268]     0  3268    16559       24  23     -17         -1000 sshd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.316992] [ 3279]    38  3279     7685       37  16       0             0 ntpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.317417] [ 3293]     0  3293    13032       20   7       0             0 vsftpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.317837] [ 3330]     0  3330    27054        2   7       0             0 mysqld_safe
        Apr 12 10:23:56 cloud-web1 kernel: [668192.318241] [ 3513]    27  3513   136464     1299  20       0             0 mysqld
        Apr 12 10:23:56 cloud-web1 kernel: [668192.318618] [ 3542]     0  3542    16610        1   2       0             0 saslauthd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.318996] [ 3543]     0  3543    16610        1   3       0             0 saslauthd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.319385] [ 3544]     0  3544    16610        1   3       0             0 saslauthd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.319729] [ 3546]     0  3546    16610        1   3       0             0 saslauthd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.320046] [ 3547]     0  3547    16610        1   3       0             0 saslauthd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.320354] [ 3580]   495  3580     4065        2  21       0             0 nrsysmond
        Apr 12 10:23:56 cloud-web1 kernel: [668192.320655] [ 3582]   495  3582    62700      571  13       0             0 nrsysmond
        Apr 12 10:23:56 cloud-web1 kernel: [668192.320943] [ 3677]     0  3677    20225       27   4       0             0 master
        Apr 12 10:23:56 cloud-web1 kernel: [668192.321236] [ 3690]    89  3690    20386       20   9       0             0 qmgr
        Apr 12 10:23:56 cloud-web1 kernel: [668192.321519] [ 3713]     0  3713    45758        2  13       0             0 abrtd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.321798] [ 3734]    89  3734    20300       48   7       0             0 anvil
        Apr 12 10:23:56 cloud-web1 kernel: [668192.322093] [ 3742]     0  3742   133283     2040  12       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.322374] [ 3830]     0  3830   387187     1896  22       0             0 newrelic-daemon
        Apr 12 10:23:56 cloud-web1 kernel: [668192.322745] [ 3836]     0  3836   610323    39610   2       0             0 newrelic-daemon
        Apr 12 10:23:56 cloud-web1 kernel: [668192.323024] [ 3867]     0  3867   109540     1444  23       0             0 rackspace-monit
        Apr 12 10:23:56 cloud-web1 kernel: [668192.323346] [ 3883]     0  3883    51665      837  15       0             0 osad
        Apr 12 10:23:56 cloud-web1 kernel: [668192.323635] [ 3895]     0  3895    29219       21   7       0             0 crond
        Apr 12 10:23:56 cloud-web1 kernel: [668192.323903] [ 3924]     0  3924    28081       35   0       0             0 varnishd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.324178] [ 3980]     0  3980     5277        1  11       0             0 atd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.324440] [ 4007]     0  4007    25234       11   2       0             0 rhnsd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.324701] [ 4222]     0  4222    69324       53   4       0             0 cvlaunchd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.324964] [ 4223]     0  4223   530813      595   5       0             0 cvd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.325243] [ 4224]     0  4224   222952      182  11       0             0 EvMgrC
        Apr 12 10:23:56 cloud-web1 kernel: [668192.325506] [ 4271]     0  4271     2393       10  19       0             0 nimbus
        Apr 12 10:23:56 cloud-web1 kernel: [668192.325774] [ 4273]     0  4273    23067       46   2       0             0 controller
        Apr 12 10:23:56 cloud-web1 kernel: [668192.326046] [ 4531]     0  4531    22547      220  14       0             0 miniserv.pl
        Apr 12 10:23:56 cloud-web1 kernel: [668192.326316] [ 4541]     0  4541     1016        2  10       0             0 mingetty
        Apr 12 10:23:56 cloud-web1 kernel: [668192.326575] [ 4543]     0  4543     1016        2  10       0             0 mingetty
        Apr 12 10:23:56 cloud-web1 kernel: [668192.326829] [ 4545]     0  4545     1016        2  10       0             0 mingetty
        Apr 12 10:23:56 cloud-web1 kernel: [668192.327097] [ 4547]     0  4547     1016        2  10       0             0 mingetty
        Apr 12 10:23:56 cloud-web1 kernel: [668192.327342] [ 4549]     0  4549     2663       35   1     -17         -1000 udevd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.327588] [ 4550]     0  4550     2663       23   0     -17         -1000 udevd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.327830] [ 4551]     0  4551     1016        2  15       0             0 mingetty
        Apr 12 10:23:56 cloud-web1 kernel: [668192.328087] [ 4553]     0  4553     1016        2   2       0             0 mingetty
        Apr 12 10:23:56 cloud-web1 kernel: [668192.328328] [ 4640]     0  4640    21899       36   5       0             0 spooler
        Apr 12 10:23:56 cloud-web1 kernel: [668192.377508] [65139]     0 65139     2835       42  11       0             0 sh
        Apr 12 10:23:56 cloud-web1 kernel: [668192.377727] [65140]     0 65140    19265      546  21       0             0 rpm
        Apr 12 10:23:56 cloud-web1 kernel: [668192.377933] [65144]    48 65144   135102     5708  13       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.378161] [65145]     0 65145    16009      144   3       0             0 sshd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.378381] [65146]    48 65146   133283     2310   9       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.378603] [65147]    48 65147    59175     3187   8       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.378809] [65148]    48 65148   133324     2651   9       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.379039] [65149]    48 65149   133324     2641   3       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.379251] [65150]    48 65150   133283     2313   9       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.379456] [65151]    48 65151   133283     2141  17       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.379677] [65152]    48 65152   133398     2579   7       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.379882] [65153]     0 65153    16009      144  15       0             0 sshd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.380112] [65154]    48 65154   133283     2145  10       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.380312] [65155]    48 65155   133283     2144  15       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.380521] [65156]     0 65156    14063       86  23       0             0 vsftpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.380732] [65157]    48 65157   133283    19144   1       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.380943] [65158]    48 65158   133283    19144   3       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.381149] [65159]    48 65159   133283    19145  10       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.381356] [65160]    48 65160   133283    19145  11       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.381565] [65161]    48 65161   133283    19145   9       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.381565] [65161]    48 65161   133283    19145   9       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.381565] [65161]    48 65161   133283    19145   9       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.381565] [65161]    48 65161   133283    19145   9       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.381565] [65161]    48 65161   133283    19145   9       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.381565] [65161]    48 65161   133283    19145   9       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.381565] [65161]    48 65161   133283    19145   9       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.381565] [65161]    48 65161   133283    19145   9       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.381565] [65161]    48 65161   133283    19145   9       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.381565] [65161]    48 65161   133283    19145   9       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.381565] [65161]    48 65161   133283    19145   9       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.381757] [65162]    48 65162   133283    19145  13       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.381961] [65163]    48 65163   133283    19144   2       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.382173] [65164]    48 65164   133283    12145  14       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.382377] [65165]    48 65165   133283    12144  14       0             0 httpd
        Apr 12 10:23:56 cloud-web1 kernel: [668192.382572] [65166]    48 65166   133283    12144   1       0             0 httpd
        Apr 12 10:23:59 cloud-web1 kernel: [668192.382766] [65168]    48 65168   133283    12145  20       0             0 httpd
        Apr 12 10:23:59 cloud-web1 kernel: [668192.382971] [65169]    48 65169   133283    12145  21       0             0 httpd
        Apr 12 10:23:59 cloud-web1 kernel: [668192.383166] [65170]    99 65170    13561       83  20       0             0 vsftpd
        Apr 12 10:23:59 cloud-web1 kernel: [668192.383358] [65172]    48 65172   133283     2164   0       0             0 httpd
        Apr 12 10:23:59 cloud-web1 kernel: [668192.383551] [65173]     0 65173   133283     1996   2       0             0 httpd
        Apr 12 10:23:59 cloud-web1 kernel: [668192.383737] Out of memory: Kill process 62185 (httpd) score 5 or sacrifice child
        Apr 12 10:23:59 cloud-web1 kernel: [668192.383946] Killed process 62185, UID 48, (httpd) total-vm:732728kB, anon-rss:198916kB, file-rss:2288kB
""")


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


OOMOUTPUT = textwrap.dedent("""\

    \x1b[4mLog Information\x1b[0m
    \x1b[92mLog File  : \x1b[93m /var/log/messages \x1b[0m
    \x1b[92mStart date: \x1b[0m\x1b[93m Apr, 12, 10:23:56 \x1b[0m
    \x1b[92mEnd Date  : \x1b[0m\x1b[93m Apr, 12, 10:23:59 \x1b[0m

    \x1b[91m\x1b[1m######## OOM ISSUE ########\x1b[0m

    Number of OOM occurrence in log file: 1 
    Service \x1b[91mhttpd        \x1b[0mKilled \x1b[91m1 \x1b[0mtime(s)

    \x1b[93m\x1b[4mKEY\x1b[0m\x1b[93m
    D = Date(s) OOM
    H = Hour OOM Occurred
    O = Number of Occurrences in Date/Hour\x1b[0m

    \x1b[4mD\x1b[0m      \x1b[4mH\x1b[0m  \x1b[4m\x1b[4mO\x1b[0m
    Apr 12 10 1

    \x1b[1m----------------------------------------\x1b[0m
    \x1b[1m\x1b[35mApr 12 10:23:56 \x1b[0m
    \x1b[93mSystem RAM:             \x1b[0m\x1b[36m1833 MB\x1b[0m
    \x1b[93mEstimated RAM at OOM:   \x1b[0m\x1b[36m1838 MB\x1b[0m
    \x1b[93mServices\x1b[0m\x1b[91m Killed:        \x1b[0m\x1b[91mhttpd \x1b[0m

    \x1b[4mTop 5 RAM Consumers at time of OOM:\x1b[0m
    Service: httpd            (35)   1641 MB 
    Service: newrelic-dae      (2)    162 MB 
    Service: mysqld            (1)      5 MB 
    Service: rackspace-mo      (1)      5 MB 
    Service: rsyslogd          (1)      4 MB 

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
