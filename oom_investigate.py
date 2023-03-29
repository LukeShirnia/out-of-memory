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


class Printer(object):  # {{{
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


def main_header():
    """
    Disclaimer and Script Header
    """
    colours = Printer()
    horizontal_line = "-" * 40
    analyzer_name = "Out Of Memory Analyzer"
    current_year = datetime.datetime.now().year
    author_name = "LukeShirnia"
    disclaimer_text = "If system OOMs too viciously, there may be nothing logged!"
    warning_text = "Do NOT take this script as FACT, ALWAYS investigate further."

    print(f"{colours.CYAN}{horizontal_line}{colours.RESET}")
    print("      _____ _____ _____ ")
    print("     |     |     |     |")
    print("     |  |  |  |  | | | |")
    print("     |_____|_____|_|_|_|")
    print(f"     {analyzer_name}")
    print("")
    print(f"\u00A9 {current_year} {author_name}")
    print("")
    print(f"{colours.RED}{colours.UNDERLINE}Disclaimer:{colours.RESET}")
    print(f"{colours.RED}{disclaimer_text}")
    print(f"{warning_text}{colours.RESET}")
    print(f"{colours.CYAN}{horizontal_line}{colours.RESET}")


class System(Printer):
    """System information"""

    def __init__(self):
        _id, _version, _ = self.get_distro_info()
        self.id = _id or "unknown"
        self.version = _version or "Unknown Version"
        self.log_files = []
        self.find_logs()

        if self.id in ["redhat", "rhel"]:
            self.id = "redhat"
            self.distro = "RHEL"
        elif self.id == "centos":
            self.distro = "CentOS"
        elif self.id == "fedora":
            self.distro = "Fedora"
        elif self.id == "oracle":
            self.distro = "Oracle"
        elif self.id in ["Ubuntu", "ubuntu"]:
            self.id = "Ubuntu"
            self.distro = "Ubuntu"
        elif self.id == "debian":
            self.distro = "Debian"
        elif self.id == "almalinux":
            self.distro = "Alma Linux"
        elif self.id in ["Rocky Linux", "rocky"]:
            self.id = "Rocky Linux"
            self.distro = "Rocky Linux"
        elif "Amazon Linux" in self.id or self.id == "amazon":
            self.distro = "Amazon"
            self.id = "amazon"
        else:
            self.distro = self.id

        distroversion = "%s %s" % (self.distro, self.version)
        self._system = self._ok(distroversion)
        self._lines = ["OS: " + self._system]

    def __str__(self):
        return self._system

    def parse_os_release(self):
        # Borrowed from the parse_os_release helper in rs-block-storage
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

        if self.log_files:
            return self.log_files
        else:
            return None

    def print_pretty(self):
        for line in self._lines:
            print(line)


def run(log_file):
    pass


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
        print("Error: Unable to find log file for this Operating System")
        return sys.exit(1)
    system.print_pretty()

    if options.file:
        if len(args) == 0:
            print("Please specify a log file to check")
            return sys.exit(1)
        log = args[0]
        if not os.path.isfile(log):
            print("File %s does not exist" % log)
            sys.exit(1)
        else:
            if os.path.getsize(log) > 314572800 and not options.override:
                print(
                    "File is larger than 300MB, please specify the -o option to override"
                )
                sys.exit(1)
            else:
                print(f"Checking file {log}")
                print("")

    return run(log)


if __name__ == "__main__":
    main()
