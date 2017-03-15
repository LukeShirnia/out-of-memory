#!/usr/bin/env python
# Author:       Luke Shirnia
# Source:       https://github.com/LukeShirnia/out-of-memory-investigation.py

from sys import argv
import platform
import re
import gzip

total_individual = []
CentOS_RedHat_Distro = ['redhat', 'centos', 'red', 'red hat']
Ubuntu_Debian_Distro = ['ubuntu', 'debian']

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


def check_if_incident(counter, oom_date_count, total_rss_per_incident, killed_services, service_value_list):
        if counter > 1: # if oom invoked then print
                neat_oom_invoke()
                # print "Dates OOM Occured"
                for i in range(1, counter):
                        print "-" * 40
                        print "Date OOM occured:    %s" % (", ".join(oom_date_count[i - 1]))
                        print "Sytem RAM: {0:14} MB".format(system_resources())
                        print "Estimated RAM at OOM: %s MB" % (sum(total_rss_per_incident[i] * 4 ) / 1024)
                        print "Services Killed:      %s " % (", ".join(killed_services[i]))
                        print "-" * 40
                        print "Top 5 RAM Consumers at time of OOM:"
                        print "-" * 40
                        for x in service_value_list[i]:
                                print "Service: {0:20}  {1} MB ".format(x[0], x[1])
                        print "-" * 40
                        print ""
                        print ""
        else:
                print ""
                print "OOM has NOT occured recently!"
                print ""

#def service_count(line):
#        value = line.split()[-1:]
#        if len(value) == 1:
#                return value


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
      killed = killed.strip("0123456789 ")
      killed_services[counter-1].append(killed)
  inLogFile.close()
  check_if_incident(counter, oom_date_count, total_rss, killed_services, service_value_list)


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
