#!/usr/bin/env python
#
# Author:       Luke Shirnia
# Source:       https://github.com/LukeShirnia/out-of-memory/
# Version 2.0
"""
This script investigates out of memory issues on "supported" linux devices.
It will calculate:
- How many oom incidents there were in a specific log file
- Dates the oom incident occured
- What services were killed
- And the top RAM consumers at the time of the incident
"""
from __future__ import print_function

__version__ = 2.0

import errno
import sys
import re
import gzip
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
import platform
import datetime
import os
import fnmatch
from optparse import OptionParser
import subprocess
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)




def std_exceptions(etype, value, tb):
    """
    The following exits cleanly on Ctrl-C or EPIPE
    while treating other exceptions as before.
    """
    sys.excepthook = sys.__excepthook__
    if issubclass(etype, KeyboardInterrupt):
        pass
    elif issubclass(etype, IOError) and value.errno == errno.EPIPE:
        pass
    else:
        sys.__excepthook__(etype, value, tb)


sys.excepthook = std_exceptions

COLOURS = {
    "HEADER": "\033[95m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m",
    "ENDC": "\033[0m",
    "GREEN": "\033[92m",
    "RED": "\033[91m",
    "PURPLE": "\033[35m",
    "YELLOW": "\033[93m",
    "CYAN": "\033[36m",
    "BLUE": '\033[94m'
}


SUPPORTED = {
    "CENTOS_RHEL": ['redhat', 'centos', 'red', 'red hat', 'fedora', 'oracle'],
    "UBUNTU_DEBIAN": ['ubuntu', 'debian']
}


DEFAULT_LOGS = {
    "CENTOS_RHEL": "/var/log/messages",
    "UBUNTU_DEBIAN": "/var/log/syslog"
}


def main_header():
    '''
    Disclaimer and Script Header
    '''
    print(COLOURS["CYAN"] + "-" * 40 + COLOURS["ENDC"])
    print("      _____ _____ _____ ")
    print("     |     |     |     |")
    print("     |  |  |  |  | | | |")
    print("     |_____|_____|_|_|_|")
    print("          Analyzer")
    print("  (Out Of Memory Analyzer)")
    print("")
    print(u"\u00A9" + " 2020 LukeShirnia")
    print("")
    print(COLOURS["RED"] + COLOURS["UNDERLINE"] + "Disclaimer:" +
          COLOURS["ENDC"])
    print(COLOURS["RED"] +
          "If system OOMs too viciously, there may be nothing logged!")
    print("Do NOT take this script as FACT, " + COLOURS["YELLOW"] +
          "ALWAYS investigate further." + COLOURS["ENDC"])
    print(COLOURS["CYAN"] + "-" * 40 + COLOURS["ENDC"])


def oom_warning_header():
    '''
    Print WARNING if there is an OOM issue
    '''
    print("")
    print("{0}{1}######## OOM WARNING ########{2}".format(
        COLOURS["RED"], COLOURS["BOLD"], COLOURS["ENDC"]))
    print("{0}An out-of-memory issue has occurred on this device{1}".format(
        COLOURS["YELLOW"], COLOURS["ENDC"]))
    print("")


def log_file_overview(log_file):
    """
    Print basic log file information
    """
    print("{3}Log File:{5}   {4}{0}{5}\n{3}Start Date:{5} {4}{1}{5}\n{3}End Date:{5}  {4}{2}{5}".format(
        log_file.filename,
        datetime.datetime.strftime(log_file.startdate, '%b %d %H:%M:%S'),
        datetime.datetime.strftime(log_file.enddate, ' %b %d %H:%M:%S'),
        COLOURS["BOLD"], COLOURS["BLUE"], COLOURS["ENDC"]))
    print("")


def oom_quick_overview(multi_oom_object):
    """
    Print an overview of the incident
    """
    print("{0}Incident(s) Overview {1}".format(
                                        COLOURS["PURPLE"], COLOURS["ENDC"]))
    print("{4}Start:{6}  {0:<17}\n" \
          "{4}End:{6}    {1:>11}\n" \
          "{4}Count:{6} {5}{2:>3}{6} Incident(s)\n" \
          "{4}Total:{6} {5}{3:>3}{6} Killed Services".format(
        datetime.datetime.strftime(multi_oom_object.starttime, '%b %d %H:%M:%S'),
        datetime.datetime.strftime(multi_oom_object.endtime, '%b %d %H:%M:%S'),
        multi_oom_object.count, multi_oom_object.totalkilled,
        COLOURS["BOLD"], COLOURS["RED"], COLOURS["ENDC"]))
    print("Most Killed Service: {0} x {1}".format(multi_oom_object.killed_services[0][0],
                                           multi_oom_object.killed_services[0][1]))
    print("")


def date_breakdown(all_instances):
    #for i in all_instances:
    #    if i.starttime =
    pass


def quick_scan_header():
    """
    Print "quick scan" HEADER
    """
    print("")
    print(
        COLOURS["YELLOW"] + "#### Log File Quick Scan ####" + COLOURS["ENDC"])
    print("")
    print("{0}Opt  {1:>7}  {2:>23}{3}".format(
        COLOURS["CYAN"], "Log File", "Occurences", COLOURS["ENDC"]))


def openfile(filename):
    '''
    Check if input file is a compressed or regular file
    '''
    try:
        if filename.endswith('.gz'):
            return gzip.open(filename, "rt")
        return open(filename, "r")
    except AttributeError:
        return open(filename, "r")


def system_ram():
    '''
    Get the RAM info from /proc
    '''
    with openfile("/proc/meminfo") as mi:
        for line in mi:
            if "MemTotal" in line.strip():
                memory_value = int(int(line.split()[1]) / 1024)
                return memory_value
    return None


def verify_os_log(logf=None):
    '''
    Checks OS distribution and accepts arguments
    '''
    #  platform module is depricated in python 3.5+
    _id, _, _ = platform.dist()

    if _id.lower() not in SUPPORTED['CENTOS_RHEL'] and \
            _id.lower() not in SUPPORTED['UBUNTU_DEBIAN']:
        raise Exception("Unsupported OS")

    # If log file has been specificed by the user
    if logf and os.path.exists(logf):
        oom_log = logf
        return oom_log
    elif logf and not os.path.exists(logf):
        raise Exception("File Not Found")

    # Obtaining system default log files if no log file specified
    if not logf and _id.lower() in SUPPORTED["CENTOS_RHEL"]:
        oom_log = DEFAULT_LOGS["CENTOS_RHEL"]
    elif not logf and _id.lower() in SUPPORTED["UBUNTU_DEBIAN"]:
        oom_log = DEFAULT_LOGS["UBUNTU_DEBIAN"]
    else:
        raise Exception("Unsupported OS")

    if (float(os.stat(oom_log).st_size) / 1024) / 1024 == 0:
        raise Exception("Empty Log File")

    return oom_log


class log_info(object):
    """
    Obtain relevant information about a specific log file
    """
    def __init__(self, log):
        self.log = log
        self.startdate, self.oomcount, self.enddate = self.get_info()

    def __repr__(self):
        return self.log + ".obj"

    @property
    def filename(self):
        return self.log

    @property
    def size(self):
        """
        Return the size of the file
        """
        if os.path.isfile(self.log):
            file_info = os.stat(self.log)
            return (float(file_info.st_size) / 1024) / 1024
        return 0

    @property
    def namelength(self):
        return len(self.log)

    def get_info(self):
        start = ""
        count = 0
        f = openfile(self.log)
        for line in f:
            if not start:
                start = datetime.datetime.strptime(
                    " ".join(line.split()[0:3]), "%b %d %H:%M:%S")
            if "[ pid ]   uid  tgid total_vm      rss" in line.strip():
                count += 1
        end = datetime.datetime.strptime(
            " ".join(line.split()[0:3]), "%b %d %H:%M:%S")
        return start, count, end


def find_all_logs(log, exclude=False):
    """
    Find all logs (compresses and non compresses)
    Return log_info object for each file
    """
    results = []
    split_log_file_dir = os.path.dirname(log)
    split_log_file_name = os.path.basename(log)
    split_log_file_name = split_log_file_name + '*'
    for root, _, files in os.walk(split_log_file_dir):
        for name in files:
            if fnmatch.fnmatch(name, split_log_file_name):
                # Exclude main log file if it has been checked already
                if exclude and log == os.path.join(root, name):
                    continue
                else:
                    results.append(log_info(os.path.join(root, name)))
    results.sort(key=lambda x: x.filename)
    return results


def select_option(options_dict):
    print("")
    while True:
        tty = open('/dev/tty')
        print("Which log would you like to check? (select opt #): "),
        option_selected = tty.readline().strip()
        tty.close()
        if option_selected.isdigit():
            option_selected = int(option_selected)
            if options_dict.get(option_selected):
                print("")
                return options_dict[option_selected]
            else:
                print("{0}Option {1} is not available{2}, "
                      "please try again.".format(
                       COLOURS["RED"], option_selected, COLOURS["ENDC"]))
        else:
            print("{0}Error:{1} Please select a suitable number".format(
                COLOURS["RED"], COLOURS["ENDC"]))


def log_quick_scan(log):
    """
    Quickly display the log_info.oomcount for all discovered logs
    """
    all_logs = find_all_logs(log.filename)
    option = 1
    selections = {}
    log_length = max(log.namelength for log in all_logs)
    for l in all_logs:
        count = l.oomcount
        if count >= 1:
            print("{0} - {1:<{2}} {3}".format(
                    option, l.filename, log_length, count))
            selections[option] = l
            option += 1
        else:
            print("  - {0:<{1}} {2}".format(l.filename, log_length, count))

    return select_option(selections)


class single_oom_instance(object):
    def __init__(self, starttime, service_dict, killed_services):
        self.starttime = starttime
        self.service_dict = service_dict
        self.killed = killed_services
        self.count = 1

    def __repr__(self):
        return "{0}-{1}.obj".format(
            __class__.__name__,
            datetime.datetime.strftime(self.starttime, '%H:%M:%S'))

    def __add__(self, other):
        all_starttimes = [self.starttime] + [other.starttime]
        all_starttimes.sort()
        all_killed = self.killed + other.killed
        self.count += 1
        return multi_oom_overview(all_starttimes, all_killed, self.count)

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)

    @property
    def killed_services(self):
        return [(x, self.killed.count(x)) for x in set(self.killed)]

    @property
    def mem_info(self):
        for key in self.service_dict:
            total = (sum(self.service_dict[key]) / 1024 * 4)
            self.service_dict[key] = total
        ordered = sorted(((round(value), key)
                         for (key, value) in
                         self.service_dict.items()), reverse=True)
        return ordered


class multi_oom_overview(object):
    def __init__(self, starttimes, killed_services, count):
        self.killed = killed_services
        self.alldates = starttimes
        self.count = count

    def __repr__(self):
        return "{0}-{1}-{2}.obj".format(
            __class__.__name__,
            datetime.datetime.strftime(self.starttime, '%H:%M:%S'),
            datetime.datetime.strftime(self.endtime, '%H:%M:%S'))

    def __add__(self, other):
        all_starttimes = self.alldates + [other.starttime]
        all_killed = self.killed + other.killed
        self.count += 1
        return multi_oom_overview(all_starttimes, all_killed, self.count)

    @property
    def killed_services(self):
        k = [(x, self.killed.count(x)) for x in set(self.killed)]
        k.sort(key=lambda x: x[1])
        return k[::-1]

    @property
    def totalkilled(self):
        return sum(x[1] for x in self.killed_services)

    @property
    def starttime(self):
        return self.alldates[0]

    @property
    def endtime(self):
        return self.alldates[-1]

    def averageconsumption(self):
        pass


def incident_check(oom_objects, log_object):
    """
    Check if an incident has occurred
    """
    if not oom_objects:
        print("")
        print("No OOOM Incident Occurred in this file")
        print("")
        return
    
    oom_warning_header()
    log_file_overview(log_object)
    oom_quick_overview(sum(oom_objects))
    date_breakdown(oom_objects)

    return oom_objects


def get_oom_info(log_object):
    """
    Scan through log file and obtain all relevent information
    on each oom incident
    """
    incident_record = False
    record_killed_services = False
    oom_objects = []
    oom_incident = {}
    with openfile(log_object.filename) as report:
        for line in report:
            killed = re.search("Killed process (.*) total", line)
            line = re.sub(r"[^a-zA-Z0-9-_.:]+", ' ', line)
            if "pid uid tgid total_vm rss" in line.strip() \
                    and "kernel" in line.lower():
                # Initiating dict to record information for
                # an instance of an incident

                if oom_incident:
                    oom_objects.append(
                        single_oom_instance(
                            incident_time, oom_incident, killed_services))

                # Resetting dict for next oom incident
                oom_incident.clear()
                incident_record = True

                killed_services = []
                rss_column = line.split().index("rss")
                incident_time = datetime.datetime.strptime(
                    " ".join(line.split()[0:3]), "%b %d %H:%M:%S")

            elif "Out of memory" in line.strip() and incident_record or \
                    len(line.split()) < 14 and incident_record:
                incident_record = False  # Stop recording of process values
                record_killed_services = True

            elif incident_record and "kernel" in line.lower():
                service = line.split()[-1]
                service_value = int(line.split()[rss_column])
                oom_incident.setdefault(service, []).append(service_value)

            elif record_killed_services and killed:
                killed_process = killed.group(1)
                killed_process = \
                    killed_process.split(",")[-1].strip("0123456789 ()")
                killed_services.append(killed_process)

    # Make sure the trailing oom instance is added to the list
    if oom_incident:
        oom_objects.append(
            single_oom_instance(incident_time, oom_incident, killed_services))

    return incident_check(oom_objects, log_object)


def main():
    '''
    Usage and help overview - Option parsing
    '''
    parser = OptionParser(usage='usage: %prog [option]')
    parser.add_option(
        "-q", "--quick",
        dest="quick",
        action="store_true",
        help="Quick Search all rotated system files")
    parser.add_option(
        "-f", "--file",
        dest="file",
        action="store_true",
        metavar="File",
        help="Specify a log to check")
    parser.add_option(
        "-o", "--override",
        dest="override",
        action="store_true",
        help="Override the 300MB file limit")
    parser.add_option(
        "-V", "--version",
        dest="version",
        action="store_true",
        help="Display the scripts version number")

    (options, args) = parser.parse_args()

    if not options.file:
        system_log_object = log_info(verify_os_log())

    if not options.version:
        main_header()

    if options.quick:
        quick_scan_header()
        get_oom_info(log_quick_scan(system_log_object))
        sys.exit(0)
    elif options.file:
        system_log_object = log_info(verify_os_log(logf=args[0]))

    if options.version:
        print(__version__)

    if not options.version:
        get_oom_info(system_log_object)


if __name__ == '__main__':
    #try:
    main()
    #except Exception as error:
    #    print("")
    #    print(COLOURS["RED"] + "Error:" + COLOURS["ENDC"])
    #    print(error)
    #    print("")
    #    print(COLOURS["BOLD"] + "-" * 40 + COLOURS["ENDC"])
