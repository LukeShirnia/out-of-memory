from sys import argv
import platform

total_rss = []
total_individual = []

def print_header():
        print "-" * 40
        print ""
        print "      _____ _____ _____ "
        print "     |     |     |     |"
        print "     |  |  |  |  | | | |"
        print "     |_____|_____|_|_|_|"
        print ""
        print "     Out Of Memory Analyser"
        print ""
        print "-" * 40
        print ""

def print_oom_invoked(line):
        print "*" * 30
        print "Out-Of-Memory HAS been invoked by the kernel recently"
        print "*" * 30
        print ""
        print ""
        date_of_first_invoke = line.split()[0:3]
        print "Date Of OOM: %s" % (date_of_first_invoke)

def summary():
        print "Total System Memory:                 %s MB" % (system_rss)
        total_ram = add_rss(total_rss)
        print "Estimated RAM usage at OOM incident: %s MB" % (total_ram)
        print ""
        print "-" * 40

def os_check():
        os_platform = platform.system()
        if os_platform == "Linux":
                distro = platform.linux_distribution()[0]
                return distro
        else:
                print "Stop Using a Rubbish OS!!"

def system_resources():
   with open("/proc/meminfo", "r") as meminfo:
      for lines in meminfo:
         if "MemTotal" in lines.strip():
            memory_value = int(lines.split()[1])
            system_memory = memory_value / 1024
            return system_memory

def strip_rss(line):
   value = int(line.split()[10])
   return value

def add_rss(total_rss):
   return sum((total_rss) * 4 ) / 1024

def strip_line(line):
   for ch in ["[","]"]:
      if ch in line:
        line = line.replace(ch,"")
   return line

def OOM_record(LOG_FILE):
  with open(LOG_FILE, "r") as inLogFile, open("/home/rack/oom", "w") as outfile:
    record = False
    for line in inLogFile:
      if "[ pid ]   uid  tgid total_vm      rss" in line.strip():
        record = True
        print_oom_invoked(line)
      elif "Out of memory: Kill process" in line.strip():
        record = False
      elif record:
        line = strip_line(line) # remove brackets from every line
        outfile.write(line) # write the process values to a file
        rss_value = strip_rss(line) # calculate total value of all processes
        total_rss.append(rss_value) #

print_header()
osd = os_check()
if "centos" or "redhat" in osd.lower():
        system_rss = system_resources()
        OOM_record("/var/log/messages")
        summary()
elif "ubuntu" or "debian" in osd.lower():
        print "Ubuntu"
        OOM_record("/var/log/syslog")
else:
        print "Unsupported OS"
