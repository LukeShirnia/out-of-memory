#!/usr/bin/env python
#
# Author:       Luke Shirnia
# Source:       https://github.com/LukeShirnia/out-of-memory/
####
# To Do:
# - Handle random log file issues (see old script)
# - Fix start and end time on linutmint
# - Check script gets multiple killed service for a single oom incident
# - add JournalCTL and DMESG
# - Add total of services killed
# - reduce memory footprint if possible
# - Add --quick options
####
from __future__ import print_function

import datetime
import errno
import fnmatch
import gzip
import os
import re
import sys
import warnings
from optparse import OptionParser

warnings.filterwarnings(
    "ignore", category=DeprecationWarning
)  # Hide platform.dist() related deprecation warnings


__version__ = "2.0.0"


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


# Helper functions # {{{
def open_file(file_path):
    """Handle reading of gzipped and regular files"""
    if file_path.endswith(".gz"):
        return gzip.open(file_path, "rt")
    else:
        return open(file_path, "r")


class Printer(object):
    """
    Base class for all facts

    A `fact` is a basic unit of information collection in this script. This is a base class
    providing the common functions such as output formatting.
    """

    horizontal_line = "_" * 40

    WHITE = "\033[1m"
    GREEN = "\033[1;32m"
    CYAN = "\033[0;96m"
    ORANGE = "\033[1;33m"
    RED = "\033[1;31m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"

    # Fact's severity
    NONE = 0  # no useful output
    INFO = 1
    NOTICE = 2
    WARN = 3
    CRIT = 4
    _severity = NONE
    _lines = []

    HEADER = None

    @property
    def spacer(self):
        return self.WHITE + self.horizontal_line + self.RESET

    def _header(self, msg):
        self._severity = max(self._severity, self.INFO)
        return self.WHITE + msg + self.RESET

    def _ok(self, msg):
        self._severity = max(self._severity, self.INFO)
        return self.GREEN + msg + self.RESET

    def _notice(self, msg):
        self._severity = max(self._severity, self.NOTICE)
        return self.CYAN + msg + self.RESET

    def _warning(self, msg):
        self._severity = max(self._severity, self.WARN)
        return self.ORANGE + msg + self.RESET

    def _critical(self, msg):
        self._severity = max(self._severity, self.CRIT)
        return self.RED + msg + self.RESET

    def multiline(self, minseverity=INFO, limit=None):
        if self._severity < minseverity or len(self._lines) == 0:
            return []
        lines = self._lines
        if limit and len(lines) > limit:
            # pylint: disable=invalid-unary-operand-type
            lines = ["...(%dx more)..." % (len(lines) - limit)] + lines[-limit:]
        if self.HEADER:
            lines = [self.WHITE + self.HEADER + ":" + self.RESET] + lines
        return lines


# }}}


def main_header():
    """
    Disclaimer and Script Header
    """
    colours = Printer()
    analyzer_name = "Out Of Memory Analyzer"
    current_year = datetime.datetime.now().year
    author_name = "LukeShirnia"
    disclaimer_text = "If the system OOMs too viciously, there may be nothing logged!"
    warning_text = "Do NOT take this script as FACT, ALWAYS investigate further."

    print(colours.spacer)
    print("      _____ _____ _____ ")
    print("     |     |     |     |")
    print("     |  |  |  |  | | | |")
    print("     |_____|_____|_|_|_|")
    print("     {}".format(analyzer_name))
    print("")
    print("\u00A9 {} {}".format(current_year, author_name))
    print("")
    print(
        "{colours.RED}{colours.UNDERLINE}Disclaimer:{colours.RESET}".format(
            colours=colours
        )
    )
    print(
        "{colours.RED}{disclaimer_text}".format(
            colours=colours, disclaimer_text=disclaimer_text
        )
    )
    print(
        "{warning_text}{colours.RESET}".format(
            warning_text=warning_text, colours=colours
        )
    )
    print(colours.spacer)


class System(Printer):
    """System information"""

    def __init__(self):
        self.python_version = None
        self.distro, self.version, _ = self.get_distro_info()
        self.log_files = []
        self.log_to_use = None
        self.ram = self.get_ram_info()
        self.find_system_logs()

    def __str__(self):
        return self._system

    def parse_os_release(self):
        distro = version = None
        release_id_map = {
            "ol": "oracle",
            "rhel": "redhat",
            "centos": "centos",
            "almalinux": "almalinux",
            "rocky": "rocky",
        }

        if os.path.isfile("/etc/os-release"):
            with open_file("/etc/os-release") as f:
                for line in f:
                    if line.startswith("VERSION_ID="):
                        version = line.split("=")[1].strip('" \n')
                    if line.startswith("ID="):
                        distro = line.split("=")[1].strip('" \n')
                        distro = release_id_map.get(distro, distro)

        return distro, version, None

    def get_distro_info(self):
        python_version = sys.version_info
        self.python_version = "{}.{}.{}".format(
            python_version.major, python_version.minor, python_version.micro
        )
        # pylint: disable=deprecated-method
        # pylint: disable=import-outside-toplevel
        try:
            # First we attempt to use platform.dist() for compatibility reasons.
            # This function however has been deprecated in py > 3.7, so we catch the AttributeError
            # and then attempt to use the distro module instead
            # Standard Library
            import platform as platform_info

            platform_info_tuple = platform_info.dist()
            # If the tuple is empty, it's probably AWS, so let's expand the supported distro list
            # If the tuple's last element is "Green Obsidian", it's Rocky Linux so let's expand
            # the supported distros
            if (
                not any(platform_info_tuple)
                or platform_info_tuple[-1] == "Green Obsidian"
            ):
                dists = platform_info._supported_dists + (
                    "system",
                )  # pylint: disable=protected-access  # Added to include Amazon and Rocky Linux Support
                return platform_info.linux_distribution(supported_dists=dists)
            return platform_info_tuple
        except AttributeError:
            try:
                # Third Party
                import distro as platform_info  # pylint: disable=import-error

                return platform_info.linux_distribution(full_distribution_name=False)
            # If the distro module does not exist, gracefully handle htLook exit
            except ModuleNotFoundError:  # pylint: disable=undefined-variable
                return self.parse_os_release()

    def parse_file(self, file_path, patterns):
        if os.path.isfile(file_path):
            with open_file(file_path) as f:
                for line in f:
                    for pattern, extractor in patterns:
                        if pattern in line:
                            path = extractor(line)
                            if not os.path.isfile(path):
                                path = file_path
                            self.log_files.append(path)

    def find_system_logs(self):
        # Check for rsyslog.conf on Linux systems
        self.parse_file(
            "/etc/rsyslog.conf", [("*.info", lambda line: line.split()[-1])]
        )

        # Check for journald.conf on newer Linux systems
        self.parse_file(
            "/etc/systemd/journald.conf",
            [("Storage=", lambda line: line.split("=")[-1].strip())],
        )

        # Check for syslog.conf on older Linux systems and older macOS systems
        self.parse_file(
            "/etc/syslog.conf",
            [
                ("*.info", lambda line: line.split()[-1]),
                ("/var/log/system.log", lambda line: line.split()[-1]),
            ],
        )

        # Check for asl.conf on newer macOS systems
        self.parse_file(
            "/etc/asl.conf",
            [
                (
                    "? [= Sender kernel] file (.+)",
                    lambda line: "/var/log/" + line.split()[-1],
                )
            ],
        )

        # Adding log info to the lines list
        if self.log_files:
            self.log_to_use = self.log_files[0]

    def search_log_dir(self, log_file):
        """
        This function finds all log files in the directory of
        default log file (or specified log file)
        """
        log_directory = os.path.dirname(log_file)
        log_file_pattern = os.path.basename(log_file) + "*"

        log_files = [
            os.path.join(root, name)
            for root, _, files in os.walk(log_directory)
            for name in files
            if fnmatch.fnmatch(name, log_file_pattern)
        ]
        return sorted(log_files)

    def get_ram_info(self):
        try:
            mem_bytes = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
            mem_gib = mem_bytes / (1024.0 ** 3)
            return round(mem_gib, 2)
        except ValueError:
            return None

    def populate_lines(self):
        # Only populate lines if they haven't been populated already
        if self._lines:
            return

        distro_version = "{} {}".format(self.distro, self.version)
        self._lines.append(self._header("OS: ") + self._notice(distro_version))
        self._lines.append(
            self._header("Python Version: ") + self._notice(self.python_version)
        )
        self._lines.append(
            self._header("RAM: ") + self._notice("{} GiB".format(self.ram))
        )
        self._lines += [
            self._header("Default System Log: ") + self._notice(self.log_files[0])
        ]
        self._lines.append("")
        self._lines.append(self._header("Using Log: ") + self._ok(self.log_to_use))

    def print_pretty(self):
        self.populate_lines()

        print()
        for line in self._lines:
            print(line)


class OOMAnalyzer(Printer):
    """Class to analyze OOM logs"""

    def __init__(self, system):
        self.system = system
        self.log_file = self.system.log_to_use
        self.oom_instances = []
        self.current_instance = None
        self.rss_column = 7
        self.log_start_time = None
        self.log_end_time = None
        self.oom_counter = 0

    def parse_log(self):
        last_line = None
        found_killed = False
        with open_file(self.log_file) as f:
            for line in f:
                last_line = line  # Used to extract the end time of the log
                # Extract the start timestamp from the line
                if self.log_start_time is None:
                    self.log_start_time = self.extract_timestamp(line)

                # Start of a new OOM incident
                if self.is_oom_start(line):
                    line = self.strip_brackets_pid(line)
                    self.oom_counter += 1
                    timestamp = self.extract_timestamp(line)
                    self.rss_column = line.split().index("rss") + 1
                    # If we've already started an OOM incident, add it to the list adn start a new
                    if self.current_instance:
                        self.oom_instances.append(self.current_instance)
                        found_killed = False
                    self.current_instance = {
                        "total_mb": 0,
                        "processes": [],
                        "killed": [],
                        "start_time": timestamp,
                        "incident_number": self.oom_counter,
                    }
                # Processing the new OOM incident
                elif (
                    # Once we've found a killed process, we don't care about this until the next
                    # OOM incident
                    not found_killed
                    and not self.is_killed_process(line)
                    and self.is_process_line(line)
                    and self.current_instance is not None
                ):
                    # Sometimes the log line isn't complete which might be an issue with the kernel
                    # logging during the incident. If we can't parse the line, lets skip it
                    try:
                        processed_line = self.parse_process_line(line)
                        self.current_instance["processes"].append(processed_line)
                        # Get a running total for each OOM incident
                        self.current_instance["total_mb"] += processed_line["rss"]
                    except ValueError:
                        # Debug: Add a "print(line)"" here if you wish know which lines are skipped
                        continue
                # Find killed services for this OOM incident
                elif self.is_killed_process(line) and self.current_instance is not None:
                    found_killed = True
                    self.current_instance["killed"].append(
                        self.parse_killed_process_line(line)
                    )

        # Extract the end timestamp from the last line
        if self.log_end_time is None:
            self.log_end_time = self.extract_timestamp(last_line)

        # Add the last OOM incident to the list
        if self.current_instance:
            self.oom_instances.append(self.current_instance)

        return self.oom_instances

    def strip_brackets_pid(self, log_line):
        return log_line.replace("[", "").replace("]", "")

    def is_oom_start(self, line):
        """Check if the line is the start of a new OOM incident"""
        return "[ pid ]" in line

    def is_process_line(self, line):
        return re.match(r".*\[\s*\d+\]\s*\d+\s+\d+\s+\d+\s+.*", line)

    def parse_process_line(self, line):
        """Parse the line and obtain the pid, rss and name of the process"""
        fields = line.split()
        rss = int(fields[self.rss_column])
        rss_mb = rss * 4 // 1024
        name = fields[-1]
        return {"rss": rss_mb, "name": name}

    def is_killed_process(self, line):
        """Check if the line is a killed process line"""
        return "killed process" in line.lower()

    def parse_killed_process_line(self, line):
        """Extract the name of the killed process"""
        match = re.search(
            r"Killed process \d+(?:, UID \d+)?, \((\S+)\)|Killed process \d+ \((\S+)\)",
            line,
            re.IGNORECASE,
        )
        if match:
            return match.group(1) or match.group(2)
        return None

    def extract_timestamp(self, line):
        """Method to extract the timestamp from the line"""
        # dmesg-style date: [Mon Feb  1 09:08:13 2021]
        if line[0] == "[":
            raw_timestamp = line[1:].split("]")[0]
            timestamp_object = datetime.datetime.strptime(raw_timestamp, "%c")
        # syslog-style date format.
        else:
            raw_timestamp_list = line.split()[0:3]
            raw_timestamp = " ".join(raw_timestamp_list)
            timestamp_object = datetime.datetime.strptime(
                raw_timestamp, "%b %d %H:%M:%S"
            )
        return timestamp_object

    def sorted_results(self, oom_processes_list):
        """Method to sort the OOM processes by RSS"""
        result = {}
        count = {}
        for item in oom_processes_list:
            process = item["name"]
            rss = item["rss"]
            if process in result:
                result[process] += rss
                count[process] += 1
            else:
                result[process] = rss
                count[process] = 1
        return sorted(result.items(), key=lambda x: x[1], reverse=True), count

    def quick_check(self, all=False):
        """Check how many oom incidents a log (or all logs) have...quickly"""
        log_list = self.system.search_log_dir(self.log_file) if all else [self.log_file]

        all_logs = {}
        for log in log_list:
            count = 0
            with open_file(log) as f:
                for line in f:
                    if self.is_oom_start(line):
                        count += 1
            all_logs[log] = count
        return all_logs

    def print_pretty_oom_instance(self, oom_instance):
        """Method to print the OOM incident in a pretty format"""
        # Print general overview
        print(
            self._warning("OOM Incident: ")
            + self._notice(str(oom_instance["incident_number"]))
        )
        print(
            self._header("Start Time: ")
            + self._notice(oom_instance["start_time"].strftime("%a %b %d %X"))
        )
        print(self._header("The following processes were killed:"))
        for killed in oom_instance["killed"]:
            print("  " + self._critical(killed))

        sorted_result, count = self.sorted_results(oom_instance["processes"])

        # Calculate column widths dynamically
        process_width = max(len(process) for process, _ in sorted_result) + 2
        count_width = max(len(str(count[process])) for process, _ in sorted_result) + 2
        rss_width = max(len(str(rss)) for _, rss in sorted_result) + 7

        # Print header row
        print(self._header("Processes (showing top 10 processes):"))
        header_row = (
            "{process:<{process_width}}{count:<{count_width}}{rss:<{rss_width}}".format(
                process="PROCESS",
                process_width=process_width - 3,
                count="COUNT",
                count_width=count_width + 3,
                rss="RSS (MB)",
                rss_width=rss_width,
            )
        )
        print(self._header("  " + header_row.rstrip()))

        # Print data rows
        for process, rss in sorted_result[:10]:
            data_row = "{process:<{process_width}}{count:<{count_width}}{rss:<{rss_width}}".format(
                process=process,
                process_width=process_width,
                count=count[process],
                count_width=count_width,
                rss="{} MB".format(rss),
                rss_width=rss_width,
            )
            print("  " + self._notice(data_row.rstrip()))

        print()

    def print_pretty_log_info(self):
        """Method to print the OOM incident in a pretty format"""
        print(
            self._header("Log Start Time: ")
            + self._notice(self.log_start_time.strftime("%a %b %d %X"))
        )
        print(
            self._header("Log End Time: ")
            + self._notice(self.log_end_time.strftime("%a %b %d %X"))
        )
        print()


def run(system, options):
    show_counter, reverse, quick = options.show_counter, options.reverse, options.quick

    # Parse the log file and extract OOM incidents
    analyzer = OOMAnalyzer(system)
    oom_instances = analyzer.parse_log()

    # Print system and log overview
    system.print_pretty()
    analyzer.print_pretty_log_info()

    # Quick check
    if quick:
        all_results = analyzer.quick_check(all=True)
        print(system.spacer)
        print()
        print(system._warning("Performing a quick check..."))
        for log, count in all_results.items():
            print(
                system._header("File {}: {} OOM incidents").format(
                    log, system._critical(str(count))
                )
            )
        print()
        print(system.spacer)
        print()

        return sys.exit(0)

    # Exit early if no OOM incidents were found
    if len(oom_instances) == 0:
        print(
            system._ok(
                "No OOM incidents found! The file {} has no OOM incidents.".format(
                    system.log_to_use
                )
            )
        )
        print()
        return sys.exit(0)

    # Handle the reverse flag and slice the OOM incidents based on the show_counter
    normal_or_reversed = -1 if reverse else 1
    show_instances = oom_instances[::normal_or_reversed][:show_counter]
    largest_incident = max(oom_instances, key=lambda d: d["total_mb"])

    # OOM Overview
    print(system.spacer)
    print()
    print()
    print(
        system._critical(
            "WARNING: This device has run out of memory at least once in this log file."
        )
    )
    print()
    oom_occurrences = len(oom_instances)
    print(system.spacer)
    print()
    print(system._header("      Incident Overview"))
    print(system.spacer)
    print()
    print(system._header("OOM Incidents: ") + system._critical(str(oom_occurrences)))
    print(
        "Highest OOM Incident: "
        + system._warning("Incident Number " + str(largest_incident["incident_number"]))
    )
    print(
        "Memory Used In Incident: "
        + system._warning(str(largest_incident["total_mb"]) + " MB")
    )
    print(system.spacer)

    # Lets ALWAYS display the largest OOM incident. If it is not in the show_instances list,
    # display it.
    if largest_incident["incident_number"] not in list(
        [i["incident_number"] for i in show_instances]
    ):
        print()
        print(system.spacer)
        print()
        print(system._critical("      Largest Incident"))
        print(system.spacer)
        print()
        print(system._header("The largest OOM incident in this log file was:"))
        print()
        analyzer.print_pretty_oom_instance(largest_incident)
        print(system.spacer)

    # print()
    # print(system.spacer)
    print()

    print(system._header("         OOM Incidents"))
    print(system.spacer)
    print()
    print("Displaying {} OOM incidents:".format(show_counter))

    # Display OOM incidents based on the show_counter and reverse (if provided)
    print()
    for instance in show_instances:
        analyzer.print_pretty_oom_instance(instance)

    print(system.spacer)
    print()

    # Only display this message if there are more oom incidents than the show_counter
    if oom_occurrences > show_counter:
        print()
        print(
            system._warning(
                "(To increase the number of OOM incidents displayed, use the -s flag)"
            )
        )
        print()

    print()

    return sys.exit(0)


def validate_options(options, system):
    """Function to validate the options provided by the user"""
    # Instantiate the System class and validate the default log file
    try:
        system.log_to_use = system.log_files[0]
    except IndexError:
        # Only return an error if the user has not specified a log file
        if not options.file:
            print(
                "Error: Unable to find log file for this Operating System. "
                "Please specify a log file with the -f option"
            )
            return sys.exit(1)

    # Check if the user has specified a valid log file and it is not too large
    if options.file:
        if not os.path.isfile(options.file):
            print("File {} does not exist".format(options.file))
            return sys.exit(1)
        else:
            system.log_to_use = options.file
            if os.path.getsize(options.file) > 314572800 and not options.override:
                print(
                    "File is larger than 300MB, please specify the -o option to override"
                )
                return sys.exit(1)

    return


def main():
    parser = OptionParser(usage="usage: %prog [option]")
    parser.add_option(
        "-f",
        "--file",
        dest="file",
        type="string",
        metavar="File",
        help="Specify a log to check",
    )
    parser.add_option(
        "-s",
        "--show",
        dest="show_counter",
        type=int,
        metavar="Show",
        default=5,
        help="Override the default number of OOM incidents to show",
    )
    parser.add_option(
        "-r",
        "--reverse",
        dest="reverse",
        default=False,
        action="store_true",
        help="Show the most recent OOM incidents first. "
        "By default we show the fist OOM incidents found in the file, "
        "which are located at the beginning of the file.",
    )
    parser.add_option(
        "-q",
        "--quick",
        dest="quick",
        default=False,
        action="store_true",
        help="Display the scripts version number",
    )
    parser.add_option(
        "-V",
        "--version",
        dest="version",
        action="store_true",
        help="Display the scripts version number",
    )

    (options, _) = parser.parse_args()

    # Show the version number and exit
    if options.version:
        print("OOM Analyzer Version: {}".format(__version__))
        return sys.exit(0)

    system = System()

    # Validate the options provided by the user and the log file
    validate_options(options, system)

    # Print the script header
    main_header()

    return run(system, options)


if __name__ == "__main__":
    main()
