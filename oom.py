from sys import argv
import platform


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

def neat_oom_invoke():
        print "*" * 50
        print "         !!!!OOM ISSUE!!!!"
	print "This device HAS run out of memory recently"
        print "*" * 50
        print ""
        print ""

def dates_invoked(dates):
	global all_dates
	all_dates = []
	date_of_first_invoke = line.split()[0:3]
	all_dates.append(date_of_first_invoke)

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

def check_if_incident(counter, oom_date_count, total_rss_per_incident):
	if counter > 1: # if oom invoked then print
		neat_oom_invoke()
		print "Sytem RAM: %s MB" % (system_resources())
		print ""
		# print "Dates OOM Occured"
		for i in (1, counter - 1):
			print "-" * 20
			print "Dates OOM occured: %s" % (oom_date_count[i - 1])
			print "Total Estimated RAM at OOM %s MB" % (sum(total_rss_per_incident[i] * 4 ) / 1024)
			print "-" * 20
			print ""
	else:
        	print ""
	        print "OOM has NOT occured recently!"


def OOM_record(LOG_FILE):    
  oom_date_count = []
  total_rss = {}
  with open(LOG_FILE, "r") as inLogFile, open("/home/rack/oom", "w") as outfile:
    record = False
    counter = 1
    for line in inLogFile:
      if "[ pid ]   uid  tgid total_vm      rss" in line.strip():
	total_rss[counter] = []
        record = True
	oom_count_plus_one = line.split()[0:3]
	oom_date_count.append(oom_count_plus_one)
      elif "Out of memory: Kill process" in line.strip():
        record = False
	counter += 1
      elif record:
        line = strip_line(line) # remove brackets from every line
 	outfile.write(line) # write the process values to a file
        rss_value = strip_rss(line) # calculate total value of all processes
        total_rss[counter].append(rss_value) # 
    check_if_incident(counter, oom_date_count, total_rss)

print_header()
osd = os_check()
if "centos" or "redhat" in osd.lower():
	system_rss = system_resources()
	OOM_record("/var/log/messages")
	# summary()
elif "ubuntu" or "debian" in osd.lower():
	print "Ubuntu"	
	OOM_record("/var/log/syslog")
else:
	print "Unsupported OS"
