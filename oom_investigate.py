#!/usr/bin/env python
#
# Author:       Luke Shirnia
# Source:       https://github.com/LukeShirnia/out-of-memory/
from __future__ import print_function

import datetime
import errno
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
def readfile(filename):
    """
    Return the whole contents of the given file
    """
    file_descriptor = open(filename)
    ret = file_descriptor.read().strip()
    file_descriptor.close()
    return ret


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
        self.find_logs()

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
            with open("/etc/os-release") as f:
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
            with open(file_path, "r") as f:
                for line in f:
                    for pattern, extractor in patterns:
                        if pattern in line:
                            path = extractor(line)
                            if not os.path.isfile(path):
                                path = file_path
                            self.log_files.append(path)

    def find_logs(self):
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


class OOMAnalyzer:
    def __init__(self, log_file):
        self.log_file = log_file
        self.oom_instances = []
        self.current_instance = []
        self.rss_column = 7
        self.pid_column = 3
        self.log_start_time = None
        self.log_end_time = None

    def parse_log(self):
        last_line = None
        with open(self.log_file, "r") as f:
            for line in f:
                last_line = line  # Used to extract the end time of the log
                if self.log_start_time is None:
                    self.log_start_time = " ".join(line.split()[0:3])
                # Start of a new OOM instance
                if self.is_oom_start(line):
                    self.pid_column = line.split().index("pid")
                    self.rss_column = line.split().index("rss")
                    if self.current_instance:
                        self.oom_instances.append(self.current_instance)
                    self.current_instance = {"processes": [], "killed": []}
                # Processing the new OOM instance
                elif (
                    not self.is_killed_process(line)
                    and self.is_process_line(line)
                    and self.current_instance is not None
                ):
                    self.current_instance["processes"].append(
                        self.parse_process_line(line)
                    )
                # Find killed services for this OOM instance
                elif self.is_killed_process(line) and self.current_instance is not None:
                    print("killed")
                    self.current_instance["killed"].append(
                        self.parse_killed_process_line(line)
                    )
                elif self.current_instance:
                    self.oom_instances.append(self.current_instance)
                    self.current_instance = None

        if self.log_end_time is None:
            self.log_end_time = " ".join(last_line.split()[0:3])

        if self.current_instance:
            self.oom_instances.append(self.current_instance)

        return self.oom_instances

    def is_oom_start(self, line):
        """Check if the line is the start of a new OOM instance"""
        return "[ pid ]" in line

    def is_process_line(self, line):
        return re.match(r".*\[\s*\d+\].*", line)

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
        match = re.match(r"Killed process \d+, UID \d+, \((\S+)\)", line)
        # print(f"foo {match.group(1)}")
        return match.group(1)

    def extract_timestamp(self, line):
        timestamp = line.split()[0]
        return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")


def run(system, log_file):
    analyzer = OOMAnalyzer(log_file)
    oom_instances = analyzer.parse_log()
    print(system._header("Log Start Time: ") + system._notice(analyzer.log_start_time))
    print(system._header("Log End Time: ") + system._notice(analyzer.log_end_time))
    print()

    # Exit early is no OOM instances were found
    if len(oom_instances) == 0:
        print(
            system._ok(
                "No OOM instances found! The file {} has no OOM instances.".format(
                    log_file
                )
            )
        )
        print()
        return sys.exit(0)

    # Display OOM instances
    print(
        "{colours.CYAN}{horizontal_line}{colours.RESET}".format(
            colours=system, horizontal_line="-" * 40
        )
    )
    print()
    print(system._critical("######## OOM WARNING ########"))
    print()
    print(system._critical("OOM Instances: {}".format(len(oom_instances))))

    print()

    # for i, instance in enumerate(oom_instances, start=1):
    #     print(f"OOM Instance {i}:")
    #     print("  Processes:")
    #     for process in instance["processes"]:
    #         print(
    #             f"    PID: {process['pid']}, RSS: {process['rss']} MB, Name: {process['name']}"
    #         )
    #     print("  Killed Processes:")
    #     for killed_process in instance["killed"]:
    #         print(
    #             f"    PID: {killed_process['pid']}, RSS: {killed_process['rss']} MB, Name: {killed_process['name']}"
    #         )
    #     print()


def main():
    parser = OptionParser(usage="usage: %prog [option]")
    parser.add_option(
        "-f",
        "--file",
        dest="file",
        action="store_true",
        metavar="File",
        help="Specify a log to check",
    )
    parser.add_option(
        "-V",
        "--version",
        dest="version",
        action="store_true",
        help="Display the scripts version number",
    )

    (options, args) = parser.parse_args()

    if options.version:
        print("OOM Analyzer Version: %s" % __version__)
        return sys.exit(0)

    # Obtain and print system information
    main_header()
    system = System()
    try:
        log = system.log_files[0]
    except IndexError:
        # Only return an error if the user has not specified a log file
        if not options.file:
            print(
                "Error: Unable to find log file for this Operating System. "
                "Please specify a log file with the -f option"
            )
            return sys.exit(1)

    if options.file:
        if len(args) == 0:
            print("Please specify a log file to check")
            return sys.exit(1)
        log = args[0]
        if not os.path.isfile(log):
            print("File %s does not exist" % log)
            return sys.exit(1)
        else:
            system.log_to_use = log
            if os.path.getsize(log) > 314572800 and not options.override:
                print(
                    "File is larger than 300MB, please specify the -o option to override"
                )
                return sys.exit(1)

    system.print_pretty()

    return run(system, log)


if __name__ == "__main__":
    main()
