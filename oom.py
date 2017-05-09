#!/usr/bin/env python
# Author:       Luke Shirnia
# Source:       https://github.com/LukeShirnia/out-of-memory-investigation.py

from sys import argv
import platform
import re
import gzip
import datetime
import operator
import os
import fnmatch

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
        print ""
	print bcolors.RED + bcolors.UNDERLINE + "Disclaimer:" + bcolors.ENDC
	print bcolors.RED + "If system OOMs too viciously, there may be nothing logged!"
	print "Do NOT take this script as FACT, investigate further" + bcolors.ENDC
        print bcolors.CYAN + "-" * 40 + bcolors.ENDC


def neat_oom_invoke():
        print bcolors.RED + bcolors.BOLD + "######## OOM ISSUE ########" + bcolors.ENDC
        print ""


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
	date_format = []
        for p in oom_date_count:
                p = datetime.datetime.strftime(p, '%b %d %H:%M:%S')
                date_format.append(p)
	if counter > 4:
		show_full_dates = 4
	else:
		show_full_dates = counter
        get_log_file_start_date(LOG_FILE, oom_date_count)
        if counter > 1: # if oom invoked then print
		date_check(oom_date_count)
                for i in (1, 2, counter - 1):
                        print bcolors.BOLD + "-" * 40 + bcolors.ENDC
                        print bcolors.BOLD + bcolors.PURPLE + "{0} ".format(date_format[i - 1]) + bcolors.ENDC
                        print bcolors.YELLOW + "Sytem RAM:              " + bcolors.ENDC + bcolors.CYAN + "{0} MB".format(system_resources()) + bcolors.ENDC
                        print bcolors.YELLOW + "Estimated RAM at OOM:   " + bcolors.ENDC + bcolors.CYAN + "{0} MB".format(sum(total_rss_per_incident[i] * 4 ) / 1024) + bcolors.ENDC
                        print bcolors.YELLOW + "Services" + bcolors.ENDC + bcolors.RED + " Killed:        " + bcolors.ENDC + bcolors.RED + "{0} ".format(", ".join(killed_services[i])) + bcolors.ENDC
			print ""
                        print bcolors.UNDERLINE + "Top 5 RAM Consumers at time of OOM:" + bcolors.ENDC
                        for x in service_value_list[i]:
                                print "Service: {0:20}  {1} MB ".format(x[0], x[1])
                        print ""
        else:
                print "-" * 40
                print "OOM has " + bcolors.GREEN + "NOT" +bcolors.ENDC + " occured in specified log file!"
                print "-" * 40
		print ""
		quick_check_all_logs(find_all_logs(OOM_LOG)) # print similar log files to check for an issue
		print ""


def find_all_logs(OOM_LOG): # function to find all other similar logs
	result = []
	split_log_file_dir = os.path.dirname(OOM_LOG)
	split_log_file_name = os.path.basename(OOM_LOG)
	split_log_file_name = split_log_file_name + '*'
	for root, dirs, files in os.walk(split_log_file_dir):
        	for name in files:
	            if fnmatch.fnmatch(name, split_log_file_name):
			result.append(os.path.join(root, name))
	result.sort()
	if len(result) > 1:
		print bcolors.YELLOW + "Other Logs worth checking:" + bcolors.ENDC
		while OOM_LOG in result:
			result.remove(OOM_LOG)
#		for i in result:
#			print i
	return result


def quick_check_all_logs(results):
	for a in results:
		total_occurences = []
		del total_occurences[:]
		total_occurences = 0
		normal_file = (False if a.endswith('.gz') else True)
	        inLogFile = openfile(a, normal_file)
		for line in inLogFile:
			if "[ pid ]   uid  tgid total_vm      rss" in line.strip():
				total_occurences += 1
		print "{0} - Occurences: {1}".format(a, total_occurences)


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
	print bcolors.GREEN + "Log File  : " + bcolors.YELLOW  + " %s " % (LOG_FILE) + bcolors.ENDC
	print bcolors.GREEN + "Start date: " + bcolors.ENDC + bcolors.YELLOW  + " %s " % (", ".join(first_line)) + bcolors.ENDC
	print bcolors.GREEN + "End Date  : " + bcolors.ENDC + bcolors.YELLOW  + " %s " % (", ".join(last_line)) + bcolors.ENDC
	print ""
	if len(oom_date_count) > 4:
		neat_oom_invoke()
        	print "Number of OOM occurances in log file: "  + bcolors.RED + " %s " % (len(oom_date_count)) + bcolors.ENDC
	elif len(oom_date_count) <=4 and len(oom_date_count) > 0:
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


# used to find out if a compressed file is being used or not
def openfile(filename, normal_file):
	if normal_file:
		return open(filename, "r")
	elif filename.endswith('.gz'):
        	return gzip.open(filename, "r")
	else:
		return open(filename, "r")


def find_rss_column(line): #function to find the column number of rss header (for OS compatibility)
	for i, word in enumerate(line):
		if word == "rss":
			column = int(i+1)
			return column


def date_time(line):                   # return a date object
	date_of_oom = line.split()[0:3]
	date_of_oom = " ".join(date_of_oom)
	date_check = datetime.datetime.strptime(date_of_oom, "%b %d %H:%M:%S")
	return date_check


def strip_time(date_time): # remove mins and seconds from date and time
	return date_time + datetime.timedelta(hours = 1, minutes = -date_time.minute, seconds = -date_time.second)


def date_time_counter_split(dates_sorted): # split the date and count ('May 12': 1) into 2 strings and back into 1 string
	sorted_dates = []
	for i in dates_sorted:
		date = datetime.datetime.strptime(i[0], "%m-%d %H")
		date = datetime.datetime.strftime(date, "%b %d %H")
		occurences = i[1]
		sorted_dates.append(date + " " + str(occurences))
	return sorted_dates


def date_check(oom_date_count): #this function is used to produce a list of dates +inc hour of every oom occurence in the log file
        dates_test = []
	dates_sorted = []
        oom_date_count.sort()
        for p in oom_date_count:
		time = strip_time(p) # removing mm and ss from time (leaving only hour)
		time = datetime.datetime.strftime(p, '%m-%d %H')
                dates_test.append(time)
#	dates_test = collections.Counter(dates_test) # uniq occurences ---- does not working with python 2.6.x
	dates_test = dict((i, dates_test.count(i)) for i in dates_test)
	dates_sorted = sorted(dates_test.iteritems())
	dates_test = date_time_counter_split(dates_sorted)
        print bcolors.YELLOW + bcolors.UNDERLINE + "KEY" + bcolors.ENDC + bcolors.YELLOW
        print "D = Dates"
        print "H = Hour"
        print "O = Number of Occurences" + bcolors.ENDC
        print ""
        print bcolors.UNDERLINE + "D" + bcolors.ENDC + "      " + bcolors.UNDERLINE + "H" + bcolors.ENDC +  "  "  + bcolors.UNDERLINE  + bcolors.UNDERLINE + "O" + bcolors.ENDC
	for value in dates_test:
		print value
        print ""
	print ""
        if len(oom_date_count) > 4:
		print bcolors.HEADER + bcolors.UNDERLINE  + "Note:" + bcolors.ENDC + " Only Showing: " + bcolors.GREEN + "3 " + bcolors.ENDC + "of the" + bcolors.RED + " %s occurences" % (len(oom_date_count)) + bcolors.ENDC
		print "Showing the " + bcolors.GREEN  + "1st" + bcolors.ENDC + ", " + bcolors.GREEN  + "2nd" + bcolors.ENDC + " and" + bcolors.GREEN + " last" + bcolors.ENDC


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
      oom_date_count.append(date_time(line))
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


###### Start script
print_header()
os_check_value = os_check()

if len(argv) == 1:
        if os_check_value.lower() in CentOS_RedHat_Distro:
                system_rss = system_resources()
		OOM_LOG = "/var/log/messages"
                OOM_record(OOM_LOG)
		print bcolors.BOLD + "-" * 40 + bcolors.ENDC
        elif os_check_value.lower() in Ubuntu_Debian_Distro:
		OOM_LOG = "/var/log/syslog"
                OOM_record(OOM_LOG)
		print bcolors.BOLD + "-" * 40 + bcolors.ENDC
        else:
                print "Unsupported OS"
elif len(argv) == 2:
        script, OOM_LOG = argv
        if os_check_value.lower() in CentOS_RedHat_Distro:
                system_rss = system_resources()
		try:
	                OOM_record(OOM_LOG)
		except Exception as error:
			print ""
			print bcolors.RED + "Error:" + bcolors.ENDC
			print error
			print ""
		print bcolors.BOLD + "-" * 40 + bcolors.ENDC
        elif os_check_value.lower() in Ubuntu_Debian_Distro:
                OOM_record(OOM_LOG)
        else:
                print "Unsupported OS"
else:
        print "Too Many Arguments"
        print "Try again"
        print len(argv)

