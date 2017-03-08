from sys import argv

script, LOG_FILE = argv
total_rss = []

def print_header():

        print "-" * 40
        print ""
        print "      _____ _____ _____ "
        print "     |     |     |   _ |"
        print "     |  |  |  |  | | | |"
        print "     |_____|_____|_|_|_|"
        print ""
        print "     Out Of Memory Analyser"
        print ""
        print "-" * 40
        print ""

def system_resources():
   with open("/proc/meminfo", "r") as meminfo:
      for lines in meminfo:
         if "MemTotal" in lines.strip():
            memory_value = int(lines.split()[1])
            system_memory = memory_value / 1024
            return system_memory

def strip_rss(line):
   rss_to_add = []
   value = int(line.split()[10])
   return value

def add_rss(total_rss):
   args = []
   return sum(total_rss)

def strip_line(line):
   for ch in ["[","]"]:
      if ch in line:
        line = line.replace(ch,"")
   return line

def calc_rss(adding_rss):
   total = sum(adding_rss)
   return total


with open(LOG_FILE, "r") as inLogFile, open("/home/rack/oom", "w") as outfile:
  record = False
  for line in inLogFile:
    if "[ pid ]   uid  tgid total_vm      rss" in line.strip():
      record = True
    elif "Out of memory: Kill process" in line.strip():
      record = False
    elif record:
      line = strip_line(line)
      outfile.write(line)
      rss_value = strip_rss(line)
      total_rss.append(rss_value)


print_header()
system_rss = system_resources()
print "Total System Memory:                 %s MB" % (system_rss)
total_ram = ( add_rss(total_rss) * 4 ) / 1024
print "Estimated RAM usage at OOM incident: %s MB" % (total_ram)
print ""
print "-" * 40
