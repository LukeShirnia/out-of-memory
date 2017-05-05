#!/usr/bin/env python
# Author:       Luke Shirnia
# Source:       https://github.com/LukeShirnia/out-of-memory-investigation.py

from sys import argv
import platform
import re
import gzip
import collections

class bcolors:
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
CentOS_RedHat_Distro = ['redhat', 'centos', 'red', 'red hat']
Ubuntu_Debian_Distro = ['ubuntu', 'debian']

def print_header():
        print bcolors.CYAN + "-" * 40 + bcolors.ENDC
        #print ""
        print "      _____ _____ _____ "
        print "     |     |     |     |"
        print "     |  |  |  |  | | | |"
        print "     |_____|_____|_|_|_|"
        #print ""
        print "     Out Of Memory Analyser"
        #print ""
        print bcolors.CYAN + "-" * 40 + bcolors.ENDC

def neat_oom_invoke():
#        print bcolors.RED + "*" * 50 + bcolors.ENDC
        print bcolors.RED + bcolors.BOLD + "######## OOM ISSUE ########" + bcolors.ENDC
#        print "This device HAS run out of memory recently"
#        print bcolors.RED + "*" * 50 + bcolors.ENDC
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
                distro = distro.split()[0]
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

def strip_rss(line, column_number):
   line = line.split()
   value = int(line[column_number-1])
   return value

def add_rss(total_rss):
   return sum((total_rss) * 4 ) / 1024

def strip_line(line):
   for ch in ["[","]","}","{","'", "(",")"]:
      if ch in line:
        line = line.replace(ch,"")
   return line


def check_if_incident(counter, oom_date_count, total_rss_per_incident, killed_services, service_value_list, LOG_FILE):
	if counter > 4:
		show_full_dates = 4
	else:
		show_full_dates = counter
        get_log_file_start_date(LOG_FILE, oom_date_count)
	date_check(oom_date_count)
        if counter > 1: # if oom invoked then print
                for i in range(1, show_full_dates):
                        print bcolors.BOLD + "-" * 40 + bcolors.ENDC
			# print "Date OOM occured:    %s" % (", ".join(oom_date_count[i - 1]))
                        # print bcolors.YELLOW + "Date OOM occured:       " + bcolors.ENDC + bcolors.CYAN + "{0} ".format(", ".join(oom_date_count[i - 1])) + bcolors.ENDC
                        print bcolors.BOLD + bcolors.PURPLE + "{0} ".format(", ".join(oom_date_count[i - 1])) + bcolors.ENDC
                        print bcolors.YELLOW + "Sytem RAM:              " + bcolors.ENDC + bcolors.CYAN + "{0} MB".format(system_resources()) + bcolors.ENDC
                        print bcolors.YELLOW + "Estimated RAM at OOM:   " + bcolors.ENDC + bcolors.CYAN + "{0} MB".format(sum(total_rss_per_incident[i] * 4 ) / 1024) + bcolors.ENDC
                        print bcolors.YELLOW + "Services" + bcolors.ENDC + bcolors.RED + " Killed:        " + bcolors.ENDC + bcolors.RED + "{0} ".format(", ".join(killed_services[i])) + bcolors.ENDC
#                        print "-" * 40
			print ""
                        print bcolors.UNDERLINE + "Top 5 RAM Consumers at time of OOM:" + bcolors.ENDC
#                        print "-" * 40
                        for x in service_value_list[i]:
                                print "Service: {0:20}  {1} MB ".format(x[0], x[1])
                        #print "-" * 40
                        print ""
        else:
                print "-" * 28
                print "OOM has NOT occured recently!"
                print "-" * 28
		print ""

def  get_log_file_start_date(LOG_FILE, oom_date_count): #function gets the start and end date of the current log file
	normal_file = (False if LOG_FILE.endswith('.gz') else True)
	inLogFile = openfile(LOG_FILE, normal_file)
	first_line = inLogFile.readline().split()[0:3]
	lineList = inLogFile.readlines()
	inLogFile.close()
	last_line = (lineList[len(lineList)-1])
	last_line = last_line.split()[0:3]
	print ""
	print bcolors.UNDERLINE + "Log Information" +bcolors.ENDC
#	print "---------------"
	print bcolors.GREEN + "Log File  : " + bcolors.YELLOW  + " %s " % (LOG_FILE) + bcolors.ENDC
	print bcolors.GREEN + "Start date: " + bcolors.ENDC + bcolors.YELLOW  + " %s " % (", ".join(first_line)) + bcolors.ENDC
	print bcolors.GREEN + "End Date  : " + bcolors.ENDC + bcolors.YELLOW  + " %s " % (", ".join(last_line)) + bcolors.ENDC
	print ""
	if len(oom_date_count) > 4:
		neat_oom_invoke()
        	print "Number of OOM occurances in log file: "  + bcolors.RED + " %s " % (len(oom_date_count)) + bcolors.ENDC
		print bcolors.HEADER + "Note: " + bcolors.ENDC + "Only Showing first " + bcolors.GREEN + "3 " +bcolors.ENDC + "OOM occurrences of the" + bcolors.RED + " %s " % (len(oom_date_count)) + bcolors.ENDC
	elif len(oom_date_count) <=4:
		neat_oom_invoke()
		"Number of OOM occurances in log file: %s " % (len(oom_date_count))
	else:
		"Number of OOM occurances in log file: %s " % (len(oom_date_count))
        print ""


# this function processes each line and saves the rss value and process name .eg (51200, apache)
def save_values(line, column_number):
        value = line.split()[-1:]
        if len(value) == 1:
                cols = line.split()
                string = cols[column_number-1], cols[-1]
                return string

# this function takes the full list of saved processes and find each unique occurance of a process
def find_unique_services(list_of_values):
        new_list = []
        for i in list_of_values:
                new_list_value = i[1]
                new_list.append(new_list_value)
        new_list = list(set(new_list))
        return new_list

# add up the rss value of the unique service list
def add_rss_for_processes(unique, list_of_values):
        values_to_add = []
        total_service_usage = []
        del total_service_usage[:]
        for i in unique:
                del values_to_add[:]
                for x in list_of_values:
                        if i == x[1]:
                                number = int(x[0])
                                values_to_add.append(number)
                added_values = ( sum(values_to_add) * 4 ) / 1024 # work out rss in MB
                string = i, added_values
                total_service_usage.append(string)
        return total_service_usage


def openfile(filename, normal_file):
	if normal_file:
		return open(filename, "r")
	elif filename.endswith('.gz'):
        	return gzip.open(filename, "r")
	else:
		return open(filename, "r")

def find_rss_column(line):
	for i, word in enumerate(line):
		if word == "rss":
			column = int(i+1)
			return column

def OOM_record(LOG_FILE):
  oom_date_count = []
  running_service = []
  list_of_values = {}
  total_rss = {}
  killed_services = {}
  unique_services = {}
  service_value_list = {}
  total_service_list = []
  normal_file = (False if LOG_FILE.endswith('.gz') else True)
  inLogFile = openfile(LOG_FILE, normal_file) #, open("/home/rack/oom", "w") as outfile:
  record = False
  record_oom_true_false = False
  counter = 1
#  get_log_file_start_date(inLogFile)  # get the start and end date of log file
  for line in inLogFile:
    killed = re.search("Killed process (.*) total", line)
    if "[ pid ]   uid  tgid total_vm      rss" in line.strip():
      total_rss[counter] = []
      killed_services[counter] = []
      unique_services[counter] = []
      list_of_values[counter] = []
      record = True
      record_oom_true_false = False
      oom_count_plus_one = line.split()[0:3]
      oom_date_count.append(oom_count_plus_one)
      line = strip_line(line)
      column_number = find_rss_column(line.split())
    elif "Out of memory: Kill process" in line.strip() or len(line.split()) < 14 and record == True:
      service_value_list[counter] = []
      list_of_values[counter] = filter(None, list_of_values[counter])
      unique = find_unique_services(list_of_values[counter])
      oom_services = add_rss_for_processes(unique, list_of_values[counter])
      oom_services = sorted(oom_services,key=lambda x: x[1], reverse=True)
      service_value_list[counter] = oom_services
      service_value_list[counter] = service_value_list[counter][:5]
      record_oom_true_false = True
      record = False
      counter += 1
    elif record:
      line = strip_line(line)
      #count_service = service_count(line)
      list_of_values[counter].append(save_values(line, column_number)) #service rss calulation initiation
      rss_value = strip_rss(line, column_number)
      total_rss[counter].append(rss_value) # calculate total value of all processes
    elif record_oom_true_false and killed:
      killed = killed.group(1)
      killed = strip_line(killed)
      killed = killed.split(",")[-1]
      killed = killed.strip("0123456789 ")
      killed_services[counter-1].append(killed)
  inLogFile.close()
  check_if_incident(counter, oom_date_count, total_rss, killed_services, service_value_list, LOG_FILE)
  #####################################################################################################################

def date_check(oom_date_count):
	dates_test = []
	for p in oom_date_count:
        	time_check = p[-1]
	        time_check = time_check.split(":")[0:1]
	        time_check = ":".join(time_check)
	        p = p[0:2]
	        p = " ".join(p)
		p = "Date: %s, Hour: %s" % (p, time_check)
	        dates_test.append(p)
	dates_and_hour =  collections.Counter(dates_test)
	list_of_dates = []
	for date in dates_test:
		string_of_dates = '%s : %d' % (date, dates_and_hour[date])
		list_of_dates.append(string_of_dates)
	list_of_dates = list(set(list_of_dates))
	print bcolors.UNDERLINE + "Date" + bcolors.ENDC + "                     " + bcolors.UNDERLINE + "Occurances" + bcolors.ENDC
	#print "-----------------------------------"
	for dates in list_of_dates:
		print dates
	print ""

###### Start script
print_header()
os_check_value = os_check()

if len(argv) == 1:
        if os_check_value.lower() in CentOS_RedHat_Distro:
                system_rss = system_resources()
                OOM_record("/var/log/messages")
        elif os_check_value.lower() in Ubuntu_Debian_Distro:
                OOM_record("/var/log/syslog")
        else:
                print "Unsupported OS"
elif len(argv) == 2:
        script, OOM_LOG = argv
        if os_check_value.lower() in CentOS_RedHat_Distro:
                system_rss = system_resources()
                OOM_record(OOM_LOG)
        elif os_check_value.lower() in Ubuntu_Debian_Distro:
                OOM_record(OOM_LOG)
        else:
                print "Unsupported OS"
else:
        print "Too Many Arguments"
        print "Try again"
        print len(argv)


# test
