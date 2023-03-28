#!/usr/bin/env python
#
# Author:       Luke Shirnia
# Source:       https://github.com/LukeShirnia/out-of-memory/
from __future__ import print_function

import os
import warnings

warnings.filterwarnings(
    "ignore", category=DeprecationWarning
)  # Hide platform.dist() related deprecation warnings


VERSION = "1.0.0"

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


class System(Printer):
    """System information"""

    def __init__(self):
        _id, _version, _ = self.get_distro_info()
        self.id = _id or "unknown"
        self.version = _version or "Unknown Version"

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


if __name__ == "__main__":
    system = System()
    print(system)
