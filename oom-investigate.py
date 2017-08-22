#!/usr/bin/env python
# Author:       Luke Shirnia
# Source:       https://github.com/LukeShirnia/out-of-memory/

from sys import argv
import sys
import platform
import re
import gzip
import datetime
import operator
import os
import fnmatch
import collections

class bcolors:
    '''
	Class used for colour formatting
    '''
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
	'''
	Disclaimer and Script Header
	'''
        print bcolors.CYAN + "-" * 40 + bcolors.ENDC
        print "      _____ _____ _____ "
        print "     |     |     |     |"
        print "     |  |  |  |  | | | |"
        print "     |_____|_____|_|_|_|"
        print "     Out Of Memory Analyser"
        print ""
	print bcolors.RED + bcolors.UNDERLINE + "Disclaimer:" + bcolors.ENDC
	print bcolors.RED + "If system OOMs too viciously, there may be nothing logged!"
	print "Do NOT take this script as FACT, investigate further" + bcolors.ENDC
        print bcolors.CYAN + "-" * 40 + bcolors.ENDC


def neat_oom_invoke():
	'''
	Print WARNING if there is an OOM issue
	'''
        print bcolors.RED + bcolors.BOLD + "######## OOM ISSUE ########" + bcolors.ENDC
        print ""


def os_check():
	'''
	Make sure this is being run on a Linux device first	
	'''
        os_platform = platform.system()
        if os_platform == "Linux":
                distro = platform.linux_distribution()[0]
                distro = distro.split()[0]
                return distro
        else:
                print "Stop Using a Rubbish OS!!"


def system_resources():
	'''
	Get the RAM info from /proc
	'''
	with open("/proc/meminfo", "r") as meminfo:
		for lines in meminfo:
			if "MemTotal" in lines.strip():
				memory_value = int(lines.split()[1])
				system_memory = memory_value / 1024
				return system_memory


def strip_rss(line, column_number):
	'''
	Obtain the RSS value of a service from the line
	'''
	line = line.split()
	value = int(line[column_number-1])
	return value


def add_rss(total_rss):
	'''
	Covert RSS value to RAM ( * 4)
	'''
	return sum((total_rss) * 4 ) / 1024


def strip_line(line):
	'''
	Stripping all non required characters from the line so not to interfere with line.split()
	'''
	for ch in ["[","]","}","{","'", "(",")"]:
		if ch in line:
			line = line.replace(ch,"")
	return line


def print_oom_output(i, date_format, system_resources, total_rss_per_incident, killed_services, service_value_list):
	'''
	Print the Output of an OOM incident (Inc TOP 5 RAM consumers)
	'''
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



def check_if_incident(counter, oom_date_count, total_rss_per_incident, killed_services, service_value_list, LOG_FILE, all_killed_services):
	'''
	Check if OOM incident occurred. ADD FUNCTION TO PROMPT FOR OTHER LOG FILES
	'''
	date_format = []
        for p in oom_date_count:
                p = datetime.datetime.strftime(p, '%b %d %H:%M:%S')
                date_format.append(p)
	if counter > 4:
		show_full_dates = 4
	else:
		show_full_dates = counter
        get_log_file_start_date(LOG_FILE, oom_date_count, all_killed_services)
	counter = counter - 1
        if counter == 1: # if only 1 instance of oom then print all
		date_check(oom_date_count)
                #for i in (1):
		i = 1
		print_oom_output(i, date_format, system_resources, total_rss_per_incident, killed_services, service_value_list,)
	elif counter == 2: # if only 3 instance of oom then print all
		date_check(oom_date_count)
		for i in (1, 2):
                        print_oom_output(i, date_format, system_resources, total_rss_per_incident, killed_services, service_value_list)
	elif counter >= 3: # if more 3 or more oom instances, print 1st, 2nd, last
		date_check(oom_date_count)
		for i in (1, 2, counter - 1):
                        print_oom_output(i, date_format, system_resources, total_rss_per_incident, killed_services, service_value_list)
        else:
                print "-" * 40
                print "OOM has " + bcolors.GREEN + "NOT" +bcolors.ENDC + " occured in specified log file!"
                print "-" * 40
		print ""
		#quick_check_all_logs(find_all_logs(OOM_LOG)) # print similar log files to check for an issue
		quick_check_all_logs(find_all_logs(LOG_FILE)) # print similar log files to check for an issue
		print ""


def find_all_logs(OOM_LOG):
	'''
	This function finds all log files in the directory of default log file (or specified log file)
	'''
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
		print bcolors.YELLOW + "Checking other logs, select an option:" + bcolors.ENDC
		while OOM_LOG in result:
			result.remove(OOM_LOG)
	return result


def quick_check_all_logs(results):
	'''
	Quickly check all log files for oom incidents
	'''
	option = 1
	next_logs_to_search = []
	del next_logs_to_search[:]
	for a in results:
		total_occurences = []
		del total_occurences[:]
		total_occurences = 0
		normal_file = (False if a.endswith('.gz') else True)
	        inLogFile = openfile(a, normal_file)
		for line in inLogFile:
			if "[ pid ]   uid  tgid total_vm      rss" in line.strip():
				total_occurences += 1
		if total_occurences >= 1:
			print bcolors.GREEN + "Option: {0}".format(option) + bcolors.ENDC + "  {0:26} - Occurrences: {1}".format(a, total_occurences)
			next_logs_to_search.append(a)
			option +=1
		else:
			print "           {0:26} - Occurrences: {1}".format(a, total_occurences)
	select_next_logfile(next_logs_to_search)


def select_next_logfile(log_file):
	'''
	This function is for the user to select the next log file they wish to inspect `if OOM count >= 1` in another log file (inspected in the previous function)
	'''
	if len(log_file) >= 1:
		print 
		incorrect = True
		while incorrect:
			Not_Integer = True
			while Not_Integer:
				print "Which file should we check next?"
				option_answer = raw_input("Select an option number between 1 and " + str(len(log_file)) + ": " )
				if option_answer.isdigit(): 
					option_answer = int(option_answer)	
					option_answer -= 1
					if ( option_answer ) <= ( len(log_file) - 1 ) and ( option_answer ) >= 0: 
						new_log_file = log_file[option_answer]
						OOM_record(new_log_file)
						incorrect = False
						Not_Integer = False
					else:
						print "Option number out of range, try again:"
						print
				else:
					print "Please select an number"


def  get_log_file_start_date(LOG_FILE, oom_date_count, all_killed_services):
	'''
	Get the start and end date of the current log file
	'''
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
        	print "Number of OOM occurrence in log file: "  + bcolors.RED + " %s " % (len(oom_date_count) -1 ) + bcolors.ENDC
	elif len(oom_date_count) <=4 and len(oom_date_count) > 0:
		neat_oom_invoke()
		"Number of OOM occurrence in log file: %s " % (len(oom_date_count))
	else:
		"Number of OOM occurrence in log file: %s " % (len(oom_date_count))
        print ""
	all_killed_services = dict((i, all_killed_services.count(i)) for i in all_killed_services) # working dict count
	ServiceCount = sorted( ((v,k) for k,v in all_killed_services.iteritems()), reverse=True)
	for i in ServiceCount:
		print "Service " + bcolors.RED + "{0:12} ".format(i[1]) + bcolors.ENDC +  "Killed " + bcolors.RED + "{0} ".format(i[0]) + bcolors.ENDC + "time(s)"
	print ""


def save_values(line, column_number):
	'''
	This function processes each line (when record = True) and saves the rss value and process name .eg (51200, apache)
	'''
        value = line.split()[-1:]
        if len(value) == 1:
                cols = line.split()
                string = cols[column_number-1], cols[-1]
                return string


def find_unique_services(list_of_values):
	'''
	Finding the unique list of killed services (excludes the duplicated, eg apache, apache, apache is just apache)
	'''
        new_list = []
        for i in list_of_values:
                new_list_value = i[1]
                new_list.append(new_list_value)
        new_list = list(set(new_list))
        return new_list


def add_rss_for_processes(unique, list_of_values):
	'''
	Adding the RSS value of each service
	'''
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
	'''
	Check if input file is a compressed or regular file
	'''
	if normal_file:
		return open(filename, "r")
	elif filename.endswith('.gz'):
        	return gzip.open(filename, "r")
	else:
		return open(filename, "r")


def find_rss_column(line): 
	'''
	This check finds the correct column for RSS
	Each distribution and version may log differently, this allows to catch all, for Linux OS compatibility
	'''
	for i, word in enumerate(line):
		if word == "rss":
			column = int(i+1)
			return column


def date_time(line):
	'''
	Creates a date object from an extracted string retreived from the log line
	'''
	date_of_oom = line.split()[0:3]
	date_of_oom = " ".join(date_of_oom)
	date_check = datetime.datetime.strptime(date_of_oom, "%b %d %H:%M:%S")
	return date_check


def strip_time(date_time):
	'''
	Used to summarise the hour OOM's occurred (excludes the mins and seconds)
	'''
	return date_time + datetime.timedelta(hours = 1, minutes = -date_time.minute, seconds = -date_time.second)

	
def date_time_counter_split(dates_sorted):
	'''
	Split the date and OOM count ('May 12': 1) into 2 strings and back into 1 string
	'''
	sorted_dates = []
	for i in dates_sorted:
		date = datetime.datetime.strptime(i[0], "%m-%d %H")
		date = datetime.datetime.strftime(date, "%b %d %H")
		occurences = i[1]
		sorted_dates.append(date + " " + str(occurences))
	return sorted_dates

	
def date_check(oom_date_count):
	'''
	The function is used to produce a list of dates +inc hour of every oom occurrence in the log file
	'''
        dates_test = []
	dates_sorted = []
        oom_date_count.sort()
        for p in oom_date_count:
		time = strip_time(p) # removing mm and ss from time (leaving only hour)
		time = datetime.datetime.strftime(p, '%m-%d %H')
                dates_test.append(time)
	dates_test = dict((i, dates_test.count(i)) for i in dates_test)
	dates_sorted = sorted(dates_test.iteritems())
	dates_test = date_time_counter_split(dates_sorted)
        print bcolors.YELLOW + bcolors.UNDERLINE + "KEY" + bcolors.ENDC + bcolors.YELLOW
        print "D = Date(s) OOM"
        print "H = Hour OOM Occurred"
        print "O = Number of Occurrences in Date/Hour" + bcolors.ENDC
        print ""
        print bcolors.UNDERLINE + "D" + bcolors.ENDC + "      " + bcolors.UNDERLINE + "H" + bcolors.ENDC +  "  "  + bcolors.UNDERLINE  + bcolors.UNDERLINE + "O" + bcolors.ENDC
	for value in dates_test:
		print value
	
        print ""
	print ""
        if len(oom_date_count) >= 3:
		print bcolors.HEADER + bcolors.UNDERLINE  + "Note:" + bcolors.ENDC + " Only Showing: " + bcolors.GREEN + "3 " + bcolors.ENDC + "of the" + bcolors.RED + " %s occurrence" % (len(oom_date_count)) + bcolors.ENDC
		print "Showing the " + bcolors.GREEN  + "1st" + bcolors.ENDC + ", " + bcolors.GREEN  + "2nd" + bcolors.ENDC + " and" + bcolors.GREEN + " last" + bcolors.ENDC


def OOM_record(LOG_FILE):
  '''
	Takes 1 argument - the log file to check
	Checks line-by-line for specific string match that indicated OOM has taken place
  '''
  oom_date_count = []
  running_service = []
  list_of_values = {}
  total_rss = {}
  killed_services = {}
  unique_services = {}
  service_value_list = {}
  total_service_list = []
  all_killed_services = []
  normal_file = (False if LOG_FILE.endswith('.gz') else True)
  inLogFile = openfile(LOG_FILE, normal_file) #, open("/home/rack/oom", "w") as outfile:
  record = False
  record_oom_true_false = False
  counter = 1
  oom_line_length = 0
  for line in inLogFile:
    killed = re.search("Killed process (.*) total", line)
    if "[ pid ]   uid  tgid total_vm      rss" in line.strip() and "kernel" in line.lower():
      oom_line_length = len(line.strip())
      total_rss[counter] = []
      killed_services[counter] = []
      unique_services[counter] = []
      list_of_values[counter] = []
      record = True
      record_oom_true_false = False
      oom_date_count.append(date_time(line))
      line = strip_line(line)
      column_number = find_rss_column(line.split())
    elif "kernel" not in line.lower() and record == True: # Skips log entries that may be interfering with oom output from kernel
      pass
    elif " hi:" in line.strip() and record == True:
      pass
    elif "MAC=" in line.strip() and record == True: # Skips log entires in Ubuntu/Debian intefering with oom output
      pass
    elif "Out of memory" in line.strip() and record == True or len(line.split()) < 14  and record == True :
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
      all_killed_services.append(killed)
  inLogFile.close()
  check_if_incident(counter, oom_date_count, total_rss, killed_services, service_value_list, LOG_FILE, all_killed_services)


def file_size(file_path):
    """
    This function will return the file size of the script.
    Currently HUGE OOM log file will cause memory issues, this is to prevent that
    """
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return int((file_info.st_size) / 1024 ) / 1024


def begin_script():
	'''
	Checks OS distribution and accepts arguments
	'''
	print_header()
	os_check_value = os_check()
	if len(argv) == 1:
        	if os_check_value.lower() in CentOS_RedHat_Distro:
                	system_rss = system_resources()
			OOM_LOG = "/var/log/messages"
			if file_size(OOM_LOG) < 250:
		                OOM_record(OOM_LOG)
				print bcolors.BOLD + "-" * 40 + bcolors.ENDC
			else:
				print 
				print "!!! File is too LARGE !!!"
				print "Please consider splitting the file into smaller chunks (such as dates)"
	        elif os_check_value.lower() in Ubuntu_Debian_Distro:
			OOM_LOG = "/var/log/syslog"
			if file_size(OOM_LOG) < 250:
		                OOM_record(OOM_LOG)
				print bcolors.BOLD + "-" * 40 + bcolors.ENDC
			else:
				print
	                        print "!!! File is too LARGE !!!"
	                        print "Please consider splitting the file into smaller chunks (such as dates)"
	        else:
	                print "Unsupported OS"
	elif len(argv) == 2:
	        script, OOM_LOG = argv
	        if os_check_value.lower() in CentOS_RedHat_Distro:
	                system_rss = system_resources()
			if file_size(OOM_LOG) < 250: # check file size is below 250 MB
				try:
	       		       		OOM_record(OOM_LOG)
				except Exception as error:
					print ""
					print bcolors.RED + "Error:" + bcolors.ENDC
					print error
					print ""
				print bcolors.BOLD + "-" * 40 + bcolors.ENDC
			else:
				print
				print "!!! File is too LARGE !!!"
	                        print "Please consider splitting the file into smaller chunks (such as dates)"
	        elif os_check_value.lower() in Ubuntu_Debian_Distro:
			if file_size(OOM_LOG) < 250:
		                OOM_record(OOM_LOG)
			else:
				print
	                        print "!!! File is too LARGE !!!"
	                        print "Please consider splitting the file into smaller chunks (such as dates)"
	        else:
	                print "Unsupported OS"
	else:
	        print "Too Many Arguments - ", ( len(argv) -1 )
		print "Try again"

try:
	begin_script()
except(EOFError, KeyboardInterrupt):
	print
	sys.exit(0)
