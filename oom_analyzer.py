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


class Colours(object):
    '''
    Class used for colour formatting
    '''
    HEADER = '\033[95m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    PURPLE = '\033[35m'
    LIGHTRED = '\033[91m'
    CYAN = '\033[36m'
    UNDERLINE = '\033[4m'


SUPPORTED = {
    "CENTOS_RHEL": ['redhat', 'centos', 'red', 'red hat', 'fedora', 'oracle'],
    "UBUNTU_DEBIAN": ['ubuntu', 'debian']
}


def print_header():
    '''
    Disclaimer and Script Header
    '''
    print(Colours.CYAN + "-" * 40 + Colours.ENDC)
    print("      _____ _____ _____ ")
    print("     |     |     |     |")
    print("     |  |  |  |  | | | |")
    print("     |_____|_____|_|_|_|")
    print("    Out Of Memory Analyzer")
    print("")
    print("Copyright 2019 LukeShirnia")
    print("")
    print(Colours.RED + Colours.UNDERLINE + "Disclaimer:" + Colours.ENDC)
    print(Colours.RED +
          "If system OOMs too viciously, there may be nothing logged!")
    print("Do NOT take this script as FACT, investigate further." +
          Colours.ENDC)
    print(Colours.CYAN + "-" * 40 + Colours.ENDC)


def neat_oom_invoke():
    '''
    Print WARNING if there is an OOM issue
    '''
    print(Colours.RED + Colours.BOLD + "######## OOM ISSUE ########" +
          Colours.ENDC)
    print("")


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


def system_resources():
    '''
    Get the RAM info from /proc
    '''
    meminfo = openfile("/proc/meminfo")
    for lines in meminfo:
        if "MemTotal" in lines.strip():
            memory_value = int(lines.split()[1])
            system_memory = int(memory_value / 1024)
            return system_memory
    return None


def strip_line(line):
    '''
    Stripping all non required characters from the line so not to
    interfere with line.split()
    '''
    for x in ["[", "]", "}", "{", "'", "(", ")"]:
        if x in line:
            line = line.replace(x, "")
    return line


class GetLogData(object):
    """
    Obtain information from the log file selected
    """

    def __init__(self, logfile):
        self._logfile = logfile
        self._size = 0
        self._info = ''

    def lastlistgzip(self):
        """
        Reads file in chunks to reduce memory footprint
        saves last 2 chunks, combines and finds the last line
        """
        in_file = openfile(self._logfile)
        line = ''
        chunks = ['', '']
        while 1:
            chunk = in_file.read(512*512)
            if not chunk:
                break
            del chunks[0]
            chunks.append(chunk)

        data = StringIO(''.join(chunks))
        for line in data:
            pass
        return line

    def size_of_file(self):
        """
        This function will return the file size of the script.
        Currently HUGE OOM log file will cause memory issues,
        this is to prevent that
        """
        if os.path.isfile(self._logfile):
            file_info = os.stat(self._logfile)
            return (float(file_info.st_size) / 1024) / 1024
        return 0

    def checkfilesize(self, skip=False):
        """
        Checking the size of the file isn't > 250MB
        This prevents script getting too large on a box that already has
        RAM issues.
        """
        if skip:
            print()
            print(Colours.RED +
                  "*****WARNING: SKIPPING FILE SIZE CHECK*****" + Colours.ENDC)
            print(Colours.RED +
                  "****Risk of OOM issues on small devices****" + Colours.ENDC)
            print()
            return True

        self._size = self.size_of_file()
        if self._size >= 300:
            print("")
            print("!!! File is too LARGE !!!")
            print("Size: {0} MB".format(int(self._size)))
            print()
            print("Investigating this {0}MB log file could cause memory issues"
                  " on small servers"
                  .format(int(self._size)))
            print("Please consider splitting the file into smaller"
                  "chunks (such as dates)")
            print()
            sys.exit(1)
        elif self._size == 0:
            print()
            print(Colours.UNDERLINE + "Log Information" + Colours.ENDC)
            print(Colours.GREEN +
                  "Log File  : " + Colours.YELLOW + " %s " % (
                                            self._logfile) + Colours.ENDC)
            print(Colours.RED +
                  "File appears to be empty" +
                  Colours.ENDC.format(self._logfile))
            print()
            sys.exit(1)
        else:
            return True

    def startdate(self):
        """
        Gets the log file start date from the first line of the file
        """
        f = openfile(self._logfile)
        for line in f:
            return line.split()[0:3]

    def enddate(self):
        """
        Get the end date of log file from the last line of the file
        """
        return self.lastlistgzip().split()[0:3]

    def information(self):
        """
        Gather and return log file start and end date
        """
        # If override flag specificed, skip the file check
        enddate = self.enddate()
        startdate = self.startdate()
        return (startdate, enddate)


def print_oom_output(
        i, date_format, oom_incident, service_value_list):
    '''
    Print the Output of an OOM incident (Inc TOP 5 RAM consumers)
    '''
    print(Colours.BOLD + "-" * 40 + Colours.ENDC)
    print(Colours.BOLD + Colours.PURPLE + "{0} ".format(
        date_format[i - 1]) + Colours.ENDC)
    print(Colours.YELLOW + "System RAM:             " + Colours.ENDC +
          Colours.CYAN + "{0:<1} MB".format(system_resources()) + Colours.ENDC)
    print(Colours.YELLOW + "Estimated RAM at OOM:   " + Colours.ENDC +
          Colours.CYAN + "{0:<3} MB".format(int(sum(
            oom_incident[i]['total_rss'] * 4) / 1024)) + Colours.ENDC)
    print(Colours.YELLOW + "Services" + Colours.ENDC + Colours.RED +
          " Killed:        " + Colours.ENDC + Colours.RED + "{0} ".format(
            ", ".join(oom_incident[i]['killed_services'])) + Colours.ENDC)
    print("")
    print(Colours.UNDERLINE +
          "Top 5 RAM Consumers at time of OOM:" + Colours.ENDC)

    for x in service_value_list[i]:
        _service_name = x[0]
        _process_count = "(%s)" % x[1]
        _service_mb = int(x[2])
        print("Service: {0:<16} {1:>4} {2:>6} MB ".format(
            _service_name[:12], _process_count, _service_mb))

    print("")


def check_if_incident(
        counter, oom_incident, service_value_list, oom_lf,
        all_killed_services):
    '''
    Check if OOM incident occurred.
    '''
    oom_dates = []
    oom_number = 1
    for j in range(1, counter):
        for k in oom_incident[j]['oom_date_count']:
            oom_dates.append(datetime.datetime.strftime(k, '%b %d %H:%M:%S'))
            oom_number += 1
    oom_dates.sort()

    showlogoverview(oom_lf, oom_number, all_killed_services)
    counter = counter - 1

    if counter == 1:  # if only 1 instance of oom then print all
        date_check(oom_dates)
        i = 1
        print_oom_output(
            i, oom_dates, oom_incident, service_value_list)
    elif counter == 2:  # if only 3 instance of oom then print all
        date_check(oom_incident)
        for i in (1, 2):
            print_oom_output(
                i, oom_dates, oom_incident, service_value_list)
    elif counter >= 3:  # if more 3 or more oom instances, print 1st, 2nd, last
        date_check(oom_incident)
        for i in (1, 2, counter - 1):
            print_oom_output(
                i, oom_dates, oom_incident, service_value_list)
    else:
        print("-" * 40)
        print("OOM has " + Colours.GREEN + "NOT" + Colours.ENDC +
              " occured in specified log file!")
        print("-" * 40)
        print("")
        # print similar log files to check for an issue
        qc_all_logs(locate_all_logs(oom_lf, option='exclude'))
        print("")


def locate_all_logs(oom_log, option=None):
    '''
    This function finds all log files in the directory of
    default log file (or specified log file)
    '''
    result = []
    split_log_file_dir = os.path.dirname(oom_log)
    split_log_file_name = os.path.basename(oom_log)
    split_log_file_name = split_log_file_name + '*'
    for root, _, files in os.walk(split_log_file_dir):
        for name in files:
            if fnmatch.fnmatch(name, split_log_file_name):
                result.append(os.path.join(root, name))
    result.sort()
    if len(result) > 1:
        print(Colours.YELLOW +
              "Checking other logs, select an option:" + Colours.ENDC)
        if option == 'exclude':
            while oom_log in result:
                result.remove(oom_log)
    return result


def qc_all_logs(results):
    '''
    Quickly check all log files for oom incidents
    (used when --quick option is invoked)
    '''
    option = 1
    next_logs_to_search = []
    del next_logs_to_search[:]
    for i in results:
        total_occurences = []
        del total_occurences[:]
        total_occurences = 0
        f = openfile(i)
        for line in f:
            if "[ pid ]   uid  tgid total_vm      rss" in line.strip():
                total_occurences += 1
        if total_occurences >= 1:
            print(Colours.GREEN + "Option: {0}".format(option) + Colours.ENDC +
                  "  {0:26} - Occurrences: {1}".format(i, total_occurences))
            next_logs_to_search.append(i)
            option += 1
        else:
            print("           {0:26} - Occurrences: {1}".format(
                i, total_occurences))
    select_next_logfile(next_logs_to_search)


def select_next_logfile(log_file):
    '''
    This function is for the user to select the next log file they wish to
    inspect `if OOM count >= 1` in another log file
    (inspected in the previous function)
    '''
    if len(log_file) >= 1:
        print("")
        incorrect = True
        while incorrect:
            not_integer = True
            while not_integer:
                print("Which file should we check next?")
                tty = open('/dev/tty')
                print("Select an option number between" + Colours.GREEN +
                      " 1 " + Colours.ENDC + "and " + Colours.GREEN +
                      str(len(log_file)) + Colours.ENDC + ": ")
                option_answer = tty.readline().strip()
                tty.close()
                if option_answer.isdigit():
                    option_answer = int(option_answer)
                    option_answer -= 1
                    if (option_answer) <= (len(log_file) - 1) and \
                            (option_answer) >= 0:
                        new_log_file = log_file[option_answer]
                        oom_record(new_log_file)
                        incorrect = False
                        not_integer = False
                    else:
                        print("Option number out of range, try again")
                        print("")
                else:
                    print("Please select a number")


class DmesgInfo(object):
    """
    Obtain information from dmesg regarding oom issues
    """
    def __init__(self, oom_count):
        self.oom_count = oom_count
        self.dmesg_count = []

    def dmesg_output(self):
        '''
        Open a subprocess to read the output of the dmesg command line-by-line
        '''
        devnull = open(os.devnull, 'wb')
        p = subprocess.Popen(
            ("dmesg"), shell=True, stdout=subprocess.PIPE, stderr=devnull)
        for line in p.stdout:
            yield line
        p.wait()
        devnull.close()

    def compare_dmesg(self):
        '''
        Compare dmesg to syslog oom report
        '''
        if len(self.dmesg_count) > self.oom_count and self.oom_count == 0:
            print("")
            print(Colours.YELLOW +
                  "Dmesg reporting errors but log files are empty...")
            print("Log files appear to have been rotated" + Colours.ENDC)
            print("")
            print("dmesg incidents: ", len(self.dmesg_count))
        elif len(self.dmesg_count) > self.oom_count:
            print("")
            print(Colours.YELLOW + "Note: " + Colours.ENDC + "More reported " +
                  Colours.RED + "errors " + Colours.ENDC + "in dmesg " +
                  Colours.PURPLE + "({0})".format(
                    len(self.dmesg_count)) + Colours.ENDC +
                  " than current log file " + Colours.PURPLE + "({0})".format(
                   self.oom_count) + Colours.ENDC)
            print("Run with " + Colours.GREEN + "--quick" + Colours.ENDC +
                  " option to check available log files")
            print("")

    def check_dmesg(self):
        '''
        Read each line and search for oom string
        '''
        for dmesg_line in self.dmesg_output():
            if b"[ pid ]   uid  tgid total_vm      rss" in dmesg_line.lower():
                self.dmesg_count.append(dmesg_line.strip())
        self.dmesg_count = list(filter(None, self.dmesg_count))
        self.compare_dmesg()


def showlogoverview(oom_lf, oom_number, all_killed_services):
    '''
    Get the start and end date of the current log file
    '''
    gld = GetLogData(oom_lf)
    try:
        first_line, last_line = gld.information()
    except IndexError:
        print("")
        print("File appears to be corrupt or empty")
        print("Please check:")
        print("             {0}".format(oom_lf))
        print("")
        sys.exit(1)
    print("")
    print(Colours.UNDERLINE + "Log Information" + Colours.ENDC)
    print(Colours.GREEN +
          "Log File  : " + Colours.YELLOW + " %s " % (oom_lf) + Colours.ENDC)
    print(Colours.GREEN +
          "Start date: " + Colours.ENDC + Colours.YELLOW + " %s " % (
            ", ".join(first_line)) + Colours.ENDC)
    print(Colours.GREEN +
          "End Date  : " + Colours.ENDC + Colours.YELLOW + " %s " % (
            ", ".join(last_line)) + Colours.ENDC)
    print("")
    if oom_number > 4:
        neat_oom_invoke()
        print("Number of OOM occurrence in log file: " +
              Colours.RED + " %s " % (oom_number - 1) + Colours.ENDC)
    elif oom_number <= 4 and ( oom_number - 1 ) > 0:
        neat_oom_invoke()
        print("Number of OOM occurrence in log file: %s " % ((oom_number - 1)))
    else:
        print("Number of OOM occurrence in log file: %s " % ((oom_number - 1)))
        print("")
    all_killed_services = dict(
        (i, all_killed_services.count(i)) for i in all_killed_services)
    service_count = sorted(
        ((v, k) for k, v in all_killed_services.items()), reverse=True)
    for i in service_count:
        print("Service " + Colours.RED + "{0:12} ".format(i[1]) +
              Colours.ENDC + "Killed " + Colours.RED + "{0} ".format(i[0]) +
              Colours.ENDC + "time(s)")
    print("")


def save_values(line, column_number):
    '''
    This function processes each line (when record = True)
    and saves the rss value and process name .eg (51200, apache)
    '''
    cols = line.split()
    string = cols[column_number-1], cols[-1]
    return string


def add_rss_for_processes(unique, list_of_values):
    '''
    Adding the RSS value of each service
    '''
    values_to_add = []
    total_service_usage = []
    del total_service_usage[:]
    for i in unique:
        counter = 0
        del values_to_add[:]
        for x in list_of_values:
            if i == x[1]:
                try:
                    counter += 1
                    number = int(x[0])
                    values_to_add.append(number)
                except Exception:
                    pass
        added_values = (sum(values_to_add) * 4) / 1024  # work out rss in MB
        string = i, counter, added_values
        total_service_usage.append(string)
    return total_service_usage


def date_time(line):
    '''
    Creates a date object from an extracted string
    retreived from the log line
    '''
    date_of_oom = " ".join(line.split()[0:3])
    _date = datetime.datetime.strptime(
        date_of_oom, "%b %d %H:%M:%S")
    return _date


def strip_time(_dt):
    '''
    Used to summarise the hour OOM's occurred (excludes the mins and seconds)
    '''
    return _dt + datetime.timedelta(
        hours=1, minutes=-_dt.minute, seconds=-_dt.second)


def date_time_counter_split(dates_sorted):
    '''
    Split the date and OOM count ('May 12': 1) into 2 strings and
    back into 1 string
    '''
    sorted_dates = []
    for i in dates_sorted:
        date = datetime.datetime.strptime(i[0], "%m-%d %H")
        date = datetime.datetime.strftime(date, "%b %d %H")
        occurences = i[1]
        sorted_dates.append(date + " " + str(occurences))
    return sorted_dates


def date_check(oom_incident):
    '''
    The function is used to produce a list of dates +inc hour of every oom
    occurrence in the log file
    '''
    dates_test = []
    dates_sorted = []
    for j in oom_incident.keys():
        for i in oom_incident[j]['oom_date_count']:
            dates_test.append(datetime.datetime.strftime(i, '%m-%d %H'))
    occurrences = len(dates_test)

    dates_test = dict((i, dates_test.count(i)) for i in dates_test)
    dates_sorted = sorted(dates_test.items())
    dates_test = date_time_counter_split(dates_sorted)
    print(Colours.YELLOW + Colours.UNDERLINE + "KEY" + Colours.ENDC +
          Colours.YELLOW)
    print("D = Date(s) OOM")
    print("H = Hour OOM Occurred")
    print("O = Number of Occurrences in Date/Hour" + Colours.ENDC)
    print("")
    print(Colours.UNDERLINE + "D" + Colours.ENDC + "      " +
          Colours.UNDERLINE + "H" + Colours.ENDC + "  " + Colours.UNDERLINE +
          Colours.UNDERLINE + "O" + Colours.ENDC)
    for value in dates_test:
        print(value)
    print("")
    if occurrences >= 3:
        print(Colours.HEADER + Colours.UNDERLINE + "Note:" +
              Colours.ENDC + " Only Showing: " + Colours.GREEN + "3 " +
              Colours.ENDC + "of the" + Colours.RED + " %s occurrence" %
              (occurrences) + Colours.ENDC)
        print("Showing the " + Colours.GREEN + "1st" + Colours.ENDC +
              ", " + Colours.GREEN + "2nd" + Colours.ENDC + " and" +
              Colours.GREEN + " last" + Colours.ENDC)


def oom_record(oom_lf):
    '''
    Takes 1 argument - the log file to check
    Checks line-by-line for specific string match that indicated OOM has taken
    place
    '''
    list_of_values = {}
    service_value_list = {}
    all_killed_services = []
    oom_incident = {}
    record = False
    record_oom_true_false = False
    counter = 1
    f = openfile(oom_lf)
    for line in f:
        killed = re.search("Killed process (.*) total", line)
        if "[ pid ]   uid  tgid total_vm      rss" in line.strip() \
                and "kernel" in line.lower():
            oom_incident[counter] = {}
            oom_incident[counter]['total_rss'] = []
            oom_incident[counter]['killed_services'] = []
            oom_incident[counter]['oom_date_count'] = []
            list_of_values[counter] = []
            record = True
            record_oom_true_false = False
            oom_incident[counter]['oom_date_count'].append(date_time(line))
            line = strip_line(line)
            column_number = line.split().index("rss") + 1
        elif "Out of memory" in line.strip() and record or \
                len(line.split()) < 14 and record:
            service_value_list[counter] = []
            list_of_values[counter] = list(
                filter(None, list_of_values[counter]))
            # Get a unique list of services
            unique = set([x[1] for x in list_of_values[counter]])
            oom_services = \
                add_rss_for_processes(unique, list_of_values[counter])
            oom_services = \
                sorted(oom_services, key=lambda x: x[2], reverse=True)
            service_value_list[counter] = oom_services
            service_value_list[counter] = service_value_list[counter][:5]
            record_oom_true_false = True
            record = False
            counter += 1
        elif record:
            try:
                line = strip_line(line)
                list_of_values[counter].append(save_values(
                    line, column_number))  # service rss calulation initiation
                rss_value = int(line.split()[int(column_number)-1])
                # calculate total value of all processes:
                oom_incident[counter]['total_rss'].append(rss_value)
            except Exception:
                pass
        elif record_oom_true_false and killed:
            killed = killed.group(1)
            killed = strip_line(killed)
            killed = killed.split(",")[-1].strip("0123456789 ")
            oom_incident[counter-1]['killed_services'].append(killed)
            all_killed_services.append(killed)
    f.close()

    incident_number = 1
    for i in oom_incident:
        if oom_incident[i]['oom_date_count']:
            incident_number += 1

    check_if_incident(
        counter, oom_incident, service_value_list, oom_lf, all_killed_services)
    dmsg_info = DmesgInfo(incident_number)
    dmsg_info.check_dmesg()


def get_log_file(logf=None):
    '''
    Checks OS distribution and accepts arguments
    '''
    #  platform module is depricated in python 3.5+
    _id, _, _ = platform.dist()

    if _id not in SUPPORTED['CENTOS_RHEL'] and _id not in SUPPORTED['UBUNTU_DEBIAN']:
        print("Unsupported OS")
        sys.exit(1)

    # If log file has been specificed by the user
    if logf and os.path.exists(logf):
        oom_log = logf
        return oom_log
    elif logf and not os.path.exists(logf):
        print("")
        print("Does the file specified exist? {0}".format(logf))
        print("Please check again")
        print("")
        sys.exit(1)

    # Obtaining system default log files if no log file specified
    if not logf and _id.lower() in SUPPORTED['CENTOS_RHEL']:
        oom_log = "/var/log/messages"
    elif not logf and _id.lower() in SUPPORTED['UBUNTU_DEBIAN']:
        oom_log = "/var/log/syslog"
    else:
        print("Unsupported OS")
        sys.exit(1)

    return oom_log


def catch_log_exceptions(oom_log):
    '''
    Catch any errors with the analysing of the log file
    '''
    try:
        oom_record(oom_log)
    except Exception as error:
        print("")
        print(Colours.RED + "Error:" + Colours.ENDC)
        print(error)
        print("")
        print(Colours.BOLD + "-" * 40 + Colours.ENDC)


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

    (options, args) = parser.parse_args()
    _oom_logf = get_log_file()

    print_header()

    if options.quick:
        qc_all_logs(locate_all_logs(_oom_logf))
        print("")
        sys.exit(0)
    elif options.file:
        _oom_logf = get_log_file(logf=args[0])

    gld = GetLogData(_oom_logf)
    gld.checkfilesize(skip=options.override)

    try:
        return catch_log_exceptions(_oom_logf)
    except EOFError:
        print()
        return sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except EOFError:
        print("")
        sys.exit(1)
