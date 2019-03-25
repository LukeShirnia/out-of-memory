#!/usr/bin/env python
#
# Author:       Luke Shirnia
# Source:       https://github.com/LukeShirnia/out-of-memory/
# Version 2.0

import __future__
from sys import argv
import sys
import platform
import re
import gzip
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
import datetime
import operator
import os
import fnmatch
import collections
from optparse import OptionParser
import subprocess


class bcolors:
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


total_individual = []
CentOS_RedHat_Distro = \
    ['redhat', 'centos', 'red', 'red hat', 'fedora', 'oracle']
Ubuntu_Debian_Distro = ['ubuntu', 'debian']


def print_header():
    '''
    Disclaimer and Script Header
    '''
    print(bcolors.CYAN + "-" * 40 + bcolors.ENDC)
    print("      _____ _____ _____ ")
    print("     |     |     |     |")
    print("     |  |  |  |  | | | |")
    print("     |_____|_____|_|_|_|")
    print("    Out Of Memory Analyzer")
    print("")
    print("Copyright 2019 LukeShirnia")
    print("")
    print(bcolors.RED + bcolors.UNDERLINE + "Disclaimer:" + bcolors.ENDC)
    print(bcolors.RED +
          "If system OOMs too viciously, there may be nothing logged!")
    print("Do NOT take this script as FACT, investigate further." +
          bcolors.ENDC)
    print(bcolors.CYAN + "-" * 40 + bcolors.ENDC)


def neat_oom_invoke():
    '''
    Print WARNING if there is an OOM issue
    '''
    print(bcolors.RED + bcolors.BOLD + "######## OOM ISSUE ########" +
          bcolors.ENDC)
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
    except IOError:
        print("")
        print("Does the file specified exist? {0}".format(filename))
        print("Please check again")
        print("")
        sys.exit(1)


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


def strip_line(line):
    '''
    Stripping all non required characters from the line so not to
    interfere with line.split()
    '''
    for ch in ["[", "]", "}", "{", "'", "(", ")"]:
        if ch in line:
            line = line.replace(ch, "")
    return line


class GetLogData(object):

    def __init__(self):
        self._info = ''
        self._logfile = ''
        self._size = 0

    def lastlistgzip(self):
        """
        Reads file in chunks to reduce memory footprint
        saves last 2 chunks, combines and finds the last line
        """
        in_file = openfile(self._logfile)
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
            return ((float(file_info.st_size) / 1024) / 1024)

    def checkfilesize(self):
        self._size = self.size_of_file()
        if self._size > 250:
            print("")
            print("!!! File is too LARGE !!!")
            print("Please consider splitting the file into smaller"
                  "chunks (such as dates)")
            return sys.exit(1)
        elif self._size == 0:
            print
            print(bcolors.UNDERLINE + "Log Information" + bcolors.ENDC)
            print(bcolors.GREEN +
                  "Log File  : " + bcolors.YELLOW + " %s " % (
                                            self._logfile) + bcolors.ENDC)
            print(bcolors.RED +
                  "File appears to be empty" +
                  bcolors.ENDC.format(self._logfile))
            print
            return sys.exit(1)
        return True

    def startdate(self):
        lf = openfile(self._logfile)
        for line in lf:
            return line.split()[0:3]

    def enddate(self):
        return self.lastlistgzip().split()[0:3]

    def information(self, logfile):
        self._logfile = logfile
        if self.checkfilesize():
            enddate = self.enddate()
            startdate = self.startdate()
            return (startdate, enddate)
        return


def print_oom_output(
        i, date_format, system_resources, total_rss_per_incident,
        killed_services, service_value_list):
    '''
    Print the Output of an OOM incident (Inc TOP 5 RAM consumers)
    '''
    print(bcolors.BOLD + "-" * 40 + bcolors.ENDC)
    print(bcolors.BOLD + bcolors.PURPLE + "{0} ".format(
        date_format[i - 1]) + bcolors.ENDC)
    print(bcolors.YELLOW + "System RAM:             " + bcolors.ENDC +
          bcolors.CYAN + "{0:<1} MB".format(system_resources()) + bcolors.ENDC)
    print(bcolors.YELLOW + "Estimated RAM at OOM:   " + bcolors.ENDC +
          bcolors.CYAN + "{0:<3} MB".format(int(sum(
            total_rss_per_incident[i] * 4) / 1024)) + bcolors.ENDC)
    print(bcolors.YELLOW + "Services" + bcolors.ENDC + bcolors.RED +
          " Killed:        " + bcolors.ENDC + bcolors.RED + "{0} ".format(
            ", ".join(killed_services[i])) + bcolors.ENDC)
    print("")
    print(bcolors.UNDERLINE +
          "Top 5 RAM Consumers at time of OOM:" + bcolors.ENDC)

    for x in service_value_list[i]:
        _service_name = x[0]
        _process_count = "(%s)" % x[1]
        _service_mb = int(x[2])
        print("Service: {0:<16} {1:>4} {2:>6} MB ".format(
            _service_name[:12], _process_count, _service_mb))

    print("")


def check_if_incident(
    counter, oom_date_count, total_rss_per_incident, killed_services,
        service_value_list, LOG_FILE, all_killed_services):
    '''
    Check if OOM incident occurred. ADD FUNCTION TO PROMPT FOR OTHER LOG FILES
    '''
    date_format = []

    for p in oom_date_count:
        p = datetime.datetime.strftime(p, '%b %d %H:%M:%S')
        date_format.append(p)

    showlogoverview(LOG_FILE, oom_date_count, all_killed_services)
    counter = counter - 1

    if counter == 1:  # if only 1 instance of oom then print all
        date_check(oom_date_count)
        i = 1
        print_oom_output(
            i, date_format, system_resources, total_rss_per_incident,
            killed_services, service_value_list)
    elif counter == 2:  # if only 3 instance of oom then print all
        date_check(oom_date_count)
        for i in (1, 2):
            print_oom_output(
                i, date_format, system_resources, total_rss_per_incident,
                killed_services, service_value_list)
    elif counter >= 3:  # if more 3 or more oom instances, print 1st, 2nd, last
        date_check(oom_date_count)
        for i in (1, 2, counter - 1):
            print_oom_output(
                i, date_format, system_resources, total_rss_per_incident,
                killed_services, service_value_list)
    else:
        print("-" * 40)
        print("OOM has " + bcolors.GREEN + "NOT" + bcolors.ENDC +
              " occured in specified log file!")
        print("-" * 40)
        print("")
        # print similar log files to check for an issue
        quick_check_all_logs(find_all_logs(LOG_FILE, option='exclude'))
        print("")


def find_all_logs(oom_log, option=None):
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
        print(bcolors.YELLOW +
              "Checking other logs, select an option:" + bcolors.ENDC)
        if option == 'exclude':
            while oom_log in result:
                result.remove(oom_log)
    return result


def quick_check_all_logs(results):
    '''
    Quickly check all log files for oom incidents
    (used when --quick option is invoked)
    '''
    option = 1
    next_logs_to_search = []
    del next_logs_to_search[:]
    for a in results:
        total_occurences = []
        del total_occurences[:]
        total_occurences = 0
        inLogFile = openfile(a)
        for line in inLogFile:
            if "[ pid ]   uid  tgid total_vm      rss" in line.strip():
                total_occurences += 1
        if total_occurences >= 1:
            print(bcolors.GREEN + "Option: {0}".format(option) + bcolors.ENDC +
                  "  {0:26} - Occurrences: {1}".format(a, total_occurences))
            next_logs_to_search.append(a)
            option += 1
        else:
            print("           {0:26} - Occurrences: {1}".format(
                a, total_occurences))
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
            Not_Integer = True
            while Not_Integer:
                print("Which file should we check next?")
                tty = open('/dev/tty')
                print("Select an option number between" + bcolors.GREEN +
                      " 1 " + bcolors.ENDC + "and " + bcolors.GREEN +
                      str(len(log_file)) + bcolors.ENDC + ": ")
                option_answer = tty.readline().strip()
                tty.close()
                if option_answer.isdigit():
                    option_answer = int(option_answer)
                    option_answer -= 1
                    if (option_answer) <= (len(log_file) - 1) and \
                            (option_answer) >= 0:
                        new_log_file = log_file[option_answer]
                        OOM_record(new_log_file)
                        incorrect = False
                        Not_Integer = False
                    else:
                        print("Option number out of range, try again")
                        print("")
                else:
                    print("Please select an number")


def _dmesg():
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


def check_dmesg(oom_date_count):
    '''
    Read each line and search for oom string
    '''
    dmesg_count = []
    check_dmesg = _dmesg()
    for dmesg_line in check_dmesg:
        if b"[ pid ]   uid  tgid total_vm      rss" in dmesg_line.lower():
            dmesg_count.append(dmesg_line.strip())
    dmesg_count = list(filter(None, dmesg_count))
    _compare_dmesg(len(dmesg_count), oom_date_count)


def _compare_dmesg(dmesg_count, oom_date_count):
    '''
    Compare dmesg to syslog oom report
    '''
    if dmesg_count > oom_date_count and oom_date_count == 0:
        print("")
        print(bcolors.YELLOW +
              "Dmesg reporting errors but log files are empty...")
        print("Log files appear to have been rotated" + bcolors.ENDC)
        print("")
        print("dmesg incidents: ", dmesg_count)
    elif dmesg_count > oom_date_count:
        print("")
        print(bcolors.YELLOW + "Note: " + bcolors.ENDC + "More reported " +
              bcolors.RED + "errors " + bcolors.ENDC + "in dmesg " +
              bcolors.PURPLE + "({0})".format(dmesg_count) + bcolors.ENDC +
              " than current log file " + bcolors.PURPLE + "({0})".format(
               oom_date_count) + bcolors.ENDC)
        print("Run with " + bcolors.GREEN + "--quick" + bcolors.ENDC +
              " option to check available log files")
        print("")


def showlogoverview(LOG_FILE, oom_date_count, all_killed_services):
    '''
    Get the start and end date of the current log file
    '''
    gld = GetLogData()
    try:
        first_line, last_line = gld.information(LOG_FILE)
    except IndexError:
        print("")
        print("File appears to be corrupt or empty")
        print("Please check:")
        print("             {0}".format(LOG_FILE))
        print("")
        sys.exit(1)
    print("")
    print(bcolors.UNDERLINE + "Log Information" + bcolors.ENDC)
    print(bcolors.GREEN +
          "Log File  : " + bcolors.YELLOW + " %s " % (LOG_FILE) + bcolors.ENDC)
    print(bcolors.GREEN +
          "Start date: " + bcolors.ENDC + bcolors.YELLOW + " %s " % (
            ", ".join(first_line)) + bcolors.ENDC)
    print(bcolors.GREEN +
          "End Date  : " + bcolors.ENDC + bcolors.YELLOW + " %s " % (
            ", ".join(last_line)) + bcolors.ENDC)
    print("")
    if len(oom_date_count) > 4:
        neat_oom_invoke()
        print("Number of OOM occurrence in log file: " +
              bcolors.RED + " %s " % (len(oom_date_count) - 1) + bcolors.ENDC)
    elif len(oom_date_count) <= 4 and len(oom_date_count) > 0:
        neat_oom_invoke()
        "Number of OOM occurrence in log file: %s " % (len(oom_date_count))
    else:
        "Number of OOM occurrence in log file: %s " % (len(oom_date_count))
        print("")
    all_killed_services = dict(
        (i, all_killed_services.count(i)) for i in all_killed_services)
    ServiceCount = sorted(
        ((v, k) for k, v in all_killed_services.items()), reverse=True)
    for i in ServiceCount:
        print("Service " + bcolors.RED + "{0:12} ".format(i[1]) +
              bcolors.ENDC + "Killed " + bcolors.RED + "{0} ".format(i[0]) +
              bcolors.ENDC + "time(s)")
    print("")


def save_values(line, column_number):
    '''
    This function processes each line (when record = True)
    and saves the rss value and process name .eg (51200, apache)
    '''
    value = line.split()[-1:]
    if len(value) == 1:
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
    date_of_oom = line.split()[0:3]
    date_of_oom = " ".join(date_of_oom)
    date_check = datetime.datetime.strptime(
        date_of_oom, "%b %d %H:%M:%S")
    return date_check


def strip_time(date_time):
    '''
    Used to summarise the hour OOM's occurred (excludes the mins and seconds)
    '''
    return date_time + datetime.timedelta(
        hours=1, minutes=-date_time.minute, seconds=-date_time.second)


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


def date_check(oom_date_count):
    '''
    The function is used to produce a list of dates +inc hour of every oom
    occurrence in the log file
    '''
    dates_test = []
    dates_sorted = []
    oom_date_count.sort()
    for p in oom_date_count:
        time = strip_time(p)
        time = datetime.datetime.strftime(p, '%m-%d %H')
        dates_test.append(time)
    dates_test = dict((i, dates_test.count(i)) for i in dates_test)
    dates_sorted = sorted(dates_test.items())
    dates_test = date_time_counter_split(dates_sorted)
    print(bcolors.YELLOW + bcolors.UNDERLINE + "KEY" + bcolors.ENDC +
          bcolors.YELLOW)
    print("D = Date(s) OOM")
    print("H = Hour OOM Occurred")
    print("O = Number of Occurrences in Date/Hour" + bcolors.ENDC)
    print("")
    print(bcolors.UNDERLINE + "D" + bcolors.ENDC + "      " +
          bcolors.UNDERLINE + "H" + bcolors.ENDC + "  " + bcolors.UNDERLINE +
          bcolors.UNDERLINE + "O" + bcolors.ENDC)
    for value in dates_test:
        print(value)
    print("")
    if len(oom_date_count) >= 3:
        print(bcolors.HEADER + bcolors.UNDERLINE + "Note:" +
              bcolors.ENDC + " Only Showing: " + bcolors.GREEN + "3 " +
              bcolors.ENDC + "of the" + bcolors.RED + " %s occurrence" %
              (len(oom_date_count)) + bcolors.ENDC)
        print("Showing the " + bcolors.GREEN + "1st" + bcolors.ENDC +
              ", " + bcolors.GREEN + "2nd" + bcolors.ENDC + " and" +
              bcolors.GREEN + " last" + bcolors.ENDC)


def OOM_record(LOG_FILE):
    '''
    Takes 1 argument - the log file to check
    Checks line-by-line for specific string match that indicated OOM has taken
    place
    '''
    oom_date_count = []
    list_of_values = {}
    total_rss = {}
    killed_services = {}
    unique_services = {}
    service_value_list = {}
    all_killed_services = []
    record = False
    record_oom_true_false = False
    counter = 1
    inLogFile = openfile(LOG_FILE)
    for line in inLogFile:
        killed = re.search("Killed process (.*) total", line)
        if "[ pid ]   uid  tgid total_vm      rss" in line.strip() \
                and "kernel" in line.lower():
            total_rss[counter] = []
            killed_services[counter] = []
            unique_services[counter] = []
            list_of_values[counter] = []
            record = True
            record_oom_true_false = False
            oom_date_count.append(date_time(line))
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
                total_rss[counter].append(rss_value)
            except Exception:
                pass
        elif record_oom_true_false and killed:
            killed = killed.group(1)
            killed = strip_line(killed)
            killed = killed.split(",")[-1].strip("0123456789 ")
            killed_services[counter-1].append(killed)
            all_killed_services.append(killed)
    inLogFile.close()
    check_if_incident(
        counter, oom_date_count, total_rss, killed_services,
        service_value_list, LOG_FILE, all_killed_services)
    check_dmesg(len(oom_date_count))


def get_log_file(logf=None):
    '''
    Checks OS distribution and accepts arguments
    '''
    os_check_value = \
        platform.dist()[0] if platform.linux_distribution() else None
    # If log file has been specificed by the user
    if logf:
        oom_log = logf
    # Obtaining system default log files if no log file specified
    elif not logf and os_check_value.lower() in CentOS_RedHat_Distro:
        oom_log = "/var/log/messages"
    elif not logf and os_check_value.lower() in Ubuntu_Debian_Distro:
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
        OOM_record(oom_log)
    except Exception as error:
        print("")
        print(bcolors.RED + "Error:" + bcolors.ENDC)
        print(error)
        print("")
        print(bcolors.BOLD + "-" * 40 + bcolors.ENDC)


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

    (options, args) = parser.parse_args()
    print_header()
    if options.quick:
        quick_check_all_logs(find_all_logs(get_log_file()))
        print("")
        return sys.exit(0)
    elif options.file:
        try:
            return catch_log_exceptions(get_log_file(logf=args[0]))
        except(EOFError, KeyboardInterrupt):
            print("")
            return sys.exit(1)
    try:
        return catch_log_exceptions(get_log_file())
    except(EOFError, KeyboardInterrupt):
        print
        return sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except(EOFError, KeyboardInterrupt):
        print("")
        sys.exit(1)
