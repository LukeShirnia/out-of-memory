# Out-Of-Memory Investigation .py


The following python script can be used to calculate the estimated RSS (RAM) value of each service at the time a kernel invoked OOM killer. At the time of an OOM incident, the system logs the estimated RSS value of each service in its system log, this script will calculate how much RAM the services were "theorietically" trying to use, the total RAM value of all services and how much RAM your system actually has to offer these services. 


The script looks in `/var/log/messages` or `/var/log/syslog` and takes the values recorded by the system just before the incident occurs. 




<br />

There are currently 2 usage methods. 
<br />

### Method 1
The first and most straight foward is simply running the command below:

```
curl -s https://raw.githubusercontent.com/LukeShirnia/out-of-memory-investigation.py/master/oom.py | python
```
### Method 2
You can also specify a specific log file if you are looking into historical data, or the logs have been rotated. 

Note: This WILL work with compressed log files!

Replace `/var/log/messages.1` with the log file you wish to analyse. 
```
curl -s https://raw.githubusercontent.com/LukeShirnia/out-of-memory-investigation.py/master/oom.py | python - /var/log/messages.1
```
<br />

<br />

The script currently works on the following OS:

*  RedHat 6,7

*  CentOS 6,7

*  Ubuntu 14.04LTS

***  Redhat/CentOS 5 - Only works on some devices,AND you need to specify python2.6 or 2.6  ***
<br />

*** Testing on Ubuntu and Debian ongoing.  ***


<br />

<br />



### Example Output
The following example shows the output of the script when run against a compressed log file in a "non standard" directory:

```
----------------------------------------
      _____ _____ _____ 
     |     |     |     |
     |  |  |  |  | | | |
     |_____|_____|_|_|_|
     Out Of Memory Analyser
----------------------------------------

Log Information
Log File  :  /home/python/rackspace/messages-20170219.gz 
Start date:  Feb, 12, 05:20:01 
End Date  :  Feb, 19, 00:44:24 

######## OOM ISSUE ########

Number of OOM occurances in log file:  68 

KEY
D = Dates
H = Hour
O = Number of Occurences

D      H  O
Feb 12 10 68


Note: Only Showing: 3 of the 68 occurences
Showing the 1st, 2nd and last
----------------------------------------
Mar, 9, 10:58:55
Sytem RAM:            987 MB
Estimated RAM at OOM: 1509 MB
Services Killed:      mysqld, apache

Top 5 RAM Consumers at time of OOM:
Service: apache2               1370 MB
Service: mysqld                251 MB
Service: 4                     59 MB
Service: driveclient           12 MB
Service: fail2ban-server       10 MB

----------------------------------------
Mar, 9, 10:59:57
Sytem RAM:            987 MB
Estimated RAM at OOM: 1555 MB
Services Killed:      mysqld

Top 5 RAM Consumers at time of OOM:
Service: apache2               1160 MB
Service: mysqld                230 MB
Service: driveclient           16 MB
Service: sshd                  16 MB
Service: rackspace-monit       15 MB

----------------------------------------
Mar, 9, 11:37:32
Sytem RAM:            987 MB
Estimated RAM at OOM: 1369 MB
Services Killed:      mysqld

Top 5 RAM Consumers at time of OOM:
Service: apache2               1041 MB
Service: mysqld                197 MB
Service: sshd                  24 MB
Service: driveclient           16 MB
Service: rackspace-monit       15 MB
----------------------------------------
```
<br />

<br />

### Example 
This example shows the output when NO oom has occured in the log file. NO options were passed with the running of this script (Method 1 was used) 

```
----------------------------------------
      _____ _____ _____ 
     |     |     |     |
     |  |  |  |  | | | |
     |_____|_____|_|_|_|
     Out Of Memory Analyser
----------------------------------------

Log Information
Log File  :  /var/log/messages 
Start date:  May, 7, 08:08:18 
End Date  :  May, 8, 14:30:01 


----------------------------------------
OOM has NOT occured in specified log file!
----------------------------------------

Other Logs worth checking:
/var/log/messages-20170416
/var/log/messages-20170424
/var/log/messages-20170430
/var/log/messages-20170507

----------------------------------------
```
