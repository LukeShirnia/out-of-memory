#!/usr/bin/env python
#
# Author:       Luke Shirnia
# Source:       https://github.com/LukeShirnia/out-of-memory/
####
# To Do:
# - Handle random log file issues (see old script)
# - Fix start and end time on linutmint
# - Check script gets multiple killed service for a single oom instance
# - add JournalCTL and DMESG
# - Add total of services killed
####
from __future__ import print_function

import datetime
import errno
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
    horizontal_line = "-" * 40
    analyzer_name = "Out Of Memory Analyzer"
    current_year = datetime.datetime.now().year
    author_name = "LukeShirnia"
    disclaimer_text = "If the system OOMs too viciously, there may be nothing logged!"
    warning_text = "Do NOT take this script as FACT, ALWAYS investigate further."

    print(
        "{colours.CYAN}{horizontal_line}{colours.RESET}".format(
            colours=colours, horizontal_line=horizontal_line
        )
    )
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
    print(
        "{colours.CYAN}{horizontal_line}{colours.RESET}".format(
            colours=colours, horizontal_line=horizontal_line
        )
    )


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

    def __init__(self, log_file):
        self.log_file = log_file
        self.oom_instances = []
        self.current_instance = None
        self.rss_column = 7
        self.pid_column = 3
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

                # Start of a new OOM instance
                if self.is_oom_start(line):
                    self.oom_counter += 1
                    timestamp = self.extract_timestamp(line)
                    self.pid_column = line.split().index("pid")
                    self.rss_column = line.split().index("rss")
                    # If we've already started an OOM instance, add it to the list adn start a new
                    if self.current_instance:
                        self.oom_instances.append(self.current_instance)
                        found_killed = False
                    self.current_instance = {
                        "processes": [],
                        "killed": [],
                        "start_time": timestamp,
                        "instance_number": self.oom_counter,
                    }
                # Processing the new OOM instance
                elif (
                    # Once we've found a killed process, we don't care about this until the next
                    # OOM instance
                    not found_killed
                    and not self.is_killed_process(line)
                    and self.is_process_line(line)
                    and self.current_instance is not None
                ):
                    # Sometimes the log line isn't complete, maybe an issue with the kernel logging
                    # during the incident. If we can't parse the line, lets skip it
                    try:
                        self.current_instance["processes"].append(
                            self.parse_process_line(line)
                        )
                    except ValueError:
                        # Debug: Add a "print(line)"" here if you wish know which lines are skipped
                        continue
                # Find killed services for this OOM instance
                elif self.is_killed_process(line) and self.current_instance is not None:
                    found_killed = True
                    self.current_instance["killed"].append(
                        self.parse_killed_process_line(line)
                    )

        # Extract the end timestamp from the last line
        if self.log_end_time is None:
            self.log_end_time = self.extract_timestamp(last_line)

        # Add the last OOM instance to the list
        if self.current_instance:
            self.oom_instances.append(self.current_instance)

        return self.oom_instances

    def is_oom_start(self, line):
        """Check if the line is the start of a new OOM instance"""
        return "[ pid ]" in line

    def is_process_line(self, line):
        return re.match(r".*\[\s*\d+\]\s*\d+\s+\d+\s+\d+\s+.*", line)

    def parse_process_line(self, line):
        """Parse the line and obtain the pid, rss and name of the process"""
        fields = line.split()
        pid = int(fields[self.pid_column].strip("[]"))
        rss = int(fields[self.rss_column])
        rss_mb = rss * 4 // 1024
        name = fields[-1]
        return {"pid": pid, "rss": rss_mb, "name": name}

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

    def print_pretty(self):
        """Method to print the OOM instances in a pretty format"""
        print(
            self._header("Log Start Time: ")
            + self._notice(self.log_start_time.strftime("%a %b %d %X"))
        )
        print(
            self._header("Log End Time: ")
            + self._notice(self.log_end_time.strftime("%a %b %d %X"))
        )
        print()


def run(system, show_counter, reverse):
    analyzer = OOMAnalyzer(system.log_to_use)
    oom_instances = analyzer.parse_log()

    system.print_pretty()
    analyzer.print_pretty()

    # Exit early if no OOM instances were found
    if len(oom_instances) == 0:
        print(
            system._ok(
                "No OOM instances found! The file {} has no OOM instances.".format(
                    system.log_to_use
                )
            )
        )
        print()
        return sys.exit(0)

    # Display OOM Overview
    print(
        "{colours.CYAN}{horizontal_line}{colours.RESET}".format(
            colours=system, horizontal_line="-" * 40
        )
    )
    print()
    print(system._critical("######## OOM WARNING ########"))
    print()
    print(
        system._header("This device has run out of memory ")
        + system._critical(str(len(oom_instances)))
        + system._header(" times.")
    )

    print()
    print(
        system._notice(
            "To increase the number of OOM instances displayed, use the -s flag."
        )
    )
    print()
    print(system._header("Displaying {} OOM instances:".format(show_counter)))
    print()

    # Handle the reverse flag and slice the OOM instances based on the show_counter
    normal_or_reversed = -1 if reverse else 1
    show_instances = oom_instances[::normal_or_reversed][:show_counter]

    # Display OOM instances based on the show_counter and reverse (if provided)
    for instance in show_instances:
        print("OOM Instance {}:".format(instance["instance_number"]))
        print("  Processes:")
        for process in instance["processes"]:
            print(
                "    PID: {}, RSS: {} MB, Name: {}".format(
                    process["pid"], process["rss"], process["name"]
                )
            )
        processes_killed = instance.get("killed") if instance.get("killed") else []
        print("  Killed Processes: {}".format(",".join(processes_killed)))
        print()
        print()

    return sys.exit(0)


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
        help="Override the default number of OOM instances to show",
    )
    parser.add_option(
        "-r",
        "--reverse",
        dest="reverse",
        default=False,
        action="store_true",
        help="Show the most recent OOM instances first. "
        "By default we show the fist OOM instances found in the file, "
        "which are located at the beginning of the file.",
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
        print("OOM Analyzer Version: %s" % __version__)
        return sys.exit(0)

    # Print the script header
    main_header()

    # Instantiate the System class and validate the default log file
    system = System()
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

    return run(system, options.show_counter, options.reverse)


if __name__ == "__main__":
    main()
